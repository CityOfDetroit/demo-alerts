from flask import Flask, request, redirect
from datetime import datetime
from sodapy import Socrata
import twilio.twiml
import os, requests, json, urllib
import geocode

soda_client = Socrata("data.detroitmi.gov", os.environ['SODA_TOKEN'], os.environ['SODA_USER'], os.environ['SODA_PASS'])

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

    # if it's a valid address, check if it has demos nearby 
    if located:
        lat = located['coords'][0]
        lng = located['coords'][1]
        demos = soda_client.get("q48r-nkgw", where="within_circle(location, {}, {}, 155)".format(lat, lng))
        print(demos)

        if len(demos) > 0:
            resp.message("Demos scheduled near {}: {}.".format(located['address'], demos))
        else:
            resp.message("No demos scheduled near {} in the next 5 days. Text 'Y' to subscribe to future demo alerts near this address.".format(located['address']))
    # default message for a bad address
    else:
        resp.message("To receive notices about demolitions happening nearby, please text us a street address (eg '123 Woodward').")

    return str(resp)

if __name__ == "__main__":
    app.run(debug=True)
