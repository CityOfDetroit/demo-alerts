import os
from datetime import datetime, timedelta
from sodapy import Socrata

soda_client = Socrata("data.detroitmi.gov", os.environ['SODA_TOKEN'], os.environ['SODA_USER'], os.environ['SODA_PASS'])

# define static text messages
language = {
    'dlba': "\nDates may change.",
    'dhd': "To help protect your family during demos: \n- Keep children & pets inside \n- Close windows & doors. \nText 'HEALTH' to learn more.",
    'add': "Text 'ADD' for alerts near here.",
    'remove': "Text 'REMOVE' to unsubscribe.",
    'health': "Most old houses have lead paint, so there might be lead in demo dust. Pregnant women & parents of young children living near demos can talk with a Health Educator by texting 'EDU'. Cleaning kits available for pickup at Rec Centers, learn more at http://www.detroitmi.gov/LeadSafe",
    'edu': "Your phone number has been sent to the Detroit Health Dept & you'll receive a call soon. Text an address to search again.",
    'default': "Sorry we can't process that! To find houses planned for demolition nearby, please text a street address (eg '9385 E Vernor' or '2 Woodward')."
}

class DemoMsg(object):
    def __init__(self, locatedAddress):
        self.addr = locatedAddress

    def make_msg(self):
        """ Find upcoming demolitions near an already geocoded address and list them in a text message """
        lat = self.addr['location']['y']
        lng = self.addr['location']['x']

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
                formatted_demo_soon = "{} the week of {}".format(d['address'], datetime.strptime((d['demolish_by_date']), '%Y-%m-%dT%H:%M:%S').strftime('%m-%d-%Y'))
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
            return "Demolitions are scheduled near {}: \n{}. {} {} {}".format(self.addr['address'][:-7], (";\n").join(list_demos_soon), language['dlba'], language['dhd'], language['add'])

        elif len(full_pipeline) > 0 and len(demos_soon) < 1:
            return "Demolitions are planned near {} soon: \n{}. {} {} {}".format(self.addr['address'][:-7], (";\n").join(full_pipeline), language['dlba'], language['dhd'], language['add'])

        elif len(demos_soon) > 0 and len(full_pipeline) > 0:
            return "Demolitions are scheduled near {}: \n{}. \nMore houses nearby will be demolished soon: \n{}. {} {} {}".format(self.addr['address'][:-7], (";\n").join(list_demos_soon), (";\n").join(full_pipeline), language['dlba'], language['dhd'], language['add'])

        else: 
            return "No demolitions planned near {}. {} {}".format(self.addr['address'][:-7], language['dhd'], language['add'])

class SubscribeMsg(object):
    def __init__(self, lastRequestedAddress):
        self.addr = lastRequestedAddress

    def make_msg(self):
        """ Confirm subscription to the address you last texted """
        return "You've subscribed to alerts near {}. Alerts are sent 3 days before demos within 500ft. {}".format(self.addr, language['remove'])

class UnsubscribeMsg(object):
    def __init__(self, activeAddresses):
        self.addrs = activeAddresses

    def make_msg(self):
        """ Unsubscribe from all active addresses """
        return "You're unsubscribed to alerts near: \n{}. \nText an address to find demos nearby or to re-subscribe.".format((";\n").join(self.addrs))

class HealthMsg(object):
    def __init__(self):
        pass

    def make_msg(self):
        """" Get additional info from the Health Department """
        return language['health']

class CallMsg(object):
    def __init__(self):
        pass

    def make_msg(self):
        """ Request a call from a Health Educator """
        return language['edu']

class DefaultMsg(object):
    def __init__(self):
        pass

    def make_msg(self):
        """ Default message for anything you send us besides HEALTH, ADD, REMOVE or a valid address """
        return language['default']
