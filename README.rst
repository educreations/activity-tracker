Activity Tracker
================

A library to perform daily-active-user (and similar) tracking.


Installation
------------

Install the package ``activity-tracker`` from PyPI using `pip`_:

.. code:: bash

    $ pip install -U activity-tracker


Basic Usage
-----------

.. code:: python

    import six

    from activity_tracker.tracker import ActivityTracker

    tracker = ActivityTracker(
        periods=[ActivityTracker.PERIOD_DAILY],
        backend='redis')

    # Record activity for a couple users.
    tracker.track(id=123)
    tracker.track(id=123)
    tracker.track(id=456)

    # At the end of the time period (days in this example), collapse the raw
    # data into counts.
    tracker.collapse()

    # After the data is collapsed, it can be queried. In this example, bucket
    # is always None, since no bucket was provided to track (and collapse).
    import datetime
    today = datetime.date.today()
    week_ago = today - datetime.timedelta(days=7)
    for date, date_data in tracker.lookup_daily(start=week_ago, end=today):
        print date
        for bucket, count in six.iteritems(date_data):
            print '  {}: {}'.format(bucket, count)


Buckets
^^^^^^^

You can use multiple buckets for tracking different types of users,
devices, etc.

.. code:: python

    tracker.track(id='random-session-1', bucket='anon')
    tracker.track(id='random-session-2', bucket='anon')
    tracker.track(id=456, bucket='auth')

    tracker.collapse(buckets=['anon', 'auth'])

    data = tracker.lookup_daily(
        start=week_ago, end=today,
        buckets=['anon', 'auth'])


Changing ids and/or buckets
^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can also change a user's id and/or bucket, primarily to allow replacing an
anonymous session id with an authenticated user's id.

.. code:: python

    tracker.track(id='random-session-1', bucket='anon')
    tracker.track(id='random-session-2', bucket='anon')

    # User logs in; replace ('anon', 'random-session-2') with ('auth', '123')
    tracker.track(
        id=123, bucket='auth',
        old_id='random-session-2', old_bucket='anon')


Aggregate buckets
^^^^^^^^^^^^^^^^^

When collapsing data, you can also create aggregate buckets which contain the
count of the union of 2 or more other buckets. This is useful for computing
totals of sets of users that may overlap.

.. code:: python

    tracker.track(id='user1@example.com', bucket='site1')
    tracker.track(id='jdoe@example.com', bucket='site1')
    tracker.track(id='jdoe@example.com', bucket='site2')
    tracker.track(id='user2@example.com', bucket='site2')

    tracker.collapse(
        buckets=['site1', 'site2'],
        aggregate_buckets={'total': ['site1', 'site2']})

When looking up data for this day, there will be 3 buckets::

    site1: 2
    site2: 2
    total: 3


License
-------

Copyright © 2023, Educreations, Inc under the MIT LICENSE.


.. _`pip`: http://www.pip-installer.org/
