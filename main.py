from flask import Flask, request, redirect
from datetime import datetime
from sodapy import Socrata
import twilio.twiml
import os, requests, json, urllib
from geocoder import Geocoder
import contact
import message

soda_client = Socrata("data.detroitmi.gov", os.environ['SODA_TOKEN'], os.environ['SODA_USER'], os.environ['SODA_PASS'])

app = Flask(__name__)

users = {}

@app.route("/", methods=['GET', 'POST'])
def initial():
    """Respond to incoming calls with a simple text message."""

    resp = twilio.twiml.Response()
    
    # get sender phone number, check if they are a current subscriber
    incoming_number = request.values.get('From')[2:]
    if incoming_number in users.keys():
        caller = users[incoming_number]
        print(caller.last_requested_address)
    else:
        caller = contact.Contact(incoming_number)
    print(caller)

    # get body of incoming SMS
    body = request.values.get('Body')

    # check if the body is 'add' or 'end'
    if body.upper() == 'ADD' and caller.last_requested_address:
        caller.watch(caller.last_requested_address)
        resp.message("You've subscribed to demolition alerts near {}. Text 'END' to unsubscribe from your alerts.".format(caller.last_requested_address))

        # remove from users so we grab a 'fresh' copy of the user with sheet rows
        del users[incoming_number]
        return str(resp)
    elif body.upper() == 'END':
        # handle unsub here
        pass
    else:
        # send it to the geocoder
        located = Geocoder().geocode(body)
        print(located)

        # if it's a valid address, check if it has demos nearby
        if located:
            demo_msg = message.Message(located)
            print(demo_msg)

            # todo: figure out how to deal with this based on message returned (1+ or 0 demos nearby soon)
            if demo_msg:
                caller.last_requested_address = located['address'][:-7]
                users[incoming_number] = caller
            else:
                caller.last_requested_address = located['address'][:-7]
                users[incoming_number] = caller

        # default message for a bad address
        else:
            resp.message("To receive notices about demolitions happening nearby, please text us a street address (eg '123 Woodward').")

    return str(resp)

if __name__ == "__main__":
    app.run(debug=True)
