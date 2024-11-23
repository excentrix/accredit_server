# core/utils/excel_export.py
from openpyxl import Workbook
from openpyxl.styles import Alignment, PatternFill, Font, Border, Side
from openpyxl.utils import get_column_letter
from datetime import datetime

class ExcelExporter:
    def __init__(self, template, academic_year):
        self.template = template
        self.academic_year = academic_year
        self.wb = Workbook()
        self.ws = self.wb.active
        self.current_row = 1
        
        # Define styles
        self.header_style = {
            'font': Font(bold=True, size=12),
            'fill': PatternFill(start_color="CCE5FF", end_color="CCE5FF", fill_type="solid"),
            'border': Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            ),
            'alignment': Alignment(horizontal='center', vertical='center', wrap_text=True)
        }
        
        self.subheader_style = {
            'font': Font(bold=True, size=11),
            'fill': PatternFill(start_color="E6F3FF", end_color="E6F3FF", fill_type="solid"),
            'border': Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            ),
            'alignment': Alignment(horizontal='center', vertical='center', wrap_text=True)
        }
        
        self.data_style = {
            'font': Font(size=10),
            'border': Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            ),
            'alignment': Alignment(vertical='center', wrap_text=True)
        }

    def _apply_styles(self, cell, styles):
        for key, value in styles.items():
            setattr(cell, key, value)

    def _write_title_info(self):
        # Write template and academic year information
        title_info = [
            f"Template: {self.template.name}",
            f"Code: {self.template.code}",
            f"Academic Year: {self.academic_year.name}",
            f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ]

        for info in title_info:
            cell = self.ws.cell(row=self.current_row, column=1, value=info)
            cell.font = Font(bold=True, size=12)
            self.current_row += 1

        # Add spacing
        self.current_row += 1

    def _get_flattened_columns(self, columns):
        """Flatten nested column structure"""
        flat_columns = []
        for column in columns:
            if column['type'] == 'single':
                flat_columns.append(column)
            elif column['type'] == 'group':
                for nested_column in column['columns']:
                    nested_column['name'] = f"{column['name']}_{nested_column['name']}"
                    flat_columns.append(nested_column)
        return flat_columns

    def _write_section(self, section_index, submissions):
        try:
            # Get section from template metadata
            if not self.template.metadata or section_index >= len(self.template.metadata):
                print(f"Invalid section index: {section_index}")
                return

            section = self.template.metadata[section_index]
            
            # Write section headers if present
            if 'headers' in section and section['headers']:
                # Get the number of columns for merging
                columns = self._get_flattened_columns(section['columns'])
                last_column = len(columns) if columns else 1
                
                for header in section['headers']:
                    merge_range = f'A{self.current_row}:{get_column_letter(max(1, last_column))}{self.current_row}'
                    self.ws.merge_cells(merge_range)
                    header_cell = self.ws.cell(row=self.current_row, column=1, value=header)
                    self._apply_styles(header_cell, self.header_style)
                    self.current_row += 1

            # Get flattened columns
            columns = self._get_flattened_columns(section['columns'])
            if not columns:
                print("No columns found in section")
                return

            # Write column headers
            for col_idx, column in enumerate(columns, start=1):
                cell = self.ws.cell(row=self.current_row, column=col_idx, value=column['name'])
                self._apply_styles(cell, self.subheader_style)
                
                # Set column width
                column_letter = get_column_letter(col_idx)
                self.ws.column_dimensions[column_letter].width = max(
                    len(str(column['name'])) + 2,
                    15
                )

            self.current_row += 1

            # Write data rows
            for submission in submissions:
                rows = submission.data_rows.filter(section_index=section_index)
                for row_data in rows:
                    for col_idx, column in enumerate(columns, start=1):
                        value = row_data.data.get(column['name'], '')
                        cell = self.ws.cell(
                            row=self.current_row, 
                            column=col_idx, 
                            value=value
                        )
                        style = self.data_style.copy()
                        # Left align text for longer fields
                        if len(str(value)) > 50:
                            style['alignment'] = Alignment(horizontal='left', vertical='center', wrap_text=True)
                        self._apply_styles(cell, style)
                    self.current_row += 1

            # Add spacing after section
            self.current_row += 1

        except Exception as e:
            print(f"Error in _write_section: {str(e)}")
            raise

    def export_to_worksheet(self, ws, submissions):
        """Export to an existing worksheet"""
        try:
            self.ws = ws
            self.current_row = 1
            
            if not submissions.exists():
                return False
                
            # Write title information
            self._write_title_info()

            # Process each section
            if self.template.metadata:
                for section_index in range(len(self.template.metadata)):
                    self._write_section(section_index, submissions)
            else:
                print(f"No metadata found for template {self.template.code}")

            # Auto-adjust row heights
            for row in self.ws.rows:
                max_length = 0
                for cell in row:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value).split('\n')))
                if max_length > 1:
                    self.ws.row_dimensions[cell.row].height = max_length * 15

            return True

        except Exception as e:
            print(f"Error in export_to_worksheet: {str(e)}")
            raise

    def export(self, submissions):
        if not submissions.exists():
            return self.wb

        self.ws.title = f"{self.template.code} Data"
        self.export_to_worksheet(self.ws, submissions)
        return self.wb