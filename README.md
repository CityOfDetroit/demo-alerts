# demo-alerts

Let's send a text message to people when there's going to be a demolition near their house.

We populate the text messages using info from two datasets on Detroit's Open Data Portal:
- [Upcoming Demolitions](https://data.detroitmi.gov/Government/Upcoming-Detroit-Demolitions/tsqq-qtet): Properties with a contractor and scheduled knock-down date
- [Demolition Pipeline](https://data.detroitmi.gov/Property-Parcels/Demolition_Pipeline/dyp9-69zf): Properties with a completed asbestos abatement survey and projected for demo within the year

## install

Requires Python 3.6

```bash
git clone https://github.com/CityOfDetroit/demo-alerts.git
cd demo-alerts
pip install -r requirements.txt
```

We store our subscriber info in SQLite. Create a `subscribers` table like so:

```
import sqlite3

conn = sqlite3.connect("db/sample.sqlite")
c = conn.cursor()

c.execute("CREATE TABLE subscribers (active integer, phone text, matched_address text, location text, subscribed_date text, last_alert_date text)")

conn.commit()
conn.close()
```

The [SQLite Manager](https://github.com/lazierthanthou/sqlite-manager) extension for Firefox is handy here.

## development

1. Copy `sample.env` to `.env` and add your secrets. We have [autoenv](https://github.com/kennethreitz/autoenv) installed to auto-execute this file
2. Run `python main.py` to start the server
3. Download [ngrok](https://ngrok.com/). In another terminal tab, change directories to your unzipped download and run `./ngrok http <your-port-number>` to forward the server to `<some-subdomain>.ngrok.io`
4. Login to Twilio. Go to Console > Phone Numbers > Messaging. Set Messaging to "Configure with Webhooks/TwiML" and "A Message Comes In" to your ngrok webhook
5. Text your number to trigger the Express app

## send the alerts

Once a day, we want to send our active subsribers a notice if there are demos scheduled nearby them in the next couple of days.

We'll eventually schedule this, but for now just run: `python send_alerts.py`
