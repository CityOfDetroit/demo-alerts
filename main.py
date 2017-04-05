from flask import Flask, request, redirect
from datetime import datetime
from sodapy import Socrata
import twilio.twiml
import os, requests, json, urllib
from geocoder import Geocoder
import contact

soda_client = Socrata("data.detroitmi.gov", os.environ['SODA_TOKEN'], os.environ['SODA_USER'], os.environ['SODA_PASS'])

app = Flask(__name__)

users = {}

@app.route("/", methods=['GET', 'POST'])
def initial():
    """Respond to incoming calls with a simple text message."""

    resp = twilio.twiml.Response()
    incoming_number = request.values.get('From')[2:]
    if incoming_number in users.keys():
        caller = users[incoming_number]
        print(caller.last_requested_address)
    else:
        caller = contact.Contact(incoming_number)
    print(caller)
    # get body of incoming SMS
    body = request.values.get('Body')
<<<<<<< HEAD
    if body.upper() == 'ADD' and caller.last_requested_address:
        caller.watch(caller.last_requested_address)
        resp.message("You've subscribed to demolition alerts near {}. Text 'END' to unsubscribe from your alerts.".format(caller.last_requested_address))
        # remove from users so we grab a 'fresh' copy of the user with sheet rows
        del users[incoming_number]
        return str(resp)
    if body.upper() == 'END':
        # handle unsub here
        pass
    else:
        # send it to the geocoder
        located = Geocoder().geocode(body)
        print(located)

        # if it's a valid address, check if it has demos nearby
        if located:
            lat = located['location']['y']
            lng = located['location']['x']
            print(lat, lng)

            # query against socrata dataset, returns an array
            # eventually, add time query here too??
            demos = soda_client.get("8wnn-qcxj", where="within_circle(location, {}, {}, 155)".format(lat, lng))
            print(demos)

            # if there's demos nearby, make a list of addresses and dates to add to the message
            if len(demos) > 0:
                list_demos = []
                for d in demos:
                    formatted_demo = "{} on {}".format(d['address'][:-7], datetime.fromtimestamp(int(d['demo_date'])).strftime('%m-%d-%Y'))
                    list_demos.append(formatted_demo)

                resp.message("{} demos scheduled near {} in the next 5 days: \n{}. \nDates subject to change. Text 'ADD' to subscribe to future demo alerts near this address.".format(len(demos), located['address'], list_demos))
                caller.last_requested_address = located['address'][:-7]
                users[incoming_number] = caller
            else:
                resp.message("No demos scheduled near {} in the next 5 days. Text 'ADD' to subscribe to future demo alerts near this address.".format(located['address']))
                caller.last_requested_address = located['address'][:-7]
                users[incoming_number] = caller

        # default message for a bad address
        else:
            resp.message("To receive notices about demolitions happening nearby, please text us a street address (eg '123 Woodward').")

    return str(resp)

if __name__ == "__main__":
    app.run(debug=True)
