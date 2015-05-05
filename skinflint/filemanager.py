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

import os
import datetime
import zipfile
import logging

import pytz
import dateutil.tz
import boto

from skinflint.billreader import *

LOG = logging.getLogger(__name__)


class FileManager(object):

    def __init__(self, config):
        self.config = config
        self.cache_dir = self.config['cache_dir']
        self.cache_dir = os.path.expanduser(self.cache_dir)
        self.cache_dir = os.path.expandvars(self.cache_dir)
        if not os.path.isdir(self.cache_dir):
            os.mkdir(self.cache_dir)

    def _get_file_modified_time(self, file_path):
        stats = os.stat(file_path)
        return datetime.datetime.fromtimestamp(
            stats.st_atime, dateutil.tz.tzlocal())

    def _get_key_modified_time(self, key):
        ts = boto.utils.parse_ts(key.last_modified)
        return pytz.utc.localize(ts)

    def _download_and_unzip(self, key, file_name):
        LOG.debug('downloading %s', key.name)
        key_path = os.path.join(self.cache_dir, key.name)
        key.get_contents_to_filename(key_path)
        if key.name.endswith('.zip'):
            zf = zipfile.ZipFile(key_path)
            namelist = zf.namelist()
            dbf = namelist[0]
            LOG.debug('unzipping downloaded file')
            zf.extract(dbf, self.cache_dir)
            zf.close()
            LOG.debug('deleting zip file')
            os.unlink(key_path)

    def _check_key(self, key, file_name):
        if not os.path.isfile(file_name):
            LOG.debug('%s not in cache, downloading now', file_name)
            self._download_and_unzip(key, file_name)
            file_mod_time = self._get_file_modified_time(file_name)
        else:
            file_mod_time = self._get_file_modified_time(file_name)
            LOG.debug('file_mod_time: %s', file_mod_time)
            key_mod_time = self._get_key_modified_time(key)
            LOG.debug('key_mod_time: %s', key_mod_time)
            if key_mod_time > file_mod_time:
                LOG.debug('cached copy of %s out of date', file_name)
                self._download_and_unzip(key, file_name)

    def _get_bill_reader(self, billreader_cls, account_id, year, month):
        account_cfg = self.config['accounts'][account_id]
        s3 = boto.connect_s3(profile_name=account_cfg['profile'])
        bucket = s3.lookup(account_cfg['bucket'])
        key_name = billreader_cls.KeyName.format(
            id=account_id, year=year, month=month)
        key = bucket.lookup(key_name)
        if key is None:
            msg = 'Bucket (%s) does not contain Key (%s)' % (bucket, key_name)
            raise ValueError(msg)
        if key_name.endswith('.zip'):
            file_name = key_name[0:-4]
        else:
            file_name = key_name
        file_name = os.path.join(self.cache_dir, file_name)
        self._check_key(key, file_name)
        return billreader_cls(file_name)

    def get_detailed_billing_report_reader(self, account_id, year, month):
        return self._get_bill_reader(
            DetailedBillReportReader, account_id, year, month)

    def get_monthly_report_reader(self, account_id, year, month):
        return self._get_bill_reader(
            MonthlyReportReader, account_id, year, month)

    def get_monthly_allocation_report_reader(self, account_id, year, month):
        return self._get_bill_reader(
            MonthlyCostAllocationReportReader, account_id, year, month)
