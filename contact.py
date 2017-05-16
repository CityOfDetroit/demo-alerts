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
        conn = sqlite3.connect('db/test.sqlite')
        c = conn.cursor()

        # check if current user is actively subscribed to any addresses
        n = (self.number,)
        for row in c.execute('SELECT matched_address FROM subscribers WHERE phone=? AND active=1', n).fetchall():
            self.addresses.append(row)

        conn.close()

    def watch(self, address):
        """Add a new row to the sqlite subscribers table"""
        # @todo check if this phone address combo exists and update row instead of insert new
        
        geo = gc.geocode(address)
        location = (round(geo['location']['x'], 5), round(geo['location']['y'], 5))

        today = datetime.now()

        # set up new subscriber info
        new_subscriber = [(1, self.number, str(geo['address'][:-7]), str(location), str(today), None)]

        # connect to the db
        conn = sqlite3.connect('db/test.sqlite')
        c = conn.cursor()

        # insert new row into the subscribers table, assumes table has been created/exists
        c.executemany('INSERT INTO subscribers VALUES (?,?,?,?,?,?)', new_subscriber)

        # commit changes and close the connection
        conn.commit()
        conn.close()

        print("{} subscribed to {}".format(self.number, str(geo['address'][:-7])))

    def unwatch(self, address):
        """Deactivate a subscription"""
        conn = sqlite3.connect('db/test.sqlite')
        c = conn.cursor()

        # update any row(s) that match crrent users phone number
        n = (self.number,)
        c.execute('UPDATE subscribers SET active=0 WHERE phone=?', n)

        conn.commit()
        conn.close()

        print("{} unsubscribed from {} address(es)".format(self.number, len(self.addresses)))
