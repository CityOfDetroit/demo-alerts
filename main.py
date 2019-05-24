import os, requests, json, urllib
from flask import Flask, request, redirect
from twilio.twiml.messaging_response import MessagingResponse
from twilio.twiml.voice_response import VoiceResponse
from geocoder import Geocoder
from datetime import datetime
from sodapy import Socrata
import contact
import message
import re

soda_client = Socrata("data.detroitmi.gov", os.environ['SODA_TOKEN'], os.environ['SODA_USER'], os.environ['SODA_PASS'])

app = Flask(__name__)

users = {}

# accept common misspellings of keywords
keywords = {
    'Add': ["ADD", "'ADD'", "AD", "ADDD", "A", "ASD", "SDD"],
    'Remove': ["REMOVE", "'REMOVE'", "REMOV", "REMOVEE", "R", "ERMOVE", "REMOEV"],
    'Health': ["HEALTH", "'HEALTH'", "HEALT", "HEALTHH", "H", "HRALTH", "HEALHT", "EHALTH", "HAELTH", "NEALTH"],
    'Edu': ["EDU", "'EDU'", "ED", "EDUU", "EDUC", "E" "DEU", "EEU"]
}

@app.route("/", methods=['GET', 'POST'])
def text():
    """Respond to incoming texts with a message."""
    resp = MessagingResponse()
    
    # get sender phone number, check if they are a current subscriber
    incoming_number = request.values.get('From')[2:]
    if incoming_number in users.keys():
        caller = users[incoming_number]
    else:
        caller = contact.Contact(incoming_number)

    # get body of incoming SMS and format it
    body = request.values.get('Body')
    b = body.upper().strip()

    # check if the body is 'HEALTH', 'EDU', 'ADD', 'REMOVE' or anything else 
    if b in keywords['Health']:
        health_msg = message.HealthMsg().make_msg()
        resp.message(health_msg)

        print("{} texted HEALTH".format(incoming_number))

    elif b in keywords['Edu']:
        call_msg = message.CallMsg().make_msg()
        resp.message(call_msg)

        print("{} requested a call from a Health Educator".format(incoming_number))

        # get users last requested address or the address they're subscribed to
        if incoming_number in users.keys():
            edu_addr = caller.last_requested_address
        else:
            edu_addr = [a[0] for a in caller.addresses][0]

        # calculate demos nearby to generate short report for Health Dept
        located = Geocoder().geocode(edu_addr)

        # query Socrata datasets
        scheduled_demos = soda_client.get("tsqq-qtet", where="within_circle(location, {}, {}, 155)".format(located['location']['y'], located['location']['x']))
        pipeline_demos = soda_client.get("dyp9-69zf", where="within_circle(location, {}, {}, 155)".format(located['location']['y'], located['location']['x']))
        past_demos = soda_client.get("rv44-e9di", where="within_circle(location, {}, {}, 155)".format(located['location']['y'], located['location']['x']))
        upcoming_demos = scheduled_demos + pipeline_demos

        # format 'em
        demo_dates = []
        if len(scheduled_demos) > 0:
            for d in scheduled_demos:
                demo_date = "{}".format(datetime.strptime((d['demolish_by_date']), '%Y-%m-%dT%H:%M:%S').strftime('%m-%d-%Y'))
                demo_dates.append(demo_date)
        else:
            demo_date = None
            demo_dates.append(demo_date)

        # send request to Slack
        webhook_url = os.environ['SLACK_WEBHOOK_URL']
        caller_msg = ":phone: `{}` requested a call from a Health Educator \nLast address texted: *{}* \nNumber of upcoming demos: *{}* \nNumber of past demos: *{}* \nNext knock-down date: *{}*".format(incoming_number, edu_addr, len(upcoming_demos), len(past_demos), demo_dates[0])
        slack_data = {'text': caller_msg}

        response = requests.post(
            webhook_url, data=json.dumps(slack_data),
            headers={'Content-Type': 'application/json'}
        )

        if response.status_code != 200:
            raise ValueError(
                'Request to slack returned an error %s, the response is:\n%s'
                % (response.status_code, response.text)
            )

    elif b in keywords['Add'] and caller.last_requested_address:
        caller.watch(caller.last_requested_address)
        
        msg = message.SubscribeMsg(caller.last_requested_address)
        success_msg = msg.make_msg()
        resp.message(success_msg)

        # remove from users so we grab a 'fresh' copy of the user with sheet rows
        del users[incoming_number]

        print("{} subscribed to {}".format(incoming_number, caller.last_requested_address))
   
    elif b in keywords['Remove']:
        for address in caller.addresses:
            caller.unwatch(address)
        
        msg = message.UnsubscribeMsg([a[0] for a in caller.addresses])
        remove_msg = msg.make_msg()
        resp.message(remove_msg)

        print("{} unsubscribed from {} addresses".format(incoming_number, len(caller.addresses)))

    else:
        pattern = re.compile('(\d{2,5})\s?(\w{2,})')
        result = pattern.search(body)
        if result:
            send = result.group(1) + ' ' + result.group(2)
        else:
            send = body

        # send it to the geocoder
        located = Geocoder().geocode(send)

        # if it's a valid address, build up a text message with demos nearby
        if located:
            print("Geocoded {} (original: {}) from {}".format(located['address'], send, incoming_number))
            
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

            print("Couldn't geocode '{}' from {}; Sent it to Slack".format(send, incoming_number))

            # send it to Slack
            webhook_url = os.environ['SLACK_WEBHOOK_URL']
            err_msg = ":exclamation: demo-alerts can't geocode `{}` from `{}`".format(send, incoming_number)
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

@app.route("/voice", methods=['GET', 'POST'])
def voice():
    """Respond to incoming calls with a recording"""
    resp = VoiceResponse()
    resp.play("https://detroit-iet.neocities.org/demo-alerts-intro.mp3")

    return str(resp)

if __name__ == "__main__":
    app.run(debug=True)
