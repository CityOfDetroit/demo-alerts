from flask import Flask, request, redirect
from datetime import datetime
import twilio.twiml
import os, requests, json, urllib
import geocode

app = Flask(__name__)

@app.route("/", methods=['GET', 'POST'])
def initial():
    """Respond to incoming calls with a simple text message."""
    resp = twilio.twiml.Response()
    
    # get body of incoming SMS
    body = request.values.get('Body')
    print(body)

    # send it to the geocoder
    located = geocode.best_parcel_match(body)
    print(located)

    # default messages for valid or invalid addresses
    if located:
    	resp.message("List of properties nearby {} scheduled to be demolished in the next few days. Subscribe to get future alerts for this address.".format(located['address']))
    else:
    	resp.message("To receive notices about demolitions happening nearby, please text us a street address (eg '123 Woodward').")

    return str(resp)

if __name__ == "__main__":
    app.run(debug=True)
