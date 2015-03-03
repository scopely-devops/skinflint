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
import re

Epoch = datetime.datetime(1970, 1, 1)

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
    'AmazonCloudWatch': 'cloudwatch',
    'Amazon CloudFront': 'cloudfront',
    'Amazon Simple Email Service': 'ses',
    'AWS Lambda': 'lambda',
    'Amazon Virtual Private Cloud': 'vpc',
    'Amazon CloudSearch': 'cloudsearch'
}


def total_seconds(delta):
    # python2.6 does not have timedelta.total_seconds() so we have
    # to calculate this ourselves.  This is straight from the
    # datetime docs.
    return ((delta.microseconds + (delta.seconds + delta.days * 24 * 3600)
             * 10 ** 6) / 10 ** 6)


class Metric(object):

    Dimensions = ''

    def __init__(self):
        self.data = {}

    def __repr__(self):
        return self.__class__.__name__

    def __add__(self, other):
        all_subdims = set(self.data.keys())
        all_subdims.update(other.data.keys())
        for subdim in all_subdims:
            if subdim not in self.data:
                self.data[subdim] = decimal.Decimal('0.0')
            other_value = other.data.get(subdim, decimal.Decimal('0.0'))
            self.data[subdim] += other_value

    def keyfn(self, data):
        pass

    def add(self, data):
        dimension_key = self.keyfn(data)
        if dimension_key is not None:
            if dimension_key not in self.data:
                self.data[dimension_key] = decimal.Decimal('0.0')
            self.data[dimension_key] += data['UnBlendedCost']

    def query(self, **kwargs):
        dimensions = self.Dimensions.split('|')
        regexs = []
        for dimension in dimensions:
            if dimension in kwargs:
                regexs.append(kwargs[dimension])
            else:
                regexs.append('.*')
        regex = '\|'.join(regexs)
        regex = re.compile(regex)
        filtered_keys = [k for k in self.data.keys() if regex.match(k)]
        return {k: self.data[k] for k in filtered_keys}


class TotalUsage(Metric):

    Dimensions = 'account|service'

    def keyfn(self, data):
        product_name = data['ProductName']
        product_name = ServiceMap.get(product_name, product_name)
        key = '%s|%s' % (data['LinkedAccountId'], product_name)
        return key


class InstanceCost(Metric):

    Dimensions = 'account|service|instance_type'

    def keyfn(self, data):
        key = None
        usage_type = data['UsageType']
        if usage_type.startswith('BoxUsage'):
            product_name = data['ProductName']
            if ':' in usage_type:
                _, instance_type = usage_type.split(':')
            else:
                instance_type = 'm1.small'
            key = '%s|%s|%s' % (
                data['LinkedAccountId'],
                ServiceMap.get(product_name, product_name),
                instance_type)
        return key


class DataTransfer(Metric):

    Dimensions = 'account|service|transfer_type'

    def keyfn(self, data):
        key = None
        if data['UsageType'].startswith('DataTransfer'):
            product_name = data['ProductName']
            _, transfer_type, _ = data['UsageType'].split('-')
            key = '%s|%s|%s' % (
                data['LinkedAccountId'],
                ServiceMap.get(product_name, product_name),
                transfer_type)
        return key
