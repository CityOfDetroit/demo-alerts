import os
import sqlite3
import geocoder
from smartsheet import Smartsheet
from datetime import datetime

smartsheet = Smartsheet(os.environ['SMARTSHEET_API_TOKEN'])
subscriber_sheet_id = 6624424314070916
SS = smartsheet.Sheets.get_sheet(subscriber_sheet_id)
COLS = { c.title: (c.index, c.id) for c in SS.columns }

gc = geocoder.Geocoder()

class Contact(object):
    def __init__(self, phone):
        self.number = phone
        self.subscriber = False
        self.addresses = []
        self.last_requested_address = None
        for r in SS.rows:
            if r.cells[COLS['Phone Number'][0]].display_value == phone:
                self.subscriber = True
                self.addresses.append((r.cells[COLS['Matched Address'][0]].value, r))

    def watch(self, address):
        """Add a new row to the sqlite subscribers table"""
        geo = gc.geocode(address)
        location = (round(geo['location']['x'], 5), round(geo['location']['y'], 5))

        today = datetime.now()

        # set up new subscriber info
        new_subscriber = [(1, self.number, str(geo['address'][:-7]), str(location), str(today), None)]
        print("New subscriber:", new_subscriber)

        # connect to the db
        conn = sqlite3.connect('db/test.sqlite')
        print(conn)

        c = conn.cursor()

        # insert new row into the subscribers table, assumes table has been created/exists
        c.executemany('INSERT INTO subscribers VALUES (?,?,?,?,?,?)', new_subscriber)

        # commit changes and close the connection
        conn.commit()
        conn.close()

    def unwatch(self, address):
        """Deactivate a subscription from the Smartsheet"""
        for r in self.addresses:
            if address == r[0]:
                cell_active = r[1].get_column(COLS['Active'][1])
                cell_active.value = False
                r[1].set_column(COLS['Active'][1], cell_active)
                smartsheet.Sheets.update_rows(SS.id, [r[1]])
