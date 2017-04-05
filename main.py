from flask import Flask, request, redirect
from datetime import datetime
from sodapy import Socrata
import twilio.twiml
import os, requests, json, urllib
from geocoder import Geocoder
import contact

soda_client = Socrata("data.detroitmi.gov", os.environ['SODA_TOKEN'], os.environ['SODA_USER'], os.environ['SODA_PASS'])

app = Flask(__name__)

@app.route("/", methods=['GET', 'POST'])
def initial():
    """Respond to incoming calls with a simple text message."""
    resp = twilio.twiml.Response()

    print(request.values.get('From')[2:])
    contact = contact.Contact(request.values.get('From')[2:])
    print(contact)
    # get body of incoming SMS
    body = request.values.get('Body')
    print(body)

    # send it to the geocoder, returns a dict
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
                formatted_demo = "{} on {}".format(d['address'], datetime.fromtimestamp(int(d['demo_date'])).strftime('%m-%d-%Y'))
                list_demos.append(formatted_demo)

            resp.message("{} demos sheduled near {} in the next 5 days: \n{}. \nDates subject to change.".format(len(demos), located['address'], list_demos))
        else:
            resp.message("No demos scheduled near {} in the next 5 days. Text 'ADD' to subscribe to future demo alerts near this address.".format(located['address']))

    # default message for a bad address
    else:
        resp.message("To receive notices about demolitions happening nearby, please text us a street address (eg '123 Woodward').")

    return str(resp)

if __name__ == "__main__":
    app.run(debug=True)
