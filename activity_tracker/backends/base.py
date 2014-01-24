class BaseBackend(object):
    """The base backend class.

    All backends implement these methods and accept these arguments, though
    some may also accept additional keyword arguments.
    """

    def track(self, period, id=None, bucket=None,
            old_id=None, old_bucket=None, date=None):
        """Record activity by a specified entity.

        Arguments:
            period: One of the PERIOD_* constants from
                    activity_tracker.tracker.ActivityTracker.

        See activity_tracker.tracker.ActivityTracker for descriptions of the
        other arguments.
        """
        raise NotImplementedError()

    def collapse(self, period, date=None, max_periods=1,
            buckets=None, aggregate_buckets=None):
        """Collapse raw data into aggregate counts.

        Arguments:
            period: One of the PERIOD_* constants from
                    activity_tracker.tracker.ActivityTracker.

        See activity_tracker.tracker.ActivityTracker for descriptions of the
        other arguments.
        """
        raise NotImplementedError()

    def lookup(self, period, start=None, end=None, buckets=None):
        """Lookup data for a time range.

        Arguments:
            period: One of the PERIOD_* constants from
                    activity_tracker.tracker.ActivityTracker.

        See activity_tracker.tracker.ActivityTracker for descriptions of the
        other arguments.
        """
        raise NotImplementedError()
