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
        
    else:
        caller = contact.Contact(incoming_number)

    # get body of incoming SMS
    body = request.values.get('Body')

    # check if the body is 'HEALTH', 'ADD', 'REMOVE' or anything else 
    if body.upper().strip() == 'HEALTH':
        health_msg = message.HealthMsg().make_msg()
        resp.message(health_msg)

        print("{} texted HEALTH".format(incoming_number))

    elif body.upper().strip() == 'ADD' and caller.last_requested_address:
        caller.watch(caller.last_requested_address)
        
        msg = message.SubscribeMsg(caller.last_requested_address)
        success_msg = msg.make_msg()
        resp.message(success_msg)

        # remove from users so we grab a 'fresh' copy of the user with sheet rows
        del users[incoming_number]

        print("{} subscribed to {}".format(incoming_number, caller.last_requested_address))
   
    elif body.upper().strip() == 'REMOVE':
        for address in caller.addresses:
            caller.unwatch(address)
        
        msg = message.UnsubscribeMsg([a[0] for a in caller.addresses])
        remove_msg = msg.make_msg()
        resp.message(remove_msg)

        print("{} unsubscribed from {} addresses".format(incoming_number, len(caller.addresses)))

    else:
        # send it to the geocoder
        located = Geocoder().geocode(body)

        # if it's a valid address, build up a text message with demos nearby
        if located:
            print("Geocoded {} from {}".format(located['address'], incoming_number))
            
            msg = message.DemoMsg(located)
            demo_msg = msg.make_msg()
            resp.message(demo_msg)

            # store matched address
            caller.last_requested_address = located['address'][:-7]
            users[incoming_number] = caller

        # default message for a bad address
        else:
            default_msg = message.DefaultMsg().make_msg()
            resp.message(default_msg)

            print("Couldn't geocode '{}' from {}; Sent it to Slack".format(body, incoming_number))

            # send it to Slack
            webhook_url = os.environ['SLACK_WEBHOOK_URL']

            err_msg = ":exclamation: demo-alerts can't geocode `{}` from `{}`".format(body, incoming_number)
            slack_data = {'text': err_msg}

            response = requests.post(
                webhook_url, data=json.dumps(slack_data),
                headers={'Content-Type': 'application/json'}
            )

            if response.status_code != 200:
                raise ValueError(
                    'Request to slack returned an error %s, the response is:\n%s'
                    % (response.status_code, response.text)
                )

    # send the text 
    return str(resp)

if __name__ == "__main__":
    app.run(debug=True)
