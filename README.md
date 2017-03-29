# demo-alerts

Let's send a text message to people when there's going to be a demolition near their house.

## demolitions

From Salesforce, we get:
- planned knock down date
- address
- parcel id

After geocoding the address, we make a Socrata dataset from this, with an additional location field.

## install

Requires Python 3.6

```bash
git clone https://github.com/CityOfDetroit/demo-alerts.git
cd demo-alerts
pip install -r requirements.txt
```

## development

Copy `sample.env` to `.env` and add your secrets. (We have [autoenv](https://github.com/kennethreitz/autoenv) installed to auto-execute this file.)

1. Run `python main.py` to start the server
2. Download [ngrok](https://ngrok.com/). In another terminal tab, change directories to your unzipped download and run `./ngrok http <your-port-number>` to forward the server to `<some-subdomain>.ngrok.io`
3. Login to Twilio. Go to Console > Phone Numbers > Messaging. Set Messaging to "Configure with Webhooks/TwiML" and "A Message Comes In" to your ngrok webhook

Now, just text your number to trigger the Express app.
