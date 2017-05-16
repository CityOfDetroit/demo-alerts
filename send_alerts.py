import os
import json
import requests
import sqlite3
from twilio.rest import Client
from sodapy import Socrata
from datetime import datetime, timedelta

client = Client(os.environ['TWILIO_ACCT_SID'], os.environ['TWILIO_AUTH_TOKEN'])
soda_client = Socrata("data.detroitmi.gov", os.environ['SODA_TOKEN'], os.environ['SODA_USER'], os.environ['SODA_PASS'])

# declare a simple counter variable
alerts_sent = 0

# connect to the db
conn = sqlite3.connect('db/test.sqlite')
c = conn.cursor()

# make a list of active subscribers
active_subscribers = []
for row in c.execute('SELECT * FROM subscribers WHERE active=1').fetchall():
    subscriber = {
        "phone": row[1],
        "address": row[2],
        "lng": row[3].strip("()")[:-10],
        "lat": row[3].strip("()")[11:],
        "demos_nearby": []
    }
    active_subscribers.append(subscriber)

# calculate three days from now
today = datetime.now()
three_days = today + timedelta(days=3)
three_days_str = three_days.strftime('%Y-%m-%d')

# find demos nearby active subscribers addresses scheduled for demo in the next three days
for i in active_subscribers:
    # query socrata, populate subscriber[demos_nearby] with result
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
        send_body = "NOTICE: Demolitions scheduled near {}: \n{}. \nDates may change. To help protect your family during demos: \n- Keep children and pets inside \n- Close windows and doors. \nText 'HEALTH' to learn more. Text 'REMOVE' to unsubscribe.".format(i['address'], (";\n").join(list_demos))

        # send the alert, increment our count
        message = client.messages.create(to=send_to,from_="+13132283610",body=send_body)
        alerts_sent += 1

        # write todays date back to our db
        c.execute('UPDATE subscribers SET last_alert_date=? WHERE phone=? and matched_address=?', (today, i['phone'], i['address']))
        conn.commit()
    
    # don't send anything if no demos nearby
    else:
        pass

# close the db connection
conn.close()

print("Sent {} alerts".format(alerts_sent))

# log some daily metrics to Slack
daily_msg = "Delivered demolition alerts :pager: \nNumber of active subscribers: *{}* \nNumber of alerts sent today: *{}*".format(len(active_subscribers), alerts_sent)

webhook_url = os.environ['SLACK_WEBHOOK_URL']
slack_data = {'text': daily_msg}

response = requests.post(
    webhook_url, data=json.dumps(slack_data),
    headers={'Content-Type': 'application/json'}
)

if response.status_code != 200:
    raise ValueError(
        'Request to slack returned an error %s, the response is:\n%s'
        % (response.status_code, response.text)
    )