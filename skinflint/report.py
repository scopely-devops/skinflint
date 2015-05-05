import xlsxwriter
from xlsxwriter.utility import xl_rowcol_to_cell


class Page(object):

    def __init__(self, name, report, worksheet):
        self.name = name
        self._report = report
        self._worksheet = worksheet

    @property
    def worksheet(self):
        return self._worksheet

    @property
    def report(self):
        return self._report

    def write(self, row, col, value, fmt=None):
        self.worksheet.write(row, col, value, fmt)

    def cell_ref(self, row, col, abs_row=False, abs_col=False, fqn=False):
        cell_ref = xl_rowcol_to_cell(row, col, abs_row, abs_col)
        if fqn:
            cell_ref = "'{}'!{}".format(self.name, cell_ref)
        return cell_ref

    def name_cell(self, row, col, name):
        cell_name = "'{}'!{}".format(
            self.name, xl_rowcol_to_cell(row, col, True, True))
        self._report.workbook.define_name(name, cell_name)

    def create_headers(self, headers, row, col):
        for header in headers:
            if 'format' in header:
                fmt = self._report.get_format(header.get('format', None))
            else:
                fmt = None
            merge_range = header.get('range', None)
            if merge_range:
                self.worksheet.merge_range(
                    row + merge_range[0][0], col + merge_range[0][1],
                    row + merge_range[1][0], col + merge_range[1][1],
                    header.get('label', ''),
                    fmt)
                col += merge_range[1][1] + 1
            else:
                width = header.get('width', None)
                if width:
                    hidden = header.get('hidden', 0)
                    if hidden:
                        self.worksheet.set_column(
                            col, col, width, None, {'hidden': hidden})
                    else:
                        self.worksheet.set_column(col, col, width)
                self.worksheet.write(row, col, header['label'], fmt)
                col += 1


class Report(object):

    def __init__(self, config):
        self.config = config
        self.name = self.config['name']
        self._file_name = '{}.xlsx'.format(self.name)
        self._workbook = xlsxwriter.Workbook(self._file_name)
        self._formats = {}
        self._pages = {}
        self.add_formats(config['formats'])

    @property
    def workbook(self):
        return self._workbook

    def close(self):
        self._workbook.close()

    def get_format(self, name):
        return self._formats[name]

    def get_page(self, name):
        return self._pages[name]

    def create_page(self, name):
        worksheet = self._workbook.add_worksheet(name)
        self._pages[name] = Page(name, self, worksheet)
        return self._pages[name]

    def add_formats(self, formats):
        for fmt in formats:
            self._formats[fmt] = self._workbook.add_format(
                formats[fmt])

    def _create_formula(self, r1, c1, r2, c2, operation):
        c1 = xl_rowcol_to_cell(r1, c1)
        c2 = xl_rowcol_to_cell(r2, c2)
        return '={}{}{}'.format(c1, operation, c2)
