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


class ReportReader(object):

    KeyName = ''

    def __init__(self, filepath):
        self.filepath = filepath
        self._fp = open(filepath)
        self._reader = csv.reader(self._fp)
        self.headers = []
        while len(self.headers) <= 1:
            self.headers = next(self._reader)

    def _computed_data(self, data):
        pass

    def __next__(self):
        line = next(self._reader)
        data = {}
        for i in range(0, len(self.headers)):
            data[self.headers[i]] = line[i]
        self._computed_data(data)
        return data

    next = __next__

    def __iter__(self):
        return self


class DetailedBillReportReader(ReportReader):

    KeyName = ('{id}-aws-billing-detailed-line-items-with-resources-'
               'and-tags-{year}-{month:02d}.csv.zip')

    def _computed_data(self, data):
        data['UnBlendedCost'] = decimal.Decimal(data['UnBlendedCost'])
        data['BlendedCost'] = decimal.Decimal(data['BlendedCost'])


class MonthlyReportReader(ReportReader):

    KeyName = '{id}-aws-billing-csv-{year}-{month:02d}.csv'

    def _computed_data(self, data):
        if data['TotalCost'] == '':
            data['TotalCost'] = '0'
        data['TotalCost'] = decimal.Decimal(data['TotalCost'])


class MonthlyCostAllocationReportReader(ReportReader):

    KeyName = '{id}-aws-cost-allocation-{year}-{month:02d}.csv'

    def _computed_data(self, data):
        if 'TotalCost' not in data or data['TotalCost'] == '':
            data['TotalCost'] = '0'
        data['TotalCost'] = decimal.Decimal(data['TotalCost'])
