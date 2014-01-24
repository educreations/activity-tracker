from __future__ import absolute_import

import datetime
import hashlib
import itertools
import logging

import redis

from .base import BaseBackend
from ..tracker import ActivityTracker

log = logging.getLogger(__name__)

__all__ = ['RedisBackend']


class RedisBackend(BaseBackend):
    """Redis backend for activity tracker.

    This stores data in redis with 2 key formats:
        track() creates keys like:
            active:<timeperiod>:raw[:<bucket>] -> set<id>
        collapse() converts them to keys like:
            active:<timeperiod>[:<bucket>] -> count

    Sharding:
        All data for a given time period / bucket pair must be stored on the
        same redis server in the same database. If multiple buckets are used
        together in a track call (bucket=, old_bucket=) or a collapse call,
        they must also be in the same database. If you are using this library
        to track multiple independent data sets, you can use its builtin
        sharding feature. To do so, provide any overrides for the connection or
        database parameters in the 'shards' keyword argument, like:
            shards=[{}, {'db': 1}, {'host': 'server2'}]
        and provide the appropriate shard=N argument to the track/collapse/
        lookup calls.

    Keyword arguments:
        host:           Default redis host. Defaults to 'localhost'.
        port:           Default redis port. Defaults to 6379.
        db:             Default redis db. Defaults to 0.
        socket_timeout: Socket timeout in seconds. Defaults to no timeout.
        shards:         A list of per-shard overrides for the above parameters.
                        Defaults to [{}], meaning a single shard (0) which uses
                        the above parameters.
    """

    PERIOD_FORMATS = {
        ActivityTracker.PERIOD_DAILY: 'daily-{0:%Y%m%d}',
        ActivityTracker.PERIOD_MONTHLY: 'monthly-{0:%Y%m}',
    }

    def __init__(self, host='localhost', port=6379, db=0, socket_timeout=None,
            shards=None):
        self.defaults = {
            'host': host,
            'port': port,
            'db': db,
            'socket_timeout': socket_timeout,
        }
        self.shards = shards or [{}]
        self.conns = {}

    def get_conn(self, shard):
        conn = self.conns.get(shard)
        if conn is None:
            params = self.defaults.copy()
            params.update(self.shards[shard])
            conn = redis.Redis(**params)
            self.conns[shard] = conn
        return conn

    def track(self, period,
            id=None, bucket=None,
            old_id=None, old_bucket=None,
            date=None, shard=0):
        """Record activity by a specified entity.

        Redis-specific keyword arguments:
            shard: The shard for this dataset. See class docs for details.

        See activity_tracker.tracker.ActivityTracker for descriptions of the
        other arguments.
        """
        conn = self.get_conn(shard)
        if date is None:
            date = datetime.date.today()
        period_str = self.PERIOD_FORMATS[period].format(date)
        add_key = make_key('active', period_str, 'raw', bucket)
        old_key = make_key('active', period_str, 'raw', old_bucket)

        if id is not None and old_id is not None:
            with conn.pipeline() as pipe:
                pipe.sadd(add_key, str(id))
                pipe.srem(old_key, str(old_id))
                pipe.execute()
        elif id is not None:
            conn.sadd(add_key, str(id))
        elif old_id is not None:
            conn.srem(old_key, str(old_id))

    def collapse(self, period,
            date=None, max_periods=1,
            buckets=None, aggregate_buckets=None,
            shard=0):
        """Collapse raw data into aggregate counts.

        Redis-specific keyword arguments:
            shard: The shard for this dataset. See class docs for details.

        See activity_tracker.tracker.ActivityTracker for descriptions of the
        other arguments.
        """
        conn = self.get_conn(shard)
        if date is None:
            date = datetime.date.today()

        sentinel = object()
        test_bucket = list(buckets or aggregate_buckets or [sentinel])[0]
        if test_bucket is sentinel:
            return

        queue = []
        period_fmt = self.PERIOD_FORMATS[period]
        for period_dt, period_str in iter_period_reverse(date, period_fmt):
            if conn.exists(make_key('active', period_str, test_bucket)):
                break
            queue.insert(0, period_str)
            if len(queue) >= max_periods:
                break

        for period_str in queue:
            self.collapse_single(
                buckets or [], aggregate_buckets or {}, conn, period_str)

    def collapse_single(self, buckets, aggregate_buckets, conn, period_str):
        log.info('Collapsing activity data for time period %r', period_str)
        to_set = {}
        to_remove = set()
        for bucket in buckets:
            in_key = make_key('active', period_str, 'raw', bucket)
            out_key = make_key('active', period_str, bucket)
            to_set[out_key] = conn.scard(in_key)
            to_remove.add(in_key)
        for agg_bucket, sources in aggregate_buckets.iteritems():
            in_keys = [make_key('active', period_str, 'raw', source)
                for source in sources]
            out_key = make_key('active', period_str, agg_bucket)
            if len(sources) == 1:
                to_set[out_key] = conn.scard(in_keys[0])
            elif len(sources) == 2:
                temp_key = make_temp_key('inter', in_keys)
                conn.sinterstore(temp_key, *in_keys)
                to_set[out_key] = (
                    conn.scard(in_keys[0]) + conn.scard(in_keys[1]) -
                    conn.scard(temp_key))
                conn.delete(temp_key)
            else:
                temp_key = make_temp_key('union', in_keys)
                conn.sunionstore(temp_key, *in_keys)
                to_set[out_key] = conn.scard(temp_key)
                conn.delete(temp_key)
            to_remove.update(in_keys)

        with conn.pipeline() as pipe:
            for key, value in to_set.iteritems():
                pipe.set(key, value)
            for key in to_remove:
                pipe.delete(key)
            pipe.execute()

    def lookup(self, period, start=None, end=None, buckets=None, shard=0):
        """Lookup data for a time range.

        Redis-specific keyword arguments:
            shard: The shard for this dataset. See class docs for details.

        See activity_tracker.tracker.ActivityTracker for descriptions of the
        other arguments.
        """
        conn = self.get_conn(shard)
        if end is None:
            end = datetime.date.today()
        if start is None:
            start = end - datetime.timedelta(days=365)

        period_fmt = self.PERIOD_FORMATS[period]
        result = []
        keys = []
        result_map = []
        for period_dt, period_str in iter_period_reverse(end, period_fmt):
            if period == ActivityTracker.PERIOD_MONTHLY:
                period_dt = period_dt.replace(day=1)
            if period_dt < start:
                break
            period_result = {}
            result.insert(0, (period_dt, period_result))
            for bucket in buckets or [None]:
                keys.append(make_key('active', period_str, bucket))
                result_map.append((period_result, bucket))

        for (period_result, bucket), value in itertools.izip(
                result_map, conn.mget(keys)):
            period_result[bucket] = int(value) if value is not None else 0
        return result


def make_key(*pieces):
    return ':'.join(piece for piece in pieces if piece)


def make_temp_key(temp_type, pieces):
    md5 = hashlib.md5(' '.join(pieces)).hexdigest()
    return make_key('temp', temp_type, md5)


def iter_period_reverse(start, fmt):
    dt = start
    last_dt_str = fmt.format(dt)
    while True:
        dt -= datetime.timedelta(days=1)
        dt_str = fmt.format(dt)
        if dt_str != last_dt_str:
            yield dt, dt_str
            last_dt_str = dt_str
