# Copyright (c) 2014 Scopely, Inc.
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
import unittest
import os
import datetime
import pytz
import decimal

from skinflint.billreader import DetailedBillReportReader
from skinflint.slice import slicer


def get_billing_filepath(name):
    return os.path.join(os.path.dirname(__file__), 'data', name)


class TestMetrics(unittest.TestCase):

    def setUp(self):
        dbr = DetailedBillReportReader(get_billing_filepath('test.csv'))
        self.sc = slicer(dbr)
        self.slice0_key = '2015-03-01 00:00:00+00:00-2015-03-01 01:00:00+00:00'
        self.slice1_key = '2015-03-01 01:00:00+00:00-2015-03-01 02:00:00+00:00'
        self.slice2_key = '2015-03-01 19:00:00+00:00-2015-03-01 20:00:00+00:00'
        self.start = datetime.datetime(2015, 3, 1, 0, 0)
        self.start = pytz.utc.localize(self.start)
        self.end = datetime.datetime(2015, 3, 1, 1, 0)
        self.end = pytz.utc.localize(self.end)

    def tearDown(self):
        pass

    def test_slicer(self):
        self.assertEqual(len(self.sc.slices), 3)
        self.assertIn(self.slice0_key, self.sc.slices)
        self.assertIn(self.slice1_key, self.sc.slices)
        self.assertIn(self.slice2_key, self.sc.slices)

    def test_first_slice(self):
        slice = self.sc.slices[self.slice0_key]
        self.assertEqual(len(slice.metrics), 3)
        self.assertEqual(str(slice.metrics[0]), 'TotalUsage')
        self.assertEqual(str(slice.metrics[1]), 'InstanceCost')
        self.assertEqual(str(slice.metrics[2]), 'DataTransfer')
        self.assertEqual(len(slice.metrics[0].data), 7)
        self.assertEqual(len(slice.metrics[1].data), 3)
        self.assertEqual(len(slice.metrics[2].data), 2)
        print(slice.metrics[0].data)
        self.assertEqual(
            slice.metrics[0].data['012345678901|EC2|usage'],
            decimal.Decimal('0.13200000'))
        self.assertEqual(
            slice.metrics[0].data['234567890123|EC2|usage'],
            decimal.Decimal('0.28500000'))
        self.assertEqual(
            slice.metrics[1].data['234567890123|EC2|m1.small'],
            decimal.Decimal('0.07500000'))
        self.assertEqual(
            slice.metrics[2].data['012345678901|SimpleDB|In'],
            decimal.Decimal('0E-8'))

    def test_second_slice(self):
        slice = self.sc.slices[self.slice1_key]
        self.assertEqual(len(slice.metrics), 3)
        self.assertEqual(str(slice.metrics[0]), 'TotalUsage')
        self.assertEqual(str(slice.metrics[1]), 'InstanceCost')
        self.assertEqual(str(slice.metrics[2]), 'DataTransfer')
        self.assertEqual(len(slice.metrics[0].data), 1)
        self.assertEqual(len(slice.metrics[1].data), 0)
        self.assertEqual(len(slice.metrics[2].data), 0)
        self.assertEqual(
            slice.metrics[0].data['012345678901|SQS|usage'],
            decimal.Decimal('0E-8'))

    def test_third_slice(self):
        slice = self.sc.slices[self.slice2_key]
        self.assertEqual(len(slice.metrics), 3)
        self.assertEqual(str(slice.metrics[0]), 'TotalUsage')
        self.assertEqual(str(slice.metrics[1]), 'InstanceCost')
        self.assertEqual(str(slice.metrics[2]), 'DataTransfer')
        self.assertEqual(len(slice.metrics[0].data), 1)
        self.assertEqual(len(slice.metrics[1].data), 2)
        self.assertEqual(len(slice.metrics[2].data), 0)
        self.assertEqual(
            slice.metrics[0].data['012345678901|EC2|usage'],
            decimal.Decimal('0.48200000'))
        self.assertEqual(
            slice.metrics[1].data['012345678901|EC2|m1.large'],
            decimal.Decimal('0.35000000'))

    def test_aggregate(self):
        start = datetime.datetime(2015, 3, 1)
        start = pytz.utc.localize(start)
        end = datetime.datetime(2015, 3, 2)
        end = pytz.utc.localize(end)
        slice = self.sc.aggregate(start, end)
        self.assertEqual(slice.start, start)
        self.assertEqual(slice.end, end)
        self.assertEqual(len(slice.metrics), 3)
        self.assertEqual(len(slice.metrics[0].data), 7)
        self.assertEqual(len(slice.metrics[1].data), 4)
        self.assertEqual(len(slice.metrics[2].data), 2)

    def test_query(self):
        slice = self.sc.slices[self.slice0_key]
        usage_metric = slice.metrics[0]
        self.assertEqual(str(usage_metric), 'TotalUsage')
        result = usage_metric.query(account='234567890123')
        self.assertEqual(len(result), 3)
        self.assertEqual(result['234567890123|DynamoDB|usage'],
                         decimal.Decimal('1.89673919'))
        result = usage_metric.query(account='234.*')
        self.assertEqual(len(result), 3)
        self.assertEqual(result['234567890123|DynamoDB|usage'],
                         decimal.Decimal('1.89673919'))
        result = usage_metric.query(service='EC2')
        self.assertEqual(len(result), 2)
        self.assertEqual(result['012345678901|EC2|usage'],
                         decimal.Decimal('0.13200000'))
        self.assertEqual(result['234567890123|EC2|usage'],
                         decimal.Decimal('0.28500000'))
        result = usage_metric.query(service='S.*')
        self.assertEqual(len(result), 4)
        self.assertEqual(result['234567890123|SQS|usage'],
                         decimal.Decimal('0.48793206'))

        
