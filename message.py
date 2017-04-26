import os
from datetime import datetime, timedelta
from sodapy import Socrata

soda_client = Socrata("data.detroitmi.gov", os.environ['SODA_TOKEN'], os.environ['SODA_USER'], os.environ['SODA_PASS'])

class DemoMsg(object):
    def __init__(self, locatedAddress):
        self.addr = locatedAddress

    def make_msg(self, addr):
        """Find upcoming demolitions near an already geocoded address and list them in a text message"""
        lat = addr['location']['y']
        lng = addr['location']['x']

        # get this week
        today = datetime.now()
        end_of_week = today + timedelta(days=7)
        end_of_week_str = end_of_week.strftime('%Y-%m-%d')

        # query for scheduled demos within 500ft (155m) this week
        # https://data.detroitmi.gov/Government/Upcoming-Detroit-Demolitions/tsqq-qtet/data
        demos = soda_client.get("tsqq-qtet", where="demolish_by_date<='{}' AND within_circle(location, {}, {}, 155)".format(end_of_week_str, lat, lng))
        print("Demos this wk:", len(demos))

        # format demos
        if len(demos) > 0:
            list_demos = []
            for d in demos:
                formatted_demo = "{} on {}".format(d['address'], datetime.strptime((d['demolish_by_date']), '%Y-%m-%dT%H:%M:%S').strftime('%m-%d-%Y'))
                list_demos.append(formatted_demo)

        # query for properties within 500ft in the demo pipeline
        # https://data.detroitmi.gov/Property-Parcels/Demolition_Pipeline/dyp9-69zf/data
        pipeline = soda_client.get("dyp9-69zf", where="within_circle(location, {}, {}, 155)".format(lat, lng))
        print("Pipeline properties:", len(pipeline))

        # format pipeline properties
        if len(pipeline) > 0:
            list_pipeline = []
            for p in pipeline:
                formatted_pipeline = "{}".format(p['address'])
                list_pipeline.append(formatted_pipeline)

        # build the text msgs
        if len(demos) > 0 & len(pipeline) < 1:
            return "{} demos scheduled near {} this week: \n{}. \nDates subject to change. Text 'ADD' to subscribe to future demo alerts near this address.".format(len(demos), addr['address'][:-7], (";\n").join(list_demos))

        elif len(demos) < 1 & len(pipeline) > 0:
            return "No demos scheduled near {} this week. Nearby properties are in the pipeline and projected for demo within a year: \n{}. \nText 'ADD' to subscribe to future demo alerts near this address.".format(addr['address'][:-7], (";\n").join(list_pipeline))

        elif len(demos) > 0 & len(pipeline) > 0:
            return "{} demos scheduled near {} this week: \n{}. \nAdditional nearby properties are in pipeline and projected for demo within a year: \n{}. \nDates subject to change. Text 'ADD' to subscribe to future demo alerts near this address."
        
        else: 
            return "No properties near {} are currently scheduled to be demolished or in the pipeline. Text 'ADD' to subscribe to future demo alerts near this address.".format(addr['address'][:-7])

class SubscribeMsg(object):
    def __init__(self, lastRequestedAddress):
        self.addr = lastRequestedAddress

    def make_msg(self, addr):
        """Confirm subscription to the address you last texted"""
        return "You've subscribed to demolition alerts near {}. Text 'REMOVE' to unsubscribe from your alerts.".format(addr)

class UnsubscribeMsg(object):
    def __init__(self, activeAddresses):
        self.addrs = activeAddresses

    def make_msg(self, addrs):
        """Unsubscribe from all active addresses"""
        return "You're unsubscribed to demolition alerts near: \n{}. \nText a street address to find demos nearby or to resubscribe.".format((";\n").join(addrs))
 
class DefaultMsg(object):
    def __init__(self):
        pass

    def make_msg(self):
        """Default message for anything you send us besides ADD, END or a valid address"""
        return "To receive notices about demolitions happening nearby, please text a street address (eg '2 Woodward')."
