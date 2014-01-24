class BaseBackend(object):
    def track(self, period, id=None, bucket=None,
            old_id=None, old_bucket=None, date=None):
        raise NotImplementedError()

    def collapse(self, period, date=None, max_periods=1,
            buckets=None, aggregate_buckets=None):
        raise NotImplementedError()

    def lookup(self, period, start=None, end=None, buckets=None):
        raise NotImplementedError()
