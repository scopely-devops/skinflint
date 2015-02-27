skinflint
=========

Tools to slice and aggregate AWS detailed billing reports.

Basic Usage
-----------

First, download your detailed billing reports from S3.  Then:

    >>> from skinflint.billreader import DetailedBillingReader
    >>> dbr = DetailedBillingReader('path_to_detailed_billing.csv')
    >>> from skinflint.slice import slicer
    >>> slices = slicer(dbr)

You can also add more billing reports to the same slice collection:

    >>> dbr = DetailedBillingReader('path_to_another_detailed_billing.csv')
    >>> slices.load(dbr)

Once you have all of the data loaded, you can get aggregated data for any time
period using the ``aggregate`` method of the SuperSlice object:

    >>> start = datetime.datetime(...)
    >>> end = datetime.datetime(...)
    >>> aggregated = slices.aggregate(start, end)

There are also convenience methods to get commonly used aggregations:

    >>> latest = slices.latest()  # last full day of data
    >>> one_day_ago = slices.one_day_ago()
    >>> one_week_ago = slices.one_week_ago()
    >>> one_month_ago = slices.one_month_ago()


Each slice or aggregated slice can have metrics associated with them.  At the
moment only one metric is active which computes a number of totals.  To see the
metric data:

    >>> lastest.metrics[0].dump()

This will print the collected data from the metric to the console.


