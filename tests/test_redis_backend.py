"""Tests for the activity tracker redis backend.

To test with a real redis server instead of the builtin fake server, set the
ACTIVITY_TRACKER_TEST_REAL_REDIS environment variable to the number of a local
database. All data in that database will be destroyed.
"""
import datetime
import os
import unittest
import uuid

import redis

from activity_tracker.backends import redis as redis_backend
from activity_tracker.tracker import ActivityTracker

import fakeredis

REAL_REDIS_ENV = "ACTIVITY_TRACKER_TEST_REAL_REDIS"

# A few dummy testing values
UUID1 = "752a46a2-0ae6-3346-9838-d4a1313b9637"
UUID2 = "e1932785-4860-34f3-a593-8ddf66fc4894"
UUID3 = "eb05ee25-807f-3d40-b853-674cf25a1d46"
UUID4 = "d3ba4e99-1e47-3a0e-9c2f-3d9f10a3d1fe"


class RedisBackendTestCase(unittest.TestCase):
    def setUp(self):
        if REAL_REDIS_ENV not in os.environ:
            redis_backend.redis.Redis = fakeredis.FakeRedis
        self.backend = redis_backend.RedisBackend(
            db=int(os.environ.get(REAL_REDIS_ENV, "0"))
        )
        self.conn = self.backend.get_conn(0)
        self.conn.flushdb()

    def tearDown(self):
        if REAL_REDIS_ENV not in os.environ:
            redis_backend.redis = redis
        self.conn.flushdb()

    def check_keys(self, *keys):
        self.assertEqual(set(keys), set(self.conn.keys()))

    def check_set(self, key, *args):
        self.assertEqual(set(args), self.conn.smembers(key))

    def test_track(self):
        def track(**kwargs):
            self.backend.track(
                ActivityTracker.PERIOD_DAILY, date=datetime.date(2014, 1, 1), **kwargs
            )

        track(id=1)

        track(id=uuid.UUID(UUID1), bucket="anon")

        track(id=uuid.UUID(UUID2), bucket="anon")

        track(id=uuid.UUID(UUID3), bucket="anon")
        track(id=4, bucket="auth:staff", old_id=uuid.UUID(UUID3), old_bucket="anon")

        track(id=5, bucket="auth:staff", old_id=uuid.UUID(UUID4), old_bucket="anon")

        self.check_keys(
            "active:daily-20140101:raw",
            "active:daily-20140101:raw:anon",
            "active:daily-20140101:raw:auth:staff",
        )
        self.check_set("active:daily-20140101:raw", "1")
        self.check_set("active:daily-20140101:raw:anon", UUID1, UUID2)
        self.check_set("active:daily-20140101:raw:auth:staff", "4", "5")

    def test_collapse(self):
        self.conn.sadd("active:daily-20140101:raw:group1", "1", "2", "3")
        self.conn.sadd("active:daily-20140101:raw:group2", "1", "4", "5")
        self.conn.sadd("active:daily-20140101:raw:group3", "1", "2", "5", "6")
        self.conn.sadd("active:daily-20140102:raw:group1", "7")

        self.backend.collapse(
            ActivityTracker.PERIOD_DAILY,
            date=datetime.date(2014, 1, 2),
            buckets=[
                "group1",
                "group2",
                "group3",
            ],
            aggregate_buckets={
                "agg1": ["group1"],
                "agg2": ["group1", "group2"],
                "agg3": ["group1", "group2", "group3"],
            },
        )

        self.check_keys(
            "active:daily-20140101:group1",
            "active:daily-20140101:group2",
            "active:daily-20140101:group3",
            "active:daily-20140101:agg1",
            "active:daily-20140101:agg2",
            "active:daily-20140101:agg3",
            "active:daily-20140102:raw:group1",
        )
        self.assertEqual("3", self.conn.get("active:daily-20140101:group1"))
        self.assertEqual("3", self.conn.get("active:daily-20140101:group2"))
        self.assertEqual("4", self.conn.get("active:daily-20140101:group3"))
        self.assertEqual("3", self.conn.get("active:daily-20140101:agg1"))
        self.assertEqual("5", self.conn.get("active:daily-20140101:agg2"))
        self.assertEqual("6", self.conn.get("active:daily-20140101:agg3"))

    def test_lookup(self):
        self.conn.set("active:monthly-201310:group1", "83")
        self.conn.set("active:monthly-201311:group1", "5")
        self.conn.set("active:monthly-201311:group2", "10")
        self.conn.set("active:monthly-201312:group1", "6")
        self.conn.set("active:monthly-201401:group2", "7")
        self.conn.set("active:monthly-201402:group2", "8")
        self.assertEqual(
            [
                (datetime.date(2013, 11, 1), {"group1": 5, "group2": 10}),
                (datetime.date(2013, 12, 1), {"group1": 6, "group2": 0}),
                (datetime.date(2014, 1, 1), {"group1": 0, "group2": 7}),
            ],
            self.backend.lookup(
                ActivityTracker.PERIOD_MONTHLY,
                start=datetime.date(2013, 10, 5),
                end=datetime.date(2014, 2, 5),
                buckets=["group1", "group2"],
            ),
        )

    def test_lookup_no_values(self):
        self.assertEqual(
            [],
            self.backend.lookup(
                ActivityTracker.PERIOD_MONTHLY,
                start=datetime.date(2013, 10, 5),
                end=datetime.date(2013, 10, 5),
            ),
        )
