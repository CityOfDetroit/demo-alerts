import os
from datetime import datetime, timedelta
from sodapy import Socrata

soda_client = Socrata("data.detroitmi.gov", os.environ['SODA_TOKEN'], os.environ['SODA_USER'], os.environ['SODA_PASS'])

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
            return "Demolitions are scheduled near {} this week: \n{}. \nDates may change. To help protect your family during demos: \n- Keep children and pets inside \n- Close windows and doors. \nText 'HEALTH' to learn more. Text 'ADD' for alerts near here.".format(self.addr['address'][:-7], (";\n").join(list_demos_soon))

        elif len(full_pipeline) > 0 and len(demos_soon) < 1:
            return "Demolitions are planned near {} soon: \n{}. \nDates may change. To help protect your family during demos: \n- Keep children and pets inside \n- Close windows and doors. \nText 'HEALTH' to learn more. Text 'ADD' for alerts near here.".format(self.addr['address'][:-7], (";\n").join(full_pipeline))

        elif len(demos_soon) > 0 and len(full_pipeline) > 0:
            return "Demolitions are scheduled near {} this week: \n{}. \nMore houses nearby will be demolished soon: \n{}. \nDates may change. To help protect your family during demos: \n- Keep children and pets inside \n- Close windows and doors. \nText 'HEALTH' to learn more. Text 'ADD' for alerts near here.".format(self.addr['address'][:-7], (";\n").join(list_demos_soon), (";\n").join(full_pipeline))

        else: 
            return "No demolitions planned near {}. To help protect your family during demos: \n- Keep children and pets inside \n- Close windows and doors. \nText 'HEALTH' to learn more. Text 'ADD' for alerts near here.".format(self.addr['address'][:-7])

class SubscribeMsg(object):
    def __init__(self, lastRequestedAddress):
        self.addr = lastRequestedAddress

    def make_msg(self):
        """ Confirm subscription to the address you last texted """
        return "You've subscribed to alerts near {}. Alerts will be sent 3 days before demos within 500ft. Text 'REMOVE' to unsubscribe.".format(self.addr)

class UnsubscribeMsg(object):
    def __init__(self, activeAddresses):
        self.addrs = activeAddresses

    def make_msg(self):
        """ Unsubscribe from all active addresses """
        return "You're unsubscribed to alerts near: \n{}. \nText a street address to find demolitions nearby or to re-subscribe.".format((";\n").join(self.addrs))

class HealthMsg(object):
    def __init__(self):
        pass

    def make_msg(self):
        """" Get additional info from the Health Department """
        return "Most old houses have lead paint, so there might be lead in demo dust. Learn more about lead from the Detroit Health Department at www.detroitmi.gov/leadsafe or (313) 876-4000."

class DefaultMsg(object):
    def __init__(self):
        pass

    def make_msg(self):
        """ Default message for anything you send us besides HEALTH, ADD, REMOVE or a valid address """
        return "To find houses planned for demolition nearby, please text a street address (eg '2 Woodward')."
