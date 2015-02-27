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

import decimal
import datetime

import botocore.utils


Epoch = datetime.datetime(1970, 1, 1)


def total_seconds(delta):
    # python2.6 does not have timedelta.total_seconds() so we have
    # to calculate this ourselves.  This is straight from the
    # datetime docs.
    return ((delta.microseconds + (delta.seconds + delta.days * 24 * 3600)
             * 10 ** 6) / 10 ** 6)


class TotalMetric(object):

    Dimensions = {
        'account': 'LinkedAccountId',
        'service': 'ProductName'}

    def __init__(self):
        self.name = 'Total Usage'
        self._totals = {
            'usage': decimal.Decimal('0.0'),
            'onetime': decimal.Decimal('0.0'),
        }
        for dim in self.Dimensions:
            self._totals[dim] = {}

    def __repr__(self):
        return self.name

    def __add__(self, other):
        for dimension in self._totals:
            if isinstance(self._totals[dimension], dict):
                all_subdims = set(self._totals[dimension].keys())
                all_subdims.update(other._totals[dimension].keys())
                for subdim in all_subdims:
                    if subdim not in self._totals[dimension]:
                        self._totals[dimension][subdim] = decimal.Decimal('0.0')
                    self._totals[dimension][subdim] += other._totals[dimension].get(subdim, decimal.Decimal('0.0'))
            else:
                self._totals[dimension] += other._totals.get(dimension, decimal.Decimal('0.0'))

    @property
    def totals(self):
        return self._totals

    def add(self, data):
        for dim_name in self.Dimensions:
            key = self.Dimensions[dim_name]
            value = data[key]
            if value not in self._totals[dim_name]:
                self._totals[dim_name][value] = decimal.Decimal('0.0')
            self._totals[dim_name][value] += data['UnBlendedCost']
        if data['ReservedInstance'] == 'Y' and not data['SubscriptionId']:
            self._totals['onetime'] += data['UnBlendedCost']
        else:
            self._totals['usage'] += data['UnBlendedCost']

    def dimensions(self):
        return self._totals.keys()

    def dump(self):
        for dimension in self._totals:
            print('Dimension: %s' % dimension)
            value = self._totals[dimension]
            if isinstance(value, dict):
                for key in value:
                    print('\t%s = %s' % (key, value[key]))
            else:
                print('\t%s = %s' % (dimension, value))


#
# The following metrics need to be converted to the newer style metric
# as shown above.
#
class InstanceCostMetric(object):

    def __init__(self):
        self.name = 'InstanceCost'
        self._instance_types = {}
        self._accounts = {}
        self._regions = {}
        self._total = decimal.Decimal('0.0')

    def add(self, data):
        if data['UsageType'].startswith('BoxUsage'):
            if ':' in data['UsageType']:
                _, instance_type = data['UsageType'].split(':')
            else:
                instance_type = 'none'
            if instance_type not in self._instance_types:
                self._instance_types[instance_type] = decimal.Decimal('0.0')
            self._instance_types[instance_type] += data['UnBlendedCost']
            account = data['LinkedAccountId']
            if account not in self._accounts:
                self._accounts[account] = decimal.Decimal('0.0')
            self._accounts[account] += data['UnBlendedCost']
            self._total += data['UnBlendedCost']

    def dimensions(self):
        for key in self._accounts:
            value = self._accounts[key]
            print('Account:%s = %s' % (key, value))
        for key in self._instance_types:
            value = self._instance_types[key]
            print('InstanceType:%s = %s' % (key, value))


class DataTransferMetric(object):

    def __init__(self):
        self.name = 'DataTranser'
        self._transfer_types = {}
        self._accounts = {}
        self._total = decimal.Decimal('0.0')

    def add(self, data):
        if data['UsageType'].startswith('DataTransfer'):
            _, transfer_type, _ = data['UsageType'].split('-')
            if not transfer_type:
                transfer_type = 'none'
            if transfer_type not in self._transfer_types:
                self._transfer_types[transfer_type] = decimal.Decimal('0.0')
            self._transfer_types[transfer_type] += data['UnBlendedCost']
            account = data['LinkedAccountId']
            if account not in self._accounts:
                self._accounts[account] = decimal.Decimal('0.0')
            self._accounts[account] += data['UnBlendedCost']
            self._total += data['UnBlendedCost']

    def dimensions(self):
        for key in self._accounts:
            value = self._accounts[key]
            print('Account:%s = %s' % (key, value))
        for key in self._transfer_types:
            value = self._transfer_types[key]
            print('TransferType:%s = %s' % (key, value))
