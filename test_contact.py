import os
import sqlite3
import contact
import unittest

class TestSubscribersDb(unittest.TestCase):
    def setUp(self):
        """Setup a temporary database"""
        conn = sqlite3.connect("db/test.db")
        c = conn.cursor()

        # create a table
        c.execute("CREATE TABLE subscribers (active integer, phone text, matched_address text, location text, subscribed_date text, last_alert_date text)")

        # insert some sample data
        texters = [
            (1, '3135551111', '3600 WAYBURN', '(-82.9474, 42.3889)', '2017-05-10', None),
            (1, '3135551111', '2 WOODWARD AVENUE', '(-82.9474, 42.3889)', '2017-05-10', None),
            (1, '3135552222', '19150 Marx St, Detroit', '(-83.08405, 42.43353)', '2017-05-11', None),
            (1, '3135553333', '3600 WAYBURN', '(-82.9474, 42.3889)', '2017-05-09', None),
            (1, '3135554444', '3855 IROQUOIS', '(-83.00383, 42.3704)', '2017-05-11', None)
        ]
        c.executemany("INSERT INTO subscribers VALUES (?,?,?,?,?,?)", texters)

        # save data to database
        conn.commit()

    def tearDown(self):
        """Delete the database"""
        os.remove("db/test.db")
