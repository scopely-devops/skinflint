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


import csv
import decimal
import datetime

import botocore.session
import botocore.utils


class Skinflint(object):

    ServiceNameMap = {
        'Amazon Elastic Compute Cloud': 'ec2',
    }

    Epoch = datetime.datetime(1970, 1, 1)

    Costs = {
        'c1.medium': .13,
        'c1.xlarge': .520,
        'c3.2xlarge': .464,
        'c3.large': .105,
        'c3.xlarge': .210,
        'm1.large': .35,
        'm1.medium': .087,
        'm1.small': .044,
        'm1.xlarge': .35,
        'm2.2xlarge': .49,
        'm2.4xlarge': .98,
        'm3.medium': .07,
        't1.micro': .013
    }

    def __init__(self, table_name, region_name='us-east-1'):
        self._table_name = table_name
        self._session = botocore.session.get_session()
        self._ddb = self._session.create_client(
            'dynamodb', region_name=region_name)

    def _total_seconds(self, delta):
        # python2.6 does not have timedelta.total_seconds() so we have
        # to calculate this ourselves.  This is straight from the
        # datetime docs.
        return ((delta.microseconds + (delta.seconds + delta.days * 24 * 3600)
                 * 10 ** 6) / 10 ** 6)

    def _convert_item(self, item):
        new_item = {}
        for key in item:
            value = item[key]
            if 'S' in value:
                new_item[key] = value['S']
            elif 'N' in value:
                new_item[key] = decimal.Decimal(value['N'])
        return new_item

    def _result_generator(self, results):
        for result in results:
            yield self._convert_item(result)

    def store_lineitem(self, data, ddb, table):
        start = botocore.utils.parse_timestamp(data['UsageStartDate'])
        start = self._total_seconds((start - self.Epoch))
        end = botocore.utils.parse_timestamp(data['UsageEndDate'])
        end = self._total_seconds((end - self.Epoch))
        item = {
            'record_id': {'S': data['RecordId']},
            'account': {'S': data['LinkedAccountId']},
            'service': {'S': data['ProductName']},
            'usage_type': {'S': data['UsageType']},
            'cost': {'N': str(data['UnBlendedCost'])},
            'start': {'N': str(start)},
            'end': {'N': str(end)},
        }
        resource = data['ResourceId']
        if resource:
            item['resource'] = resource
        self._ddb.put_item(
            TableName=self._table_name, Item=item)
        print(data['RecordId'])

    def get_item(self, record_id):
        key = {
            'record_id': {'S': record_id}
        }
        response = self._ddb.get_item(
            TableName=self._table_name, Key=key)
        return self._convert_item(response['Item'])

    def date_query(self, date):
        start = self._total_seconds((date - self.Epoch))
        kc = {
            'start': {
                'ComparisonOperator': 'EQ',
                'AttributeValueList': [
                    {'N': str(start)}
                ]
            }
        }
        response = self._ddb.query(
            TableName=self._table_name, IndexName='start-end-index',
            KeyConditions=kc)
        return self._result_generator(response['Items'])

    def _create_record(self, headers, line):
        data = {}
        for i in range(0, len(headers)):
            data[headers[i]] = line[i]
        return data

    def _skip(self, reader, last=None):
        n = 0
        if last:
            data = self._create_record(next(reader))
            if data['RecordId'] != last:
                n += 1
                data = self._create_record(next(reader))
        print('skipped %d records' % n)

    def load(self, file, last=None):
        fp = open(file)
        reader = csv.reader(fp)
        headers = next(reader)
        self._skip(reader, last)
        for line in reader:
            data = self._create_record(headers, line)
            data['UnBlendedCost'] = decimal.Decimal(data['UnBlendedCost'])
            self.store_lineitem(data)
        fp.close()

    def load2(self, file, last=None):
        timestamp = (None, None)
        fp = open(file)
        reader = csv.reader(fp)
        headers = next(reader)
        self._skip(reader, last)
        data = self._create_record(headers, next(reader))
        while data:
            timestamp = (data['UsageStartDate'], data['UsageEndDate'])
            slice = {}
            data['ProductName'] = self.ServiceNameMap[data['ProductName']]
            data['UnBlendedCost'] = decimal.Decimal(data['UnBlendedCost'])
            self.store_lineitem(data)
        fp.close()
        
