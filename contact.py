import os
import sqlite3
import geocoder
from datetime import datetime

gc = geocoder.Geocoder()

class Contact(object):
    def __init__(self, phone):
        self.number = phone
        self.subscriber = False
        self.addresses = []

        # connect to the db
        conn = sqlite3.connect('db/prod.sqlite')
        c = conn.cursor()

        # check if current user is actively subscribed to any addresses
        n = (self.number,)
        for row in c.execute('SELECT matched_address FROM subscribers WHERE phone=? AND active=1', n).fetchall():
            self.addresses.append(row)

        conn.close()

    def watch(self, address):
        """Add a new subscription or activate an existing one"""     
        geo = gc.geocode(address)
        location = (round(geo['location']['x'], 5), round(geo['location']['y'], 5))

        today = datetime.now()

        # connect to the db
        conn = sqlite3.connect('db/prod.sqlite')
        c = conn.cursor()

        # check if this phone/address combo exists
        subscriptions = []
        for row in c.execute('SELECT * FROM subscribers WHERE phone=? and matched_address=?', (self.number, str(geo['address'][:-7]))).fetchall():
            subscriptions.append(row)

        # add a new row or update existing row
        if len(subscriptions) < 1:
            new_subscriber = (1, self.number, str(geo['address'][:-7]), str(location), str(today), None)
            c.execute('INSERT INTO subscribers VALUES (?,?,?,?,?,?)', new_subscriber)
            conn.commit()
        
        else:
            c.execute('UPDATE subscribers SET active=1 WHERE phone=? AND matched_address=?', (self.number, str(geo['address'][:-7])))
            conn.commit()

        # close the connection
        conn.close()

    def unwatch(self, address):
        """Deactivate a subscription"""
        conn = sqlite3.connect('db/prod.sqlite')
        c = conn.cursor()

        # update any row(s) that match current users phone number
        n = (self.number,)
        c.execute('UPDATE subscribers SET active=0 WHERE phone=?', n)

        conn.commit()
        conn.close()
