from flask import Flask, request, redirect
from twilio.twiml.messaging_response import MessagingResponse
import os, requests, json, urllib
from geocoder import Geocoder
import contact
import message

app = Flask(__name__)

users = {}

@app.route("/", methods=['GET', 'POST'])
def initial():
    """Respond to incoming calls with a simple text message."""

    # define the twilio response, ref https://twilio.github.io/twilio-python/6.0.0/twiml/messaging_response.m.html
    resp = MessagingResponse()
    
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

    # check if the body is 'add' or 'remove' or anything else 
    if body.upper() == 'ADD' and caller.last_requested_address:
        caller.watch(caller.last_requested_address)
        
        msg = message.SubscribeMsg(caller.last_requested_address)
        success_msg = msg.make_msg(msg.addr)
        resp.message(success_msg)

        # remove from users so we grab a 'fresh' copy of the user with sheet rows
        del users[incoming_number]
        return str(resp)
   
    elif body.upper() == 'REMOVE':
        for address in caller.addresses:
            caller.unwatch(address)
        
        msg = message.UnsubscribeMsg([a[0] for a in caller.addresses])
        remove_msg = msg.make_msg(msg.addrs)
        resp.message(remove_msg)

    else:
        # send it to the geocoder
        located = Geocoder().geocode(body)

        # if it's a valid address, build up a text message with demos nearby
        if located:
            print("Geocode match:", located['address'])
            msg = message.DemoMsg(located)
            demo_msg = msg.make_msg(msg.addr)
            resp.message(demo_msg)

            caller.last_requested_address = located['address'][:-7]
            users[incoming_number] = caller

        # default message for a bad address
        else:
            default_msg = message.DefaultMsg().make_msg()
            resp.message(default_msg)

    # send the text 
    return str(resp)

if __name__ == "__main__":
    app.run(debug=True)
