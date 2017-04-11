import os
from twilio.rest import Client

client = Client(os.environ['TWILIO_ACCT_SID'], os.environ['TWILIO_AUTH_TOKEN'])

message = client.messages.create(to="+17345566915", 
	                             from_="+13132283610", 
	                             body="I'm a demo alert!")

print(message.sid)

# I had to `pip uninstall twilio` 5.7.0 and `pip install twilio` 6.0.0 for `python send_alerts.py` to successfully work
# `python main.py` only works on 5.7.0 currently (but it seems this version might only be supported thru 7/2017)
# Specifcally, need to change twilio.twiml.Response() in main.py to migrate to new version