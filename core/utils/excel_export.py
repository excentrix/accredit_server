# core/utils/excel_export.py
from openpyxl import Workbook
from openpyxl.styles import Alignment, PatternFill, Font
from openpyxl.utils import get_column_letter
from operator import itemgetter

class ExcelExporter:
    def __init__(self, template, academic_year):
        self.template = template
        self.academic_year = academic_year
        self.wb = Workbook()
        self.ws = self.wb.active
        self.current_row = 1

    def _write_headers(self):
        # Write each header row
        for header in self.template.headers:
            # Calculate the last column letter
            last_column = get_column_letter(len(self.template.columns))
            
            # Merge cells for header
            merge_range = f'A{self.current_row}:{last_column}{self.current_row}'
            self.ws.merge_cells(merge_range)
            
            # Set header cell value and formatting
            cell = self.ws.cell(row=self.current_row, column=1)
            cell.value = header
            cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="E0E0E0", end_color="E0E0E0", fill_type="solid")
            
            self.current_row += 1

    def _write_column_headers(self):
        # Write column headers
        for col, column_def in enumerate(self.template.columns, start=1):
            cell = self.ws.cell(row=self.current_row, column=col)
            cell.value = column_def['display_name']
            cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="F0F0F0", end_color="F0F0F0", fill_type="solid")
            
            # Set column width based on content
            column_letter = get_column_letter(col)
            max_length = max(
                len(line) for line in column_def['display_name'].split('\n')
            )
            self.ws.column_dimensions[column_letter].width = max(
                max_length + 2,
                15 if col == 1 else 30 if col == 3 else 12
            )
        
        self.current_row += 1

    def _write_data(self, submissions):
        # Get all data rows from all submissions and sort them
        all_data = []
        for submission in submissions:
            department_code = submission.department.code
            data_rows = submission.data_rows.all().order_by('row_number')
            
            for data_row in data_rows:
                all_data.append({
                    'department_code': department_code,
                    'data': data_row.data
                })
        
        # Sort by department code
        all_data.sort(key=lambda x: x['department_code'])
        
        # Write sorted data
        for row_data in all_data:
            for col, column_def in enumerate(self.template.columns, start=1):
                cell = self.ws.cell(row=self.current_row, column=col)
                cell.value = row_data['data'].get(column_def['name'], '')
                
                # Set cell alignment and text wrapping
                cell.alignment = Alignment(
                    vertical='center',
                    wrap_text=True,
                    horizontal='left' if col == 3 else 'center'  # Left align long text columns
                )
            self.current_row += 1

    def export(self, submissions):
        self._write_headers()
        self._write_column_headers()
        self._write_data(submissions)
        return self.wb