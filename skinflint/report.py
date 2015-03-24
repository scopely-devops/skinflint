from skinflint.filemanager import FileManager
from skinflint.slice import SuperSlice
import xlsxwriter
from xlsxwriter.utility import xl_rowcol_to_cell


Formats = {
    'money': {'num_format': '$#,##0',
              'font_size': 14},
    'percent': {'num_format': '0%',
                'font_size': 14},
    'money_pos_big': {'num_format': '$#,##0',
                      'bg_color': '#FA6B6B',
                      'font_size': 14},
    'money_pos_small': {'num_format': '$#,##0',
                        'bg_color': '#FC8D8D',
                        'font_size': 14},
    'money_neg_big': {'num_format': '$#,##0',
                      'bg_color': '#20C948',
                      'font_size': 14},
    'money_neg_small': {'num_format': '$#,##0',
                        'bg_color': '#87FFA3',
                        'font_size': 14},
    'percent': {'num_format': '0%',
                'font_size': 14},
    'percent_pos_big': {'num_format': '0%',
                        'bg_color': '#FA6B6B',
                        'font_size': 14},
    'percent_pos_small': {'num_format': '0%',
                          'bg_color': '#FC8D8D',
                          'font_size': 14},
    'percent_neg_big': {'num_format': '0%',
                        'bg_color': '#20C948',
                        'font_size': 14},
    'percent_neg_small': {'num_format': 0x09,
                          'bg_color': '#87FFA3',
                          'font_size': 14},
    'bold': {'bold': True,
             'font_size': 14},
    'topheader': {'bg_color': '#DDDDDD',
                  'italic': True,
                  'border': 1, 'align':
                  'center', 'font_size': 14},
    'mergedheader': {'bg_color': '#888888',
                     'font_color': '#FFFFFF',
                     'border': 1,
                     'align': 'center',
                     'bold': True,
                     'font_size': 14},
    'header': {'align': 'center',
               'bold': True,
               'font_size': 14},
}

Header1 = [
    # Create the 'Compared To' merged row
    {'format': 'topheader',
     'range': ((0, 3), (0, 10)),
     'label': 'Compared To'}
]

Header2 = [
    # Service Column
    {'format': 'header',
     'label': 'Service'},
    # Daily Spend Column
    {'format': 'header',
     'label': 'Daily Spend',
     'width': 12},
    # Day Ago Spend (to be hidden)
    {'format': 'header',
     'label': 'Day Ago Spend',
     'width': 10,
     'hidden': 1},
    # Day Ago Comparisons
    {'format': 'mergedheader',
     'label': 'A Day Ago',
     'range': ((0, 0), (0, 1))},
    # Week Ago Spend (to be hidden)
    {'format': 'header',
     'label': 'Week Ago Spend',
     'width': 10,
     'hidden': 1},
    # Week Ago Comparisons
    {'format': 'mergedheader',
     'label': 'A Week Ago',
     'range': ((0, 0), (0, 1))},
    # Month Ago Spend (to be hidden)
    {'format': 'header',
     'label': 'Month Ago Spend',
     'width': 10,
     'hidden': 1},
    # Month Ago Comparisons
    {'format': 'mergedheader',
     'label': 'A Month Ago',
     'range': ((0, 0), (0, 1))},
]

SeriesData = [
    {'categories': '=(prod!$D$3:$E$3,prod!$H$3,prod!$K$3)',
     'values': '=(prod!$D$4:$E$4,prod!$H$4,prod!$K$4)',
     'name': '=prod!$C$4'},
    {'categories': '=(prod!$D$3:$E$3,prod!$H$3,prod!$K$3)',
     'values': '=(prod!$D$5:$E$5,prod!$H$5,prod!$K$5)',
     'name': '=prod!$C$5'},
    {'categories': '=(prod!$D$3:$E$3,prod!$H$3,prod!$K$3)',
     'values': '=(prod!$D$6:$E$6,prod!$H$6,prod!$K$6)',
     'name': '=prod!$C$6'},
    {'categories': '=(prod!$D$3:$E$3,prod!$H$3,prod!$K$3)',
     'values': '=(prod!$D$7:$E$7,prod!$H$7,prod!$K$7)',
     'name': '=prod!$C$7'},
    {'categories': '=(prod!$D$3:$E$3,prod!$H$3,prod!$K$3)',
     'values': '=(prod!$D$8:$E$8,prod!$H$8,prod!$K$8)',
     'name': '=prod!$C$8'},
    {'categories': '=(prod!$D$3:$E$3,prod!$H$3,prod!$K$3)',
     'values': '=(prod!$D$9:$E$9,prod!$H$9,prod!$K$9)',
     'name': '=prod!$C$9'}
]


class Cell(object):

    def __init__(self, row, col):
        self._row = row
        self._col = col

    def __repr__(self):
        return xl_rowcol_to_cell(self._row, self._col)

    @property
    def row(self):
        return self._row

    @property
    def col(self):
        return self._col


class Workbook(object):

    def __init__(self, name, formats):
        self.name = name
        self._file_name = '{}.xlsx'.format(self.name)
        self._workbook = xlsxwriter.Workbook(self._file_name)
        self._formats = {}
        self._worksheets = {}

    def close(self):
        self._workbook.close()

    def get_format(self, name):
        return self._formats[name]

    def get_worksheet(self, name):
        return self._worksheets[name]

    def add_worksheet(self, name):
        self._worksheets[name] = self._workbook.add_worksheet(
            name)

    def add_formats(self, formats):
        for format in formats:
            self._formats[format] = self._workbook.add_format(
                formats[format])

    def create_headers(self, worksheet_name, headers, row, col):
        worksheet = self.get_worksheet(worksheet_name)
        for header in headers:
            print('row={} col={}'.format(row, col))
            print(header)
            format = self.get_format(header['format'])
            merge_range = header.get('range', None)
            if merge_range:
                print('merge_range')
                worksheet.merge_range(
                    row + merge_range[0][0], col + merge_range[0][1],
                    row + merge_range[1][0], col + merge_range[1][1],
                    header.get('label', ''),
                    format)
                col += merge_range[1][1] + 1
            else:
                print('non-merged')
                width = header.get('width', None)
                if width:
                    hidden = header.get('hidden', 0)
                    if hidden:
                        print('hidden')
                        worksheet.set_column(
                            col, col, width, None, {'hidden': hidden})
                    else:
                        print('not hidden')
                        worksheet.set_column(col, col, width)
                worksheet.write(row, col, header['label'])
                col += 1

    def _create_headers(self, worksheet_name):
        worksheet = self.get_worksheet(worksheet_name)
        row = 1
        col = 2
        # Create the 'Compared To' merged row
        format = self.get_format('topheader')
        worksheet.merge_range(
            row, col + 2, row, col + 10, 'Compared To', format)
        row += 1
        # Service Column
        format = self.get_format('header')
        worksheet.write(row, col, 'Service', format)
        # Daily Spend Column
        worksheet.set_column(col + 1, col + 1, 12)
        worksheet.write(row, col + 1, 'Daily Spend', format)
        # Day Ago Spend (to be hidden)
        worksheet.write(row, col + 2, 'Day Ago Spend')
        worksheet.set_column(col + 2, col + 2, 10, None, {'hidden': 1})
        # Day Ago Comparisons
        format = self.get_format('mergedheader')
        worksheet.merge_range(
            row, col + 3, row, col + 4, 'A Day Ago', format)
        # Week Ago Spend (to be hidden)
        worksheet.write(row, col + 5, 'Week Ago Spend')
        worksheet.set_column(col + 5, col + 5, 10, None, {'hidden': 1})
        # Week Ago Comparisons
        worksheet.merge_range(
            row, col + 6, row, col + 7, 'A Week Ago', format)
        # Month Ago Spend (to be hidden)
        worksheet.write(row, col + 8, 'Month Ago Spend')
        worksheet.set_column(col + 8, col + 8, 10, None, {'hidden': 1})
        # Month Ago Comparisons
        worksheet.merge_range(
            row, col + 9, row, col + 10, 'A Month Ago', format)

    def _create_formula(self, r1, c1, r2, c2, operation):
        c1 = xl_rowcol_to_cell(r1, c1)
        c2 = xl_rowcol_to_cell(r2, c2)
        return '={}{}{}'.format(c1, operation, c2)

    thresholds = ((1, 500), (.005, .2))

    def _create_conditional_formatting(self, fmt_type, worksheet, row, col):
        pos_big_format = self.get_format('{}_pos_big'.format(fmt_type))
        pos_small_format = self.get_format('{}_pos_small'.format(fmt_type))
        neg_big_format = self.get_format('{}_neg_big'.format(fmt_type))
        neg_small_format = self.get_format('{}_neg_small'.format(fmt_type))
        if fmt_type == 'money':
            thresh_low, thresh_high = self.thresholds[0]
        else:
            thresh_low, thresh_high = self.thresholds[1]
        worksheet.conditional_format(
            row, col, row, col, {'type': 'cell', 'criteria': 'between',
                                 'minimum': thresh_low, 'maximum': thresh_high,
                                 'format': pos_small_format})
        worksheet.conditional_format(
            row, col, row, col, {'type': 'cell', 'criteria': '>=',
                                 'value': thresh_high,
                                 'format': pos_big_format})
        worksheet.conditional_format(
            row, col, row, col, {'type': 'cell', 'criteria': 'between',
                                 'minimum': -thresh_high,
                                 'maximum': thresh_low,
                                 'format': neg_small_format})
        worksheet.conditional_format(
            row, col, row, col, {'type': 'cell', 'criteria': '<=',
                                 'value': -thresh_high,
                                 'format': neg_big_format})

    def write_service_data(self, worksheet_name, row, col, service_name, data):
        worksheet = self.get_worksheet(worksheet_name)
        money_format = self.get_format('money')
        percent_format = self.get_format('percent')
        daily_spend = data[0]
        worksheet.write(row, col, service_name)
        col += 1
        worksheet.write_number(row, col, daily_spend, money_format)
        daily_spend_col = col
        col += 1
        for i in range(1, 4):
            worksheet.write_number(row, col, data[i], money_format)
            col += 1
            formula = self._create_formula(
                row, daily_spend_col, row, col - 1, '-')
            worksheet.write_formula(row, col, formula, money_format)
            self._create_conditional_formatting(
                'money', worksheet, row, col)
            col += 1
            formula = self._create_formula(
                row, col - 1, row, daily_spend_col, '/')
            worksheet.write_formula(row, col, formula, percent_format)
            self._create_conditional_formatting(
                'percent', worksheet, row, col)
            col += 1

    def add_chart(self, name, series_data, row, col):
        chart = self._workbook.add_chart({'type': 'bar', 'subtype': 'stacked'})
        chart.show_hidden_data()
        for series in series_data:
            chart.add_series(series)
        worksheet = self.get_worksheet(name)
        worksheet.insert_chart(row, col, chart)


def create_workbook(cfg, names, year, month):
    fm = FileManager(cfg)
    ss = SuperSlice()
    for name in names:
        dbr = fm.get_bill_reader(name, year, month)
        ss.load(dbr)
        dbr = fm.get_bill_reader(name, year, month - 1)
        ss.load(dbr)
    latest = ss.latest()
    one_day_ago = ss.one_day_ago()
    one_week_ago = ss.one_week_ago()
    one_month_ago = ss.one_month_ago()
    total_metric = latest.metrics[0]
    costs = [(k, total_metric.data[k]) for k in total_metric.data]
    costs = sorted(costs, key=lambda t: t[1], reverse=True)
    workbook = Workbook('foobar', Formats)
    workbook.add_formats(Formats)
    workbook.add_worksheet(name)
    workbook.create_headers(name, Header1, 1, 2)
    workbook.create_headers(name, Header2, 2, 2)
    row = 3
    col = 2
    i = 0
    for service, amount in costs:
        if amount < 100:
            break
        data = [amount]
        data.append(one_day_ago.metrics[0].data[service])
        data.append(one_week_ago.metrics[0].data[service])
        data.append(one_month_ago.metrics[0].data[service])
        service_name = service.split('|')[-1]
        workbook.write_service_data(
            name, row, col, service_name, data)
        row += 1
        i += 1
    other_data = [0, 0, 0, 0]
    for service, amount in costs[i:]:
        other_data[0] += amount
        other_data[1] += one_day_ago.metrics[0].data.get(service, 0)
        other_data[2] += one_week_ago.metrics[0].data.get(service, 0)
        other_data[3] += one_month_ago.metrics[0].data.get(service, 0)
    workbook.write_service_data(
        name, row, col, 'Other', other_data)
    row += 2
    workbook.add_chart(name, SeriesData, row, col)
    workbook.close()
