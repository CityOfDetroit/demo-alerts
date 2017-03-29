from flask import Flask, request, redirect
from datetime import datetime
import twilio.twiml
import os, requests, json, urllib

app = Flask(__name__)

@app.route("/", methods=['GET', 'POST'])
def initial():
    """Respond to incoming calls with a simple text message."""
    resp = twilio.twiml.Response()
    
    # get body of incoming SMS
    body = request.values.get('Body')
    print(body)

    # set a default message
    resp.message("Thanks for texting!")

    return str(resp)

if __name__ == "__main__":
    app.run(debug=True)
