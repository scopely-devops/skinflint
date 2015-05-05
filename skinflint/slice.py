# Copyright (c) 2015 Scopely, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
# http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.

import datetime
import calendar

from dateutil.tz import tzlocal, tzutc
import dateutil.parser
import pytz

from skinflint.metric import TotalUsage, InstanceCost, DataTransfer


# The following utility functions were copied directly from botocore.utils


def parse_timestamp(value):
    if isinstance(value, (int, float)):
        # Possibly an epoch time.
        return datetime.datetime.fromtimestamp(value, tzlocal())
    else:
        try:
            return datetime.datetime.fromtimestamp(float(value), tzlocal())
        except (TypeError, ValueError):
            pass
    try:
        return dateutil.parser.parse(value)
    except (TypeError, ValueError) as e:
        raise ValueError('Invalid timestamp "%s": %s' % (value, e))


def parse_to_aware_datetime(value):
    if isinstance(value, datetime.datetime):
        datetime_obj = value
    else:
        datetime_obj = parse_timestamp(value)
    if datetime_obj.tzinfo is None:
        datetime_obj = datetime_obj.replace(tzinfo=tzutc())
    else:
        datetime_obj = datetime_obj.astimezone(tzutc())
    return datetime_obj


class Slice(object):

    def __init__(self, start, end, retain_lineitems=False):
        if start:
            self.start = parse_to_aware_datetime(start)
        else:
            self.start = start
        if end:
            self.end = parse_to_aware_datetime(end)
        else:
            self.end = end
        self._retain_lineitems = retain_lineitems
        self._lineitems = []
        self.metrics = [TotalUsage(), InstanceCost(), DataTransfer()]

    def __add__(self, other):
        for metric, other_metric in zip(self.metrics, other.metrics):
            metric + other_metric

    def add_lineitem(self, lineitem):
        if self._retain_lineitems:
            self._lineitems.append(lineitem)
        for metric in self.metrics:
            metric.add(lineitem)

    @property
    def metric_names(self):
        return self.metrics.keys()


class SuperSlice(object):

    def __init__(self, now=None):
        self.slices = {}
        self.non_lineitems = []
        self.onetime_charges = []
        self.start = None
        self.end = None
        self.now = now
        if self.now is None:
            self.now = pytz.utc.localize(datetime.datetime.utcnow())

    def add(self, new_slice):
        if not new_slice.start and not new_slice.end:
            self.non_lineitems.append(new_slice)
        else:
            if self.start is None:
                self.start = new_slice.start
            elif self.start > new_slice.start:
                self.start = new_slice.start
            if self.end is None:
                self.end = new_slice.end
            elif self.end < new_slice.end:
                self.end = new_slice.end
            slice_key = '%s-%s' % (new_slice.start, new_slice.end)
            if slice_key not in self.slices:
                self.slices[slice_key] = new_slice
            else:
                self.slices[slice_key] + new_slice

    def load(self, billreader):
        new_slice = None
        start = None
        end = None
        done = False
        while not done:
            try:
                lineitem = next(billreader)
            except StopIteration:
                done = True
                continue
            usage_start = lineitem['UsageStartDate']
            usage_end = lineitem['UsageEndDate']
            if lineitem['RateId'] != '0':
                if usage_start != start or usage_end != end:
                    if new_slice:
                        self.add(new_slice)
                    start = usage_start
                    end = usage_end
                    new_slice = Slice(start, end)
            new_slice.add_lineitem(lineitem)
        if new_slice:
            self.add(new_slice)

    def metrics(self):
        metrics = []
        if self.slices:
            metrics = self.slices[0].metrics
        return metrics

    def aggregate(self, start, end):
        aggregate_slice = Slice(start, end)
        for slice_key in self.slices:
            new_slice = self.slices[slice_key]
            if new_slice.start >= start and new_slice.end <= end:
                aggregate_slice + new_slice
        return aggregate_slice

    def all(self):
        return self.aggregate(self.start, self.end)

    def _slice_a_day(self, days_ago):
        now = self.now - days_ago
        start = datetime.datetime(now.year, now.month, now.day)
        start = pytz.utc.localize(start)
        end = start + datetime.timedelta(hours=23, minutes=59, seconds=59)
        return self.aggregate(start, end)

    def latest(self):
        one_day = datetime.timedelta(hours=24)
        return self._slice_a_day(one_day)

    def one_day_ago(self):
        two_days = datetime.timedelta(hours=24 * 2)
        return self._slice_a_day(two_days)

    def one_week_ago(self):
        one_week = datetime.timedelta(hours=24 * 8)
        return self._slice_a_day(one_week)

    def one_month_ago(self):
        one_month = datetime.timedelta(hours=24 * 29)
        return self._slice_a_day(one_month)

    def month(self, year, month):
        month_start = pytz.utc.localize(
            datetime.datetime(year, month, 1))
        month_end = pytz.utc.localize(
            datetime.datetime(year, month + 1, 1, 0, 0, 0))
        return self.aggregate(month_start, month_end)

    def this_month(self):
        return self.month(self.now.year, self.now.month)

    def last_month(self):
        then = self.now - datetime.timedelta(days=self.now.day + 1)
        return self.month(then.year, then.month)

    def last_month_to_date(self):
        then = self.now - datetime.timedelta(days=self.now.day + 1)
        _, ndays = calendar.monthrange(then.year, then.month)
        month_start = pytz.utc.localize(
            datetime.datetime(then.year, then.month, 1))
        month_end = pytz.utc.localize(
            datetime.datetime(then.year, then.month,
                              min(self.now.day, ndays),
                              self.now.hour, self.now.minute))
        return self.aggregate(month_start, month_end)


def slicer(billreader):
    ss = SuperSlice()
    ss.load(billreader)
    return ss
