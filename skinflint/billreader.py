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


class DetailedBillingReader(object):

    def __init__(self, filepath):
        self.filepath = filepath
        self._fp = open(filepath)
        self._reader = csv.reader(self._fp)
        self.headers = next(self._reader)

    def next(self):
        line = next(self._reader)
        data = {}
        for i in range(0, len(self.headers)):
            data[self.headers[i]] = line[i]
        data['UnBlendedCost'] = decimal.Decimal(data['UnBlendedCost'])
        return data

    def __iter__(self):
        return self
