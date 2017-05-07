from smartsheet import Smartsheet
import os
import geocoder

smartsheet = Smartsheet(os.environ['SMARTSHEET_API_TOKEN'])
subscriber_sheet_id = 1734039796246404
SS = smartsheet.Sheets.get_sheet(subscriber_sheet_id)
COLS = { c.title: (c.index, c.id) for c in SS.columns }
gc = geocoder.Geocoder()

class Contact(object):
    def __init__(self, phone):
        self.number = phone
        self.subscriber = "No"
        self.addresses = []
        # self.last_requested_address = None
        for r in SS.rows:
            if r.cells[COLS['Phone Number'][0]].display_value == phone:
                self.subscriber = "Yes"
                self.addresses.append((r.cells[COLS['Matched Address'][0]].value, r))

    def watch(self, address):
        """Add a new row/reactivate subscription? to the smartsheet"""
        # add new row
        geo = gc.geocode(address)
        location = (round(geo['location']['x'], 5), round(geo['location']['y'], 5))

        new_row = smartsheet.models.Row()
        new_row.to_top = True

        new_row.cells.append({
            'column_id': COLS['Phone Number'][1],
            'value': self.number
        })
        new_row.cells.append({
            'column_id': COLS['Address'][1],
            'value': address
        })
        new_row.cells.append({
            'column_id': COLS['Matched Address'][1],
            'value': str(geo['address'][:-7])
        })
        new_row.cells.append({
            'column_id': COLS['LatLng'][1],
            'value': str(location)
        })
        new_row.cells.append({
            'column_id': COLS['Active'][1],
            'value': "Yes"
        })

        new_row_in_sheet = smartsheet.Sheets.add_rows(SS.id, [new_row])
        self.addresses.append((str(geo['address'][:-7]), new_row_in_sheet.result[0]))

    def unwatch(self, address):
        """Deactivate a subscription from the Smartsheet"""
        for r in self.addresses:
            if address == r[0]:
                cell_active = r[1].get_column(COLS['Active'][1])
                cell_active.value = "No"
                r[1].set_column(COLS['Active'][1], cell_active)
                smartsheet.Sheets.update_rows(SS.id, [r[1]])
