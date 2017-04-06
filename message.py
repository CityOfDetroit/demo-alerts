import os
from datetime import datetime
from sodapy import Socrata

soda_client = Socrata("data.detroitmi.gov", os.environ['SODA_TOKEN'], os.environ['SODA_USER'], os.environ['SODA_PASS'])

class Message(object):
    def __init__(self, locatedAddress):
        self.addr = locatedAddress
        self.hasDemos = False

    def make_demo_msg(self, addr):
        """Find upcoming demolitions near an already geocoded address and list them in a text message"""
        lat = addr['location']['y']
        lng = addr['location']['x']

        # query Socrata dataset for demos within 500ft (155m) and n days (todo)
        demos = soda_client.get("8wnn-qcxj", where="within_circle(location, {}, {}, 155)".format(lat, lng))
        print(demos)

        # build the text
        if len(demos) > 0:
            self.hasDemos = True
            list_demos = []
            
            for d in demos:
                formatted_demo = "{} on {}".format(d['address'], datetime.fromtimestamp(int(d['demo_date'])).strftime('%m-%d-%Y'))
                list_demos.append(formatted_demo)

            return "{} demos scheduled near {} in the next 5 days: \n{}. \nDates subject to change. Text 'ADD' to subscribe to future demo alerts near this address.".format(len(demos), addr['address'], (";\n").join(list_demos))
        else:
            return "No demos scheduled near {} in the next 5 days. Text 'ADD' to subscribe to future demo alerts near this address.".format(addr['address'])
