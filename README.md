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

smartsheet cell.py:

Setting `checkbox` values will fail unless you change cell.py like so:

https://github.com/smartsheet-platform/smartsheet-python-sdk/issues/38

```
@value.setter
def value(self, value):
    if isinstance(value, (six.string_types, six.integer_types, float, bool)):
        self._value = value
```

## development

Copy `sample.env` to `.env` and add your secrets. (We have [autoenv](https://github.com/kennethreitz/autoenv) installed to auto-execute this file.)

Run `python main.py` to start the server.

Download [ngrok](https://ngrok.com/). In another terminal tab, change directories to your unzipped download and run `./ngrok http <your-port-number>` to forward the server to `<some-subdomain>.ngrok.io`.

Login to Twilio. Go to Console > Phone Numbers > Messaging. Set Messaging to "Configure with Webhooks/TwiML" and "A Message Comes In" to your ngrok webhook.

Now, just text your number to trigger the Express app.
