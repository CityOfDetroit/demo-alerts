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
        end_of_week = today + timedelta(days=8)
        end_of_week_str = end_of_week.strftime('%Y-%m-%d')

        # query Socrata datasets
        demos_soon = soda_client.get("tsqq-qtet", where="demolish_by_date<='{}' AND within_circle(location, {}, {}, 155)".format(end_of_week_str, lat, lng))
        demos_nearby = soda_client.get("tsqq-qtet", where="demolish_by_date>='{}' AND within_circle(location, {}, {}, 155)".format(end_of_week_str, lat, lng))
        pipeline = soda_client.get("dyp9-69zf", where="within_circle(location, {}, {}, 155)".format(lat, lng))
        print("Demos this wk:", len(demos_soon))

        # format query results as formatted lists for text msgs
        list_demos_soon = []
        if len(demos_soon) > 0:
            for d in demos_soon:
                formatted_demo_soon = "{} on {}".format(d['address'], datetime.strptime((d['demolish_by_date']), '%Y-%m-%dT%H:%M:%S').strftime('%m-%d-%Y'))
                list_demos_soon.append(formatted_demo_soon)

        list_demos_nearby = []
        if len(demos_nearby) > 0:
            for d in demos_nearby:
                formatted_demo_nearby = "{} on {}".format(d['address'], datetime.strptime((d['demolish_by_date']), '%Y-%m-%dT%H:%M:%S').strftime('%m-%d-%Y'))
                list_demos_nearby.append(formatted_demo_nearby)

        list_pipeline = []
        if len(pipeline) > 0:
            for p in pipeline:
                formatted_pipeline = "{}".format(p['address'])
                list_pipeline.append(formatted_pipeline)

        # concat demos nearby beyond one week and pipeline
        full_pipeline = list_demos_nearby + list_pipeline
        print("Pipeline properties:", len(full_pipeline))

        # build the text msgs
        if len(demos_soon) > 0 and len(full_pipeline) < 1:
            return "Demolitions are scheduled near {} this week: \n{}. \nDates subject to change. Protect your family against health risks during demolition by keeping windows and doors closed and children and pets inside. Text 'ADD' to get alerts 3 days prior to demos near this address.".format(addr['address'][:-7], (";\n").join(list_demos_soon))

        elif len(full_pipeline) > 0 and len(demos_soon) < 1:
            return "Properties nearby {} are in the demolition pipeline and projected for knock-down within a year: \n{}. \nDates subject to change. Protect your family against health risks during demolition by keeping windows and doors closed and children and pets inside. Text 'ADD' to get alerts 3 days prior to demos near this address.".format(addr['address'][:-7], (";\n").join(full_pipeline))

        elif len(demos_soon) > 0 and len(full_pipeline) > 0:
            return "Demolitions are scheduled near {} this week: \n{}. \nAdditional properties nearby are in the pipeline and projected for knock-down within a year: \n{}. \nDates subject to change. Protect your family against health risks during demolition by keeping windows and doors closed and children and pets inside. Text 'ADD' to get alerts 3 days prior to demos near this address.".format(addr['address'][:-7], (";\n").join(list_demos_soon), (";\n").join(full_pipeline))

        else: 
            return "No properties near {} are currently in the demolition pipeline or scheduled to be knocked-down. Protect your family against health risks during demolition by keeping windows and doors closed and children and pets inside. Text 'ADD' to get alerts one week prior to demos near this address.".format(addr['address'][:-7])

class SubscribeMsg(object):
    def __init__(self, lastRequestedAddress):
        self.addr = lastRequestedAddress

    def make_msg(self, addr):
        """Confirm subscription to the address you last texted"""
        return "You've subscribed to demolition alerts near {}. You'll receive a text 3 days prior to any scheduled knock-downs within 500ft. Protect your family against health risks during demolition by keeping windows and doors closed and children and pets inside. Text 'REMOVE' to unsubscribe.".format(addr)

class UnsubscribeMsg(object):
    def __init__(self, activeAddresses):
        self.addrs = activeAddresses

    def make_msg(self, addrs):
        """Unsubscribe from all active addresses"""
        return "You're unsubscribed to demolition alerts near: \n{}. \nText a street address to find demos nearby or to re-subscribe.".format((";\n").join(addrs))
 
class DefaultMsg(object):
    def __init__(self):
        pass

    def make_msg(self):
        """Default message for anything you send us besides ADD, END or a valid address"""
        return "To find properties scheduled for demolition nearby, please text a street address (eg '2 Woodward')."
