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
import pytz

from botocore.utils import parse_to_aware_datetime

from skinflint.metric import TotalMetric


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
        self.metrics = [TotalMetric()]

    def __add__(self, other):
        for metric, other_metric in zip(self.metrics, other.metrics):
            metric += other_metric

    def add_lineitem(self, lineitem):
        if self._retain_lineitems:
            self._lineitems.append(lineitem)
        for metric in self.metrics:
            metric.add(lineitem)

    @property
    def metric_names(self):
        return self.metrics.keys()


class SuperSlice(object):

    SkipTypes = ['InvoiceTotal', 'StatementTotal', 'Rounding']

    def __init__(self):
        self.start = None
        self.end = None
        self.slices = []
        self.non_lineitems = []
        self.onetime_charges = []

    def add(self, slice):
        if not slice.start and not slice.end:
            self.non_lineitems.append(slice)
        else:
            if self.start is None:
                self.start = slice.start
            elif self.start > slice.start:
                self.start = slice.start
            if self.end is None:
                self.end = slice.end
            elif self.end < slice.end:
                self.end = slice.end
            self.slices.append(slice)

    def load(self, billreader):
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
            if usage_start != start or usage_end != end:
                start = usage_start
                end = usage_end
                slice = Slice(start, end)
                self.add(slice)
            slice.add_lineitem(lineitem)

    def metrics(self):
        metrics = []
        if self.slices:
            metrics = self.slices[0].metrics
        return metrics

    def aggregate(self, start, end):
        aggregate_slice = Slice(start, end)
        print(aggregate_slice)
        for slice in self.slices:
            if slice.start >= start and slice.end <= end:
                aggregate_slice + slice
        return aggregate_slice

    def _slice_a_day(self, days_ago):
        now = pytz.utc.localize(datetime.datetime.utcnow())
        now = now - days_ago
        start = datetime.datetime(now.year, now.month, now.day)
        start = pytz.utc.localize(start)
        end = start + datetime.timedelta(hours=23, minutes=59)
        return self.aggregate(start, end)

    def latest(self):
        one_day = datetime.timedelta(hours=24)
        return self._slice_a_day(one_day)

    def one_day_ago(self):
        two_days = datetime.timedelta(hours=24*2)
        return self._slice_a_day(two_days)

    def one_week_ago(self):
        one_week = datetime.timedelta(hours=24*8)
        return self._slice_a_day(one_week)

    def one_month_ago(self):
        one_month = datetime.timedelta(hours=24*29)
        return self._slice_a_day(one_month)


def slicer(billreader):
    ss = SuperSlice()
    ss.load(billreader)
    return ss
