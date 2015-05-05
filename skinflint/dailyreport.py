import datetime
import calendar
import decimal

import pytz
from xlsxwriter.utility import xl_rowcol_to_cell
import yaml

from skinflint.filemanager import FileManager
from skinflint.slice import SuperSlice
from skinflint.report import Report


Header1 = [
    # Create the 'Compared To' merged row
    {'format': 'topheader',
     'range': ((0, 3), (0, 10)),
     'label': 'Compared To'}
]

Header2 = [
    # Service Column
    {'format': 'header',
     'label': 'Service',
     'width': 12},
    # Daily Spend Column
    {'format': 'header',
     'label': 'Current',
     'width': 12},
    # Day Ago Spend (to be hidden)
    {'label': 'Day Ago Spend',
     'width': 10,
     'hidden': 1},
    # Day Ago Comparisons
    {'format': 'mergedheader',
     'label': 'A Day Ago',
     'range': ((0, 0), (0, 1))},
    # Week Ago Spend (to be hidden)
    {'label': 'Week Ago Spend',
     'width': 10,
     'hidden': 1},
    # Week Ago Comparisons
    {'format': 'mergedheader',
     'label': 'A Week Ago',
     'range': ((0, 0), (0, 1))},
    # Month Ago Spend (to be hidden)
    {'label': 'Month Ago Spend',
     'width': 10,
     'hidden': 1},
    # Month Ago Comparisons
    {'format': 'mergedheader',
     'label': 'A Month Ago',
     'range': ((0, 0), (0, 1))},
]


class DailyReport(Report):

    def create_headers(self, page_name, headers, row, col):
        page = self.get_page(page_name)
        for header in headers:
            if 'format' in header:
                format = self.get_format(header.get('format', None))
            else:
                format = None
            merge_range = header.get('range', None)
            if merge_range:
                page.worksheet.merge_range(
                    row + merge_range[0][0], col + merge_range[0][1],
                    row + merge_range[1][0], col + merge_range[1][1],
                    header.get('label', ''),
                    format)
                col += merge_range[1][1] + 1
            else:
                width = header.get('width', None)
                if width:
                    hidden = header.get('hidden', 0)
                    if hidden:
                        page.worksheet.set_column(
                            col, col, width, None, {'hidden': hidden})
                    else:
                        page.worksheet.set_column(col, col, width)
                page.write(row, col, header['label'], format)
                col += 1

    def _create_formula(self, r1, c1, r2, c2, operation):
        c1 = xl_rowcol_to_cell(r1, c1)
        c2 = xl_rowcol_to_cell(r2, c2)
        return '={}{}{}'.format(c1, operation, c2)

    thresholds = ((1, 500), (.005, .2))

    def _create_conditional_formatting(self, fmt_type, page, row, col):
        pos_big_format = self.get_format('{}_pos_big'.format(fmt_type))
        pos_small_format = self.get_format('{}_pos_small'.format(fmt_type))
        neg_big_format = self.get_format('{}_neg_big'.format(fmt_type))
        neg_small_format = self.get_format('{}_neg_small'.format(fmt_type))
        if fmt_type == 'money':
            thresh_low, thresh_high = self.thresholds[0]
        else:
            thresh_low, thresh_high = self.thresholds[1]
        page.worksheet.conditional_format(
            row, col, row, col, {'type': 'cell', 'criteria': 'between',
                                 'minimum': thresh_low, 'maximum': thresh_high,
                                 'format': pos_small_format})
        page.worksheet.conditional_format(
            row, col, row, col, {'type': 'cell', 'criteria': '>=',
                                 'value': thresh_high,
                                 'format': pos_big_format})
        page.worksheet.conditional_format(
            row, col, row, col, {'type': 'cell', 'criteria': 'between',
                                 'minimum': -thresh_high,
                                 'maximum': thresh_low,
                                 'format': neg_small_format})
        page.worksheet.conditional_format(
            row, col, row, col, {'type': 'cell', 'criteria': '<=',
                                 'value': -thresh_high,
                                 'format': neg_big_format})

    def write_service_data(self, worksheet_name, row, col, service_name, data):
        page = self.get_page(worksheet_name)
        money_format = self.get_format('money')
        percent_format = self.get_format('percent')
        daily_spend = data[0]
        page.write(row, col, service_name)
        col += 1
        page.write(row, col, daily_spend, money_format)
        daily_spend_col = col
        col += 1
        for i in range(1, 4):
            page.write(row, col, data[i], money_format)
            col += 1
            if data[i] == 0:
                page.write(row, col, 'N/A')
            else:
                formula = self._create_formula(
                    row, daily_spend_col, row, col - 1, '-')
                page.write(row, col, formula, money_format)
                self._create_conditional_formatting(
                    'money', page, row, col)
            col += 1
            if data[i] == 0:
                page.write(row, col, 'N/A')
            else:
                formula = self._create_formula(
                    row, col - 1, row, col - 2, '/')
                page.write(row, col, formula, percent_format)
                self._create_conditional_formatting(
                    'percent', page, row, col)
            col += 1

    def add_chart(self, name, row, col, nrows):
        chart = self._workbook.add_chart({'type': 'bar', 'subtype': 'stacked'})
        chart.show_hidden_data()
        cell1 = '{}!{}'.format(name, xl_rowcol_to_cell(
            row, col + 1, row_abs=True, col_abs=True))
        cell2 = '{}'.format(xl_rowcol_to_cell(
            row, col + 2, row_abs=True, col_abs=True))
        range1 = '{}:{}'.format(cell1, cell2)
        cell3 = '{}!{}'.format(name, xl_rowcol_to_cell(
            row, col + 5, row_abs=True, col_abs=True))
        cell4 = '{}!{}'.format(name, xl_rowcol_to_cell(
            row, col + 8, row_abs=True, col_abs=True))
        categories = '=({},{},{})'.format(range1, cell3, cell4)
        for r in range(row, row + nrows + 1):
            names = '={}!{}'.format(
                name, xl_rowcol_to_cell(r + 1, col,
                                        row_abs=True, col_abs=True))
            cell1 = '{}!{}'.format(
                name, xl_rowcol_to_cell(r + 1, col + 1,
                                        row_abs=True, col_abs=True))
            cell2 = '{}'.format(
                xl_rowcol_to_cell(r + 1, col + 2,
                                  row_abs=True, col_abs=True))
            range1 = '{}:{}'.format(cell1, cell2)
            cell3 = '{}!{}'.format(
                name, xl_rowcol_to_cell(r + 1, col + 5,
                                        row_abs=True, col_abs=True))
            cell4 = '{}!{}'.format(
                name, xl_rowcol_to_cell(r + 1, col + 8,
                                        row_abs=True, col_abs=True))
            values = '=({},{},{})'.format(range1, cell3, cell4)
            series = {
                'values': values,
                'categories': categories,
                'name': names}
            chart.add_series(series)
        page = self.get_page(name)
        page.worksheet.insert_chart(r + 4, col, chart)

    def write_monthly_totals(self, account, row, col):
        page = self.get_page(account.name)
        money_format = self.get_format('money')
        header_format = self.get_format('header')
        this_month = sum([v for v in account.usage['this_month'].values()])
        last_month = sum([v for v in account.usage['last_month'].values()])
        last_month_to_date = sum([v for v in account.usage['last_month_to_date'].values()])
        now = pytz.utc.localize(datetime.datetime.utcnow())
        beginning = pytz.utc.localize(
            datetime.datetime(now.year, now.month, 1))
        _, ndays = calendar.monthrange(now.year, now.month)
        total_seconds = decimal.Decimal(ndays * 24 * 60 * 60)
        seconds_so_far = decimal.Decimal((now - beginning).total_seconds())
        estimate = (this_month / seconds_so_far) * total_seconds
        page.worksheet.set_column(col, col, 24)
        page.write(row, col, 'Month So Far', header_format)
        page.write(row, col + 1, this_month, money_format)
        row += 1
        page.write(row, col, 'Last Month To Date', header_format)
        page.write(row, col + 1, last_month_to_date, money_format)
        row += 1
        page.write(row, col, 'Estimated Full Month', header_format)
        page.write(row, col + 1, estimate, money_format)
        row += 1
        page.write(row, col, 'Last Month', header_format)
        page.write(row, col + 1, last_month, money_format)


class Account(object):

    def __init__(self, account_id, name=None):
        self.id = account_id
        self.name = name or account_id
        self.usage = {}
        self.one_time = {}

    def add(self, label, service, charge_type, value):
        if charge_type == 'usage':
            if label not in self.usage:
                self.usage[label] = {}
            if service not in self.usage[label]:
                self.usage[label][service] = 0
            self.usage[label][service] += value
        elif charge_type == 'one-time':
            if label not in self.one_time:
                self.one_time[label] = {}
            if service not in self.one_time[label]:
                self.one_time[label][service] = 0
            self.one_time[label][service] += value

    def sort_label(self, label):
        if label not in self.usage:
            return []
        costs = [(k, v) for k, v in self.usage[label].items()]
        return sorted(costs, key=lambda t: t[1], reverse=True)


class AccountCollection(object):

    def __init__(self, superslice, account_map=None):
        self.superslice = superslice
        self.account_map = account_map or {}
        self.data = {}
        self.data['latest'] = self.superslice.latest()
        self.data['one_day_ago'] = self.superslice.one_day_ago()
        self.data['one_week_ago'] = self.superslice.one_week_ago()
        self.data['one_month_ago'] = self.superslice.one_month_ago()
        self.data['this_month'] = self.superslice.this_month()
        self.data['last_month'] = self.superslice.last_month()
        self.data['last_month_to_date'] = self.superslice.last_month_to_date()
        self.totals = {}
        self._create_accounts()

    def _create_accounts(self):
        self.totals['AllAccounts'] = Account('AllAccounts')
        for time_frame in self.data:
            metric = self.data[time_frame].metrics[0]
            for data_key in metric.data:
                account_id, service, charge_type = data_key.split('|')
                if account_id not in self.totals:
                    if account_id in self.account_map:
                        account_name = self.account_map[account_id]['name']
                    else:
                        account_name = account_id
                    self.totals[account_id] = Account(
                        account_id, account_name)
                self.totals[account_id].add(
                    time_frame, service, charge_type, metric.data[data_key])
                self.totals['AllAccounts'].add(
                    time_frame, service, charge_type, metric.data[data_key])


def create_report(config_path, accounts, year, month):
    fp = open(config_path)
    config = yaml.load(fp)
    fp.close()
    fm = FileManager(config)
    ss = SuperSlice()
    for account in accounts:
        dbr = fm.get_detailed_billing_report_reader(account, year, month)
        ss.load(dbr)
        dbr = fm.get_detailed_billing_report_reader(account, year, month - 1)
        ss.load(dbr)
    account_collection = AccountCollection(ss, config['accounts'])
    report = DailyReport(config)
    # Write summary worksheet
    report.create_page('Summary')
    report.create_headers('Summary', Header1, 1, 2)
    report.create_headers('Summary', Header2, 2, 2)
    account_totals = {}
    for label in ['latest', 'one_day_ago', 'one_week_ago', 'one_month_ago']:
        account_totals[label] = {}
        slice = account_collection.data[label]
        metric = slice.metrics[0]
        accounts = metric.dimensions()['account']
        for account in accounts:
            account_costs = metric.query(account=account)
            total = sum([v for v in account_costs.values()])
            account_totals[label][account] = total
    latest_costs = [(k, v) for k, v in account_totals['latest'].items()]
    latest_costs.sort(key=lambda t: t[1], reverse=True)
    account_order = [t[0] for t in latest_costs]
    row = 3
    col = 2
    for account_id in account_order:
        latest_cost = account_totals['latest'][account_id]
        data = [latest_cost]
        datum = account_totals['one_day_ago'].get(account_id, 0)
        data.append(datum)
        datum = account_totals['one_week_ago'].get(account_id, 0)
        data.append(datum)
        datum = account_totals['one_month_ago'].get(account_id, 0)
        data.append(datum)
        if account_id in config['accounts']:
            account_name = config['accounts'][account_id]['name']
        else:
            account_name = account_id
        report.write_service_data(
            'Summary', row, col, account_name, data)
        row += 1
    # Now write worksheets for each account
    all_accounts = config['accounts'].keys() + ['AllAccounts']
    for account_id in account_collection.totals:
        account = account_collection.totals[account_id]
        account_latest = account.sort_label('latest')
        total_cost = sum([c[1] for c in account_latest])
        if total_cost < 30 or account.id not in all_accounts:
            continue
        if 'one_day_ago' not in account.usage:
            continue
        if 'one_week_ago' not in account.usage:
            continue
        if 'one_month_ago' not in account.usage:
            continue
        report.create_page(account.name)
        report.create_headers(account.name, Header1, 1, 2)
        report.create_headers(account.name, Header2, 2, 2)
        row = 3
        col = 2
        i = 0
        for service, amount in account_latest:
            if amount < 15:
                break
            data = [amount]
            datum = account.usage['one_day_ago'].get(service, 0)
            data.append(datum)
            datum = account.usage['one_week_ago'].get(service, 0)
            data.append(datum)
            datum = account.usage['one_month_ago'].get(service, 0)
            data.append(datum)
            report.write_service_data(
                account.name, row, col, service, data)
            row += 1
            i += 1
        other_data = [0, 0, 0, 0]
        for service, amount in account_latest[i:]:
            other_data[0] += amount
            other_data[1] += account.usage['one_day_ago'].get(service, 0)
            other_data[2] += account.usage['one_week_ago'].get(service, 0)
            other_data[3] += account.usage['one_month_ago'].get(service, 0)
        report.write_service_data(
            account.name, row, col, 'Other', other_data)
        report.add_chart(account.name, 2, 2, i)
        report.write_monthly_totals(account, 1, 14)
    report.close()
