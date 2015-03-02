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


class Metric(object):

    Dimensions = {}

    def __init__(self):
        self.data = {}
        for dim in self.Dimensions:
            self.data[dim] = {}

    def __repr__(self):
        return self.__class__.__name__

    def __add__(self, other):
        for dimension in self.data:
            all_subdims = set(self.data[dimension].keys())
            all_subdims.update(other.data[dimension].keys())
            for subdim in all_subdims:
                if subdim not in self.data[dimension]:
                    self.data[dimension][subdim] = decimal.Decimal('0.0')
                other_value = other.data[dimension].get(
                    subdim, decimal.Decimal('0.0'))
                self.data[dimension][subdim] += other_value

    def add(self, data):
        for dimension in self.Dimensions:
            dimension_key = self.Dimensions[dimension](data)
            if dimension_key not in self.data[dimension]:
                self.data[dimension][dimension_key] = decimal.Decimal('0.0')
            self.data[dimension][dimension_key] += data['UnBlendedCost']

    def dimensions(self):
        return self.data.keys()

    def dump(self):
        for dimension in self.data:
            print('Dimension: %s' % dimension)
            value = self.data[dimension]
            for key in value:
                print('\t%s = %s' % (key, value[key]))


def usage_or_onetime(d):
    if d['ReservedInstance'] == 'Y' and not d['SubscriptionId']:
        return 'onetime'
    else:
        return 'usage'

ServiceMap = {
    'AWS Data Pipeline': 'datapipeline',
    'Amazon DynamoDB': 'dynamodb',
    'Amazon ElastiCache': 'elasticache',
    'Amazon Elastic Compute Cloud': 'ec2',
    'Amazon Elastic MapReduce': 'emr',
    'Amazon Kinesis': 'kinesis',
    'Amazon RDS Service': 'rds',
    'Amazon Redshift': 'redshift',
    'Amazon Route 53': 'route53',
    'Amazon Simple Notification Service': 'sns',
    'Amazon Simple Queue Service': 'sqs',
    'Amazon Simple Storage Service': 's3',
    'Amazon SimpleDB': 'simpledb',
    'AWS Key Management Service': 'kms',
}


def account_service(d):
    product_name = d['ProductName']
    product_name = ServiceMap.get(product_name, product_name)
    dimension = '%s:%s' % (d['LinkedAccountId'], product_name)
    return dimension


class TotalUsage(Metric):

    Dimensions = {
        'account.service': account_service,
        'total': usage_or_onetime,
    }


def instance_type(d):
    if ':' in d['UsageType']:
        _, instance_type = d['UsageType'].split(':')
    else:
        instance_type = 'none'
    return instance_type


class InstanceCost(Metric):

    Dimensions = {
        'account': lambda d: d['LinkedAccountId'],
        'availability_zone': lambda d: d['AvailabilityZone'],
        'instance_type': instance_type,
    }


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
