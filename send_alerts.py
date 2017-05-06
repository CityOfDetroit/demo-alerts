import os
from twilio.rest import Client
from sodapy import Socrata
from smartsheet import Smartsheet
from datetime import datetime, timedelta

smartsheet = Smartsheet(os.environ['SMARTSHEET_API_TOKEN'])
subscriber_sheet_id = 6624424314070916
SS = smartsheet.Sheets.get_sheet(subscriber_sheet_id)
COLS = { c.title: (c.index, c.id) for c in SS.columns }

soda_client = Socrata("data.detroitmi.gov", os.environ['SODA_TOKEN'], os.environ['SODA_USER'], os.environ['SODA_PASS'])

client = Client(os.environ['TWILIO_ACCT_SID'], os.environ['TWILIO_AUTH_TOKEN'])

# declare a simple counter variable
alerts_sent = 0

# make a list of active subscribers, where each element is a dict with subscriber address, lat, lng, phone and list of demos nearby
active_subscribers = []
for r in SS.rows:
    # todo: figure out how to fix this, should set as col Active to True/checked
    if r.cells[COLS['Phone Number'][0]].value == '7345566915':
        subscriber = {
            "address": r.cells[COLS['Matched Address'][0]].display_value,
            "lng": r.cells[COLS['LatLng'][0]].display_value.strip("()")[:-10],
            "lat": r.cells[COLS['LatLng'][0]].display_value.strip("()")[11:],
            "phone": r.cells[COLS['Phone Number'][0]].display_value,
            "demos_nearby": []
        }
        active_subscribers.append(subscriber)

# calculate three days from now
today = datetime.now()
three_days = today + timedelta(days=3)
three_days_str = three_days.strftime('%Y-%m-%d')

# find demos nearby active subscribers addresses scheduled for knock-down in the next three days
for i in active_subscribers:
    # query socrata, populate subscriber[demos_nearby]
    demos = soda_client.get("tsqq-qtet", where="demolish_by_date<='{}' AND within_circle(location, {}, {}, 155)".format(three_days_str, i['lat'], i['lng']))
    i['demos_nearby'].extend(demos)

    # if an active subscriber is near demos, send them an alert
    if len(i['demos_nearby']) > 0:
        # format list of demos nearby
        list_demos = []
        for d in i['demos_nearby']:
            formatted_demo = "{} on {}".format(d['address'], datetime.strptime((d['demolish_by_date']), '%Y-%m-%dT%H:%M:%S').strftime('%m-%d-%Y'))
            list_demos.append(formatted_demo)

        # setup the message 
        send_to = "+1" + i['phone']
        send_body = "Notice: Demolitions are scheduled nearby {}: \n{}. \nDates subject to change. Text 'REMOVE' to unsubscribe.".format(i['address'], (";\n").join(list_demos))

        # send the alert, increment our count
        message = client.messages.create(to=send_to,from_="+13132283610",body=send_body)
        alerts_sent += 1
       
        # todo: write this back to smartsheet record as confirmation alert was sent?
        # message sids are unique ids we can later map to our message logs
        print(message.sid)
    
    # don't send anything if no demos nearby
    else:
        pass

# log some basic stats, later we can send these to slack
print("# active subscribers:",len(active_subscribers))
print("# alerts sent today:", alerts_sent)
