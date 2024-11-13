# api/views/excel.py
from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from django.core.files.storage import default_storage
from core.services.excel_service import ExcelService
from core.models.template import Template, TemplateData

class ExcelUploadView(views.APIView):
    parser_classes = [MultiPartParser]

    def post(self, request, template_id):
        try:
            template = Template.objects.get(id=template_id)
            excel_file = request.FILES['file']
            
            # Save the uploaded file temporarily
            file_path = default_storage.save(
                f'temp/{excel_file.name}',
                excel_file
            )
            
            # Parse the Excel file
            data = ExcelService.parse_excel_data(file_path, template)
            
            # Clean up temporary file
            default_storage.delete(file_path)
            
            return Response(data)
            
        except Template.DoesNotExist:
            return Response(
                {'error': 'Template not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class ExcelDownloadView(views.APIView):
    def get(self, request, template_id):
        try:
            template = Template.objects.get(id=template_id)
            file_path = ExcelService.generate_template_excel(template)
            
            return Response({
                'file_url': default_storage.url(file_path)
            })
            
        except Template.DoesNotExist:
            return Response(
                {'error': 'Template not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )