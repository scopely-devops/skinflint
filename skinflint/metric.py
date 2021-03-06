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
    'AWS Data Pipeline': 'DataPipeline',
    'Amazon DynamoDB': 'DynamoDB',
    'Amazon ElastiCache': 'ElastiCache',
    'Amazon Elastic Compute Cloud': 'EC2',
    'Amazon Elastic MapReduce': 'EMR',
    'Amazon Kinesis': 'Kinesis',
    'Amazon RDS Service': 'RDS',
    'Amazon Redshift': 'Redshift',
    'Amazon Route 53': 'Route53',
    'Amazon Simple Notification Service': 'SNS',
    'Amazon Simple Queue Service': 'SQS',
    'Amazon Simple Storage Service': 'S3',
    'Amazon SimpleDB': 'SimpleDB',
    'AWS Key Management Service': 'KMS',
    'AmazonCloudWatch': 'CloudWatch',
    'Amazon CloudFront': 'CloudFront',
    'Amazon Simple Email Service': 'SES',
    'AWS Lambda': 'Lambda',
    'Amazon Virtual Private Cloud': 'VPC',
    'Amazon CloudSearch': 'CloudSearch',
    'AWS Config': 'Config'
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
            self.data[dimension_key] += data['BlendedCost']

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

    def dimensions(self):
        dimension_names = self.Dimensions.split('|')
        dimensions = {k: [] for k in dimension_names}
        for k in self.data:
            dimension_values = k.split('|')
            for i in range(0, len(dimension_values)):
                if dimension_values[i] not in dimensions[dimension_names[i]]:
                    dimensions[dimension_names[i]].append(dimension_values[i])
        return dimensions


class TotalUsage(Metric):

    Dimensions = 'account|service|type'

    def keyfn(self, data):
        if not data['UsageType']:
            charge_type = 'one-time'
        else:
            charge_type = 'usage'
        product_name = data['ProductName']
        product_name = ServiceMap.get(product_name, product_name)
        key = '%s|%s|%s' % (data['LinkedAccountId'], product_name, charge_type)
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
