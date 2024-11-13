# core/services/excel_service.py
import pandas as pd
from typing import List, Dict, Any
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from core.models.template import Template, TemplateData

class ExcelService:
    @staticmethod
    def generate_template_excel(template: Template) -> str:
        """Generate an Excel template file based on template columns."""
        df = pd.DataFrame(columns=template.columns)
        
        # Create Excel file
        excel_file = ContentFile(b'')
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        
        # Save file
        file_path = f'templates/{template.file_code}_template.xlsx'
        default_storage.save(file_path, excel_file)
        return file_path

    @staticmethod
    def parse_excel_data(file_path: str, template: Template) -> List[Dict[str, Any]]:
        """Parse Excel file and validate against template columns."""
        df = pd.read_excel(file_path)
        
        # Validate columns
        missing_columns = set(template.columns) - set(df.columns)
        if missing_columns:
            raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
        
        # Convert DataFrame to list of dictionaries
        records = df[template.columns].to_dict('records')
        return records

    @staticmethod
    def generate_report(template_data: TemplateData) -> str:
        """Generate Excel report from template data."""
        df = pd.DataFrame([template_data.data])
        
        # Create Excel file
        excel_file = ContentFile(b'')
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        
        # Save file
        file_path = (
            f'reports/{template_data.template.file_code}_'
            f'{template_data.department.code}_{template_data.academic_year}.xlsx'
        )
        default_storage.save(file_path, excel_file)
        return file_path

    @staticmethod
    def generate_consolidated_report(template: Template, academic_year: str) -> str:
        """Generate consolidated report for all departments."""
        template_data = TemplateData.objects.filter(
            template=template,
            academic_year=academic_year,
            status='APPROVED'
        )
        
        all_data = []
        for data in template_data:
            dept_data = data.data.copy()
            dept_data['Department'] = data.department.name
            all_data.append(dept_data)
        
        if not all_data:
            raise ValueError("No approved data found for the template")
        
        df = pd.DataFrame(all_data)
        
        # Create Excel file
        excel_file = ContentFile(b'')
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        
        # Save file
        file_path = f'reports/consolidated_{template.file_code}_{academic_year}.xlsx'
        default_storage.save(file_path, excel_file)
        return file_path