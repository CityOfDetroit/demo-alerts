import os
from datetime import datetime
from sodapy import Socrata

soda_client = Socrata("data.detroitmi.gov", os.environ['SODA_TOKEN'], os.environ['SODA_USER'], os.environ['SODA_PASS'])

class DemoMsg(object):
    def __init__(self, locatedAddress):
        self.addr = locatedAddress

    def make_msg(self, addr):
        """Find upcoming demolitions near an already geocoded address and list them in a text message"""
        lat = addr['location']['y']
        lng = addr['location']['x']

        # query socrata dataset for demos within 500ft (155m) and n days (todo)
        demos = soda_client.get("8wnn-qcxj", where="within_circle(location, {}, {}, 155)".format(lat, lng))
        print(demos)

        # build the text
        if len(demos) > 0:
            list_demos = []
            for d in demos:
                formatted_demo = "{} on {}".format(d['address'], datetime.fromtimestamp(int(d['demo_date'])).strftime('%m-%d-%Y'))
                list_demos.append(formatted_demo)

            return "{} demos scheduled near {} in the next 5 days: \n{}. \nDates subject to change. Text 'ADD' to subscribe to future demo alerts near this address.".format(len(demos), addr['address'][:-7], (";\n").join(list_demos))
        else:
            return "No demos scheduled near {} in the next 5 days. Text 'ADD' to subscribe to future demo alerts near this address.".format(addr['address'][:-7])

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
