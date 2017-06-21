# demo-alerts

Let's send a text message to people when there's going to be a demolition near their house.

Try it out by texting a street address in Detroit to 313-254-DEMO (aka 313-254-3366).

We locate the address you send us against our ESRI Composite Geocode and then populate the text response by querying two datasets on our Open Data Portal:
- [Upcoming Demolitions](https://data.detroitmi.gov/Government/Upcoming-Detroit-Demolitions/tsqq-qtet): Properties with a contractor and scheduled knock-down date
- [Demolition Pipeline](https://data.detroitmi.gov/Property-Parcels/Demolition_Pipeline/dyp9-69zf): Properties with a completed asbestos abatement survey and projected for demo within the year

If you call this number, we'll play back an instructional voice recording.

## Install

Requires Python 3.6

```bash
git clone https://github.com/CityOfDetroit/demo-alerts.git
cd demo-alerts
pip install -r requirements.txt
```

We store our subscribers in a SQLite database. Create a `subscribers` table like so:

```
import sqlite3

conn = sqlite3.connect("db/sample.sqlite")
c = conn.cursor()

c.execute("CREATE TABLE subscribers (active integer, phone text, matched_address text, location text, subscribed_date text, last_alert_date text)")

conn.commit()
conn.close()
```

The [SQLite Manager](https://github.com/lazierthanthou/sqlite-manager) extension for Firefox is handy here.

## Development

1. Copy `sample.env` to `.env` and add your secrets. We have [autoenv](https://github.com/kennethreitz/autoenv) installed to auto-execute this file
2. Run `python main.py` to start the server
3. Download [ngrok](https://ngrok.com/). In another terminal tab, change directories to your unzipped download and run `./ngrok http <your-port-number>` to forward the server to `<some-subdomain>.ngrok.io`
4. Login to Twilio. Go to Console > Phone Numbers. 
5. Set Messaging to "Configure with Webhooks, or TwiML Bins or Functions" and "A Message Comes In" to your ngrok webhook
6. Set Voice & Fax to "Configure with Webhooks, or TwiML Bins or Functions" and "A Call Comes In" to a TwiML Bin (twilio.com/console/dev-tools/twiml-bins) that looks something like this:
```
<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Play>https://some-file.mp3</Play>
</Response>
```
7. Text or call your number to trigger the Express app!

## Send the alerts

Once a day, we want to send our active subsribers a notice if there are demos scheduled nearby them in the next three days.

In development, you can just run: `python send_alerts.py`

For production, we shedule this to run as a cron job on a remote Linux server:
1. Edit `daily-alets-twilio.sh` and replace `/path/to/` with your full directories
2. Edit `send_alerts.py` with the full path to your database, around line 16
3. Add a new cron task: `crontab -e`
4. Configure the job to run at 11am every day and log errors to a local file:
```
0 11 * * * /bin/bash /path/to/demo-alerts/daily-alerts-twilio.sh >> /path/to/cron-output.log 2>&1
```
5. List all cron jobs to confirm it's scheduled: `crontab -l`