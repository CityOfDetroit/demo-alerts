import os
from twilio.rest import Client

client = Client(os.environ['TWILIO_ACCT_SID'], os.environ['TWILIO_AUTH_TOKEN'])

message = client.messages.create(to="+17345566915", 
	                             from_="+13132283610", 
	                             body="I'm a demo alert!")

print(message.sid)
