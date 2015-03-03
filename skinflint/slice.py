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

from skinflint.metric import TotalUsage, InstanceCost, DataTransfer


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

    def merge(self, other):
        for metric, other_metric in zip(self.metrics, other.metrics):
            metric.merge(other_metric)

    def add_lineitem(self, lineitem):
        if self._retain_lineitems:
            self._lineitems.append(lineitem)
        for metric in self.metrics:
            metric.add(lineitem)

    @property
    def metric_names(self):
        return self.metrics.keys()


class SuperSlice(object):

    def __init__(self):
        self.slices = {}
        self.non_lineitems = []
        self.onetime_charges = []

    def add(self, slice_):
        if not slice_.start and not slice_.end:
            self.non_lineitems.append(slice_)
        else:
            slice_key = '%s-%s' % (slice_.start, slice_.end)
            if slice_key not in self.slices:
                self.slices[slice_key] = slice_
            else:
                self.slices[slice_key] + slice_

    def load(self, billreader):
        slice_ = None
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
                if slice_:
                    self.add(slice_)
                start = usage_start
                end = usage_end
                slice_ = Slice(start, end)
            slice_.add_lineitem(lineitem)
        if slice_:
            self.add(slice_)

    def metrics(self):
        metrics = []
        if self.slices:
            metrics = self.slices[0].metrics
        return metrics

    def aggregate(self, start, end):
        aggregate_slice = Slice(start, end)
        for slice_key in self.slices:
            slice_ = self.slices[slice_key]
            if slice_.start >= start and slice_.end <= end:
                aggregate_slice + slice_
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
