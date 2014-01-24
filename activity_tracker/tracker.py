import importlib

from .backends.base import BaseBackend

__all__ = ['ActivityTracker']


class ActivityTracker(object):
    """Activity Tracker.

    Keyword arguments:
        periods: A list of PERIOD_* constants for which activity should be
                 tracked. Used as a default for track() and collapse() calls.
        backend: The storage backend to use. Can be any of the following:
                 - the name of a builtin backend ('redis')
                 - the fully qualified name of a backend class
                   ('foo.bar.CustomBackend')
                 - an instance of a subclass of
                   activity_tracker.base.BaseBackend

    Any additional keyword arguments are passed to the backend's constructor.
    """

    PERIOD_DAILY = 'daily'
    PERIOD_MONTHLY = 'monthly'

    def __init__(self, periods=None, backend=None, **kwargs):
        self._periods = periods

        if isinstance(backend, BaseBackend):
            self._backend = backend
            if kwargs:
                raise ValueError(
                    'Cannot pass backend keyword arguments when providing a '
                    'backend instance.')
        elif isinstance(backend, basestring):
            if '.' not in backend:
                backend = 'activity_tracker.backends.{}.{}Backend'.format(
                    backend, backend.title())
            module_name, class_name = backend.rsplit('.', 1)
            module = importlib.import_module(module_name)
            self._backend = getattr(module, class_name)(**kwargs)
        else:
            raise TypeError('Invalid backend')

    #
    # Track
    #

    def track(self, periods=None, **kwargs):
        """Record activity by a specified entity.

        Keyword arguments:
            periods:    A list of 1 or more of the PERIOD_* constants for which
                        this activity should be tracked. Defaults to the list
                        provided to the constructor.
            id:         A unique id of the enitity to track. Can be any
                        str()-able object.
            bucket:     An optional name of a bucket to which the entity
                        belongs.
            old_id:     If the entity's id and/or bucket changed, the old id of
                        the entity. Can by any str()-able object.
            old_bucket: If the entity's id and/or bucket changed, the old
                        bucket to which the entity belonged.
            date:       A datetime.date indicating the day on which the
                        activity occurred. Defaults to the current day (local
                        time).

        Any additional keyword arguments are passed to the backend's track()
        method.
        """
        for period in periods or self._periods:
            self._backend.track(period, **kwargs)

    def track_daily(self, **kwargs):
        """Alias for track(periods=[PERIOD_DAILY], ...)."""
        return self.track(periods=[self.PERIOD_DAILY], **kwargs)

    def track_monthly(self, **kwargs):
        """Alias for track(periods=[PERIOD_MONTHLY], ...)."""
        return self.track(periods=[self.PERIOD_MONTHLY], **kwargs)

    #
    # Collapse
    #

    def collapse(self, periods=None, **kwargs):
        """Collapse raw data into aggregate counts.

        Keyword arguments:
            periods:           A list of 1 or more of the PERIOD_* constants
                               for which raw activity data should be collapsed.
                               Defaults to the list provided to the
                               constructor.
            date:              A datetime.date after the range(s) to be
                               collapsed. Defaults to the current day (local
                               time).
            max_periods:       The maximum number of periods of each type to
                               attempt to collapse. Defaults to 1.
            buckets:           A list of bucket names that were used in the
                               corresponding track_* calls.
            aggregate_buckets: A dict of {agg_bucket: [raw_bucket, ...]}.
                               Each aggregate bucket will be computed as the
                               union of its raw buckets.

        Any additional keyword arguments are passed to the backend's collapse()
        method.
        """
        for period in periods or self._periods:
            self._backend.collapse(period, **kwargs)

    def collapse_daily(self, **kwargs):
        """Alias for collapse(periods=[PERIOD_DAILY], ...)."""
        return self.collapse(periods=[self.PERIOD_DAILY], **kwargs)

    def collapse_monthly(self, **kwargs):
        """Alias for collapse(periods=[PERIOD_MONTHLY], ...)."""
        return self.collapse(periods=[self.PERIOD_MONTHLY], **kwargs)

    #
    # Lookup
    #

    def lookup(self, period=None, **kwargs):
        """Lookup data for a time range.

        Keyword arguments:
            period:  One of the PERIOD_* constants.
            start:   A datetime.date in the first {period} to lookup. Defaults
                     to 365 days before end.
            end:     A datetime.date after the last {period} to lookup.
                     Defaults to the current day (local time).
            buckets: A list of bucket names to lookup.

        Returns:
            A list of (date, date_buckets) tuples for each period in the
            range of [start, end).
                date: a datetime.date at the start of the period.
                date_buckets: a dict of {bucket: value} for the period.

        Any additional keyword arguments are passed to the backend's lookup()
        method.
        """
        return self._backend.lookup(period, **kwargs)

    def lookup_daily(self, **kwargs):
        """Alias for lookup(period=PERIOD_DAILY, ...)."""
        return self.lookup(period=self.PERIOD_DAILY, **kwargs)

    def lookup_monthly(self, **kwargs):
        """Alias for lookup(period=PERIOD_MONTHLY, ...)."""
        return self.lookup(period=self.PERIOD_MONTHLY, **kwargs)
