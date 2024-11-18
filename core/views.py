from rest_framework import viewsets, status, permissions
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, NotFound
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.http import HttpResponse

from .services import AcademicYearTransitionService
from .tasks import process_academic_year_transition

from .filters import DataSubmissionFilter
from .utils.excel_export import ExcelExporter
from datetime import datetime
import io
import re
from rest_framework.views import APIView
import json

from .models import (
    AcademicYearTransition, User, Department, AcademicYear, Template, 
    DataSubmission, SubmissionData
)
from .serializers import (
    UserSerializer, DepartmentSerializer, AcademicYearSerializer,
    TemplateSerializer, DataSubmissionSerializer, SubmissionDataSerializer
)

import openpyxl
from openpyxl import load_workbook
from django.core.exceptions import ValidationError

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .serializers import (
    UserSerializer, LoginSerializer, DepartmentSerializer,
    TemplateSerializer, DataSubmissionSerializer
)
from .models import User, Department, Template, DataSubmission
from .permissions import IsFaculty, IsIQACDirector, IsAdmin

class AuthViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=['post'])
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            user = authenticate(username=username, password=password)
            
            if user:
                refresh = RefreshToken.for_user(user)
                user_serializer = UserSerializer(user)
                
                return Response({
                    'status': 'success',
                    'data': {
                        'user': user_serializer.data,
                        'tokens': {
                            'access': str(refresh.access_token),
                            'refresh': str(refresh)
                        }
                    }
                })
            
            return Response({
                'status': 'error',
                'message': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        return Response({
            'status': 'error',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def logout(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'status': 'success'})
        except Exception:
            return Response({'status': 'error'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def me(self, request):
        if not request.user.is_authenticated:
            return Response({
                'status': 'error',
                'message': 'Not authenticated'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        serializer = UserSerializer(request.user)
        return Response({
            'status': 'success',
            'data': serializer.data
        })

class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        return User.objects.all()

class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role == 'faculty':
            return Department.objects.filter(id=self.request.user.department.id)
        return Department.objects.all()
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsIQACDirector|IsAdmin]
        return super().get_permissions()

class AcademicYearViewSet(viewsets.ModelViewSet):
    queryset = AcademicYear.objects.all()
    serializer_class = AcademicYearSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['post'])
    def set_current(self, request, pk=None):
        academic_year = self.get_object()
        academic_year.is_current = True
        academic_year.save()
        return Response({'status': 'academic year set as current'})

class TemplateViewSet(viewsets.ModelViewSet):
    queryset = Template.objects.all()
    serializer_class = TemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field='code'
    
    def get_object(self):
        try:
            # Get the lookup value from kwargs
            lookup_value = self.kwargs.get(self.lookup_field)
            # print(f"Attempting to find template with code: {lookup_value}")
            
            # Get all templates (for debugging)
            all_templates = list(self.queryset.values_list('code', flat=True))
            # print(f"Available template codes: {all_templates}")
            
            # Try to get the object
            obj = self.queryset.get(code=lookup_value)
            # print(f"Found template: {obj.code}")
            
            # Check permissions
            self.check_object_permissions(self.request, obj)
            return obj
            
        except Template.DoesNotExist:
            print(f"Template not found with code: {lookup_value}")
            raise NotFound(detail=f"Template with code '{lookup_value}' not found")

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except NotFound as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset().order_by('code')
        print(f"List called, found {queryset.count()} templates")  # Debug print
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    

    @action(detail=True, methods=['post', 'get'])
    def data(self, request, code=None):
        print("Data action called")
        try:
            template = self.get_object()
            current_year = AcademicYear.objects.filter(is_current=True).first()

            if not current_year:
                return Response({
                    'status': 'error',
                    'message': 'No active academic year found'
                }, status=status.HTTP_400_BAD_REQUEST)

            if not request.user.department:
                return Response({
                    'status': 'error',
                    'message': 'User has no associated department'
                }, status=status.HTTP_400_BAD_REQUEST)

            if request.method == 'POST':
                try:
                    with transaction.atomic():
                        # Create or get submission
                        submission, _ = DataSubmission.objects.get_or_create(
                            template=template,
                            department=request.user.department,
                            academic_year=current_year,
                            defaults={
                                'submitted_by': request.user,
                                'status': 'draft'
                            }
                        )

                        # Validate incoming data against template columns
                        data = request.data.get('data', {})
                        required_fields = [
                            col['name'] for col in template.columns 
                            if col.get('required', False)
                        ]
                        
                        missing_fields = [
                            field for field in required_fields 
                            if field not in data or not data[field]
                        ]
                        
                        if missing_fields:
                            return Response({
                                'status': 'error',
                                'message': f'Missing required fields: {", ".join(missing_fields)}'
                            }, status=status.HTTP_400_BAD_REQUEST)

                        # Add new data row
                        row_number = SubmissionData.objects.filter(
                            submission=submission
                        ).count() + 1
                        
                        submission_data = SubmissionData.objects.create(
                            submission=submission,
                            row_number=row_number,
                            data=data
                        )

                        return Response({
                            'status': 'success',
                            'message': 'Data saved successfully',
                            'data': {
                                'id': submission_data.id,
                                'row_number': row_number,
                                'data': data
                            }
                        })

                except Exception as e:
                    return Response({
                        'status': 'error',
                        'message': str(e)
                    }, status=status.HTTP_400_BAD_REQUEST)

            # GET method
            try:
                submission = DataSubmission.objects.get(
                    template=template,
                    department=request.user.department,
                    academic_year=current_year
                )
                data_rows = SubmissionData.objects.filter(submission=submission)\
                    .order_by('row_number')
                
                return Response({
                    'status': 'success',
                    'data': {
                        'submission_id': submission.id,
                        'status': submission.status,
                        'rows': [
                            {
                                'id': row.id,
                                'row_number': row.row_number,
                                'data': row.data
                            } for row in data_rows
                        ]
                    }
                })
            except DataSubmission.DoesNotExist:
                return Response({
                    'status': 'success',
                    'data': {
                        'submission_id': None,
                        'status': None,
                        'rows': []
                    }
                })

        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    @action(detail=True, methods=['put', 'delete'])
    def data_row(self, request, code=None, *args, **kwargs):
        template = self.get_object()
        row_id = request.query_params.get('row_id')
        
        if not row_id:
            return Response({
                'status': 'error',
                'message': 'row_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            submission_data = SubmissionData.objects.get(
                id=row_id,
                submission__template=template,
                submission__department=request.user.department
            )
        except SubmissionData.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Data row not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Check if submission is editable
        if submission_data.submission.status not in ['draft', 'rejected']:
            return Response({
                'status': 'error',
                'message': 'Cannot modify data that has been submitted or approved'
            }, status=status.HTTP_400_BAD_REQUEST)

        if request.method == 'PUT':
            try:
                with transaction.atomic():
                    # Validate incoming data against template columns
                    data = request.data.get('data', {})
                    required_fields = [
                        col['name'] for col in template.columns 
                        if col.get('required', False)
                    ]
                    
                    missing_fields = [
                        field for field in required_fields 
                        if field not in data or not data[field]
                    ]
                    
                    if missing_fields:
                        return Response({
                            'status': 'error',
                            'message': f'Missing required fields: {", ".join(missing_fields)}'
                        }, status=status.HTTP_400_BAD_REQUEST)

                    # Update the data
                    submission_data.data = data
                    submission_data.save()

                    return Response({
                        'status': 'success',
                        'message': 'Data updated successfully',
                        'data': {
                            'id': submission_data.id,
                            'row_number': submission_data.row_number,
                            'data': submission_data.data
                        }
                    })

            except Exception as e:
                return Response({
                    'status': 'error',
                    'message': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'DELETE':
            try:
                with transaction.atomic():
                    # Store the row number before deleting
                    deleted_row_number = submission_data.row_number
                    submission_data.delete()

                    # Reorder remaining rows
                    subsequent_rows = SubmissionData.objects.filter(
                        submission=submission_data.submission,
                        row_number__gt=deleted_row_number
                    ).order_by('row_number')

                    for row in subsequent_rows:
                        row.row_number -= 1
                        row.save()

                    return Response({
                        'status': 'success',
                        'message': 'Data row deleted successfully'
                    })

            except Exception as e:
                return Response({
                    'status': 'error',
                    'message': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            'status': 'error',
            'message': 'Invalid method'
        }, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        
    @action(detail=False, methods=['POST'])
    def import_from_excel(self, request):
        if 'file' not in request.FILES:
            return Response({
                'status': 'error',
                'message': 'No file provided'
            }, status=status.HTTP_400_BAD_REQUEST)

        file = request.FILES['file']
        template_code = file.name.split('.xlsx')[0]

        try:
            wb = openpyxl.load_workbook(file)
            ws = wb.active

            # Process Excel structure
            sections = []
            current_section = None
            current_headers = []
            current_group = None
            
            for row_index, row in enumerate(ws.rows, start=1):
                first_cell = row[0].value
                if not first_cell:
                    continue

                # Check if this is a header row
                if re.match(r'^\d+\.\d+\.?\d*\s+[a-zA-Z]', str(first_cell)):
                    if current_section:
                        sections.append(current_section)
                    
                    current_headers = [first_cell.strip()]
                    current_section = {
                        'headers': current_headers,
                        'columns': []
                    }
                
                # Check if this is a column group row
                elif first_cell and any(cell.value for cell in row[1:]):
                    column_definitions = self._process_column_row(row)
                    
                    if self._is_group_header(column_definitions):
                        current_group = self._create_group_column(column_definitions)
                        current_section['columns'].append(current_group)
                    else:
                        if current_group:
                            current_group['columns'].extend(column_definitions)
                            current_group = None
                        else:
                            current_section['columns'].extend(column_definitions)

            # Add the last section
            if current_section:
                sections.append(current_section)

            # Create template data
            template_data = {
                'code': template_code,
                'name': sections[0]['headers'][0] if sections else '',
                'metadata': sections
            }

            # Save or update template
            try:
                template = Template.objects.get(code=template_code)
                serializer = self.get_serializer(template, data=template_data)
            except Template.DoesNotExist:
                serializer = self.get_serializer(data=template_data)

            if serializer.is_valid():
                serializer.save()
                return Response({
                    'status': 'success',
                    'message': f'Successfully imported template {template_code}',
                    'data': serializer.data
                })
            else:
                return Response({
                    'status': 'error',
                    'message': 'Invalid template data',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _process_column_row(self, row):
        """Process a row of column definitions"""
        columns = []
        for cell in row:
            if cell.value:
                column = {
                    'name': cell.value.strip(),
                    'type': 'single',
                    'data_type': self._determine_data_type(cell.value),
                    'required': True
                }
                
                if column['data_type'] == 'option':
                    column['options'] = self._determine_options(cell.value)
                
                columns.append(column)
        return columns

    def _determine_data_type(self, value):
        """Determine the data type of a column based on its name"""
        value_lower = value.lower()
        if 'date' in value_lower:
            return 'date'
        elif 'email' in value_lower:
            return 'email'
        elif 'link' in value_lower or 'url' in value_lower:
            return 'url'
        elif 'number' in value_lower or 'amount' in value_lower:
            return 'number'
        elif '(yes/no)' in value_lower or any(opt in value_lower for opt in ['choose', 'select']):
            return 'option'
        return 'string'

    def _determine_options(self, value):
        """Determine options for option-type columns"""
        if '(yes/no)' in value.lower():
            return ['Yes', 'No']
        # Add more option patterns as needed
        return []

    def _is_group_header(self, columns):
        """Determine if a row of columns represents a group header"""
        return len(columns) == 1 and not any(
            keyword in columns[0]['name'].lower() 
            for keyword in ['link', 'url', 'email', 'date']
        )

    def _create_group_column(self, columns):
        """Create a group column structure"""
        return {
            'name': columns[0]['name'],
            'type': 'group',
            'columns': []
        }

    def _process_column_groups(self, row):
        """Process row containing column group headers"""
        column_groups = []
        current_group = None
        
        for cell in row:
            if cell.value:
                current_group = cell.value.strip()
            if current_group:
                column_groups.append(current_group)
            
        return column_groups

    def _create_columns_with_groups(self, row, column_groups):
        """Create column definitions with their groups"""
        columns = []
        for idx, cell in enumerate(row):
            if cell.value:
                column_name = cell.value.strip()
                group = column_groups[idx] if idx < len(column_groups) else None
                
                # Create column definition
                column = {
                    'name': f"{column_name.lower().replace(' ', '_')}",
                    'display_name': column_name,
                    'type': 'number',  # Default to number for this template
                    'required': True,
                    'description': f'Enter {column_name.lower()}',
                    'group': group
                }
                
                columns.append(column)
        
        return columns
class DataSubmissionViewSet(viewsets.ModelViewSet):
    serializer_class = DataSubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'faculty':
            return DataSubmission.objects.filter(department=user.department)
        return DataSubmission.objects.all()

    def perform_create(self, serializer):
        serializer.save(
            submitted_by=self.request.user,
            department=self.request.user.department
        )


    @action(detail=True, methods=['post'])
    def submit_for_approval(self, request, pk=None):
        submission = self.get_object()
        if submission.submitted_by != request.user:
            raise PermissionDenied("You don't have permission to submit this data")
        
        submission.status = 'submitted'
        submission.save()
        return Response({'status': 'submitted for approval'})

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        submission = self.get_object()
        if request.user.role != 'iqac_director':
            raise PermissionDenied("Only IQAC Director can approve submissions")
        
        submission.status = 'approved'
        submission.verified_by = request.user
        submission.save()
        return Response({'status': 'submission approved'})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        submission = self.get_object()
        if request.user.role != 'iqac_director':
            raise PermissionDenied("Only IQAC Director can reject submissions")
        
        reason = request.data.get('reason')
        if not reason:
            return Response(
                {'error': 'Rejection reason is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        submission.status = 'rejected'
        submission.verified_by = request.user
        submission.rejection_reason = reason
        submission.save()
        return Response({'status': 'submission rejected'})

    @action(detail=True, methods=['post'])
    def submit_data(self, request, pk=None):
        submission = self.get_object()
        if submission.submitted_by != request.user:
            raise PermissionDenied("You don't have permission to submit data")
        
        data_rows = request.data.get('data_rows', [])
        
        with transaction.atomic():
            # Clear existing data
            submission.data_rows.all().delete()
            
            # Create new data rows
            for index, row_data in enumerate(data_rows, 1):
                SubmissionData.objects.create(
                    submission=submission,
                    row_number=index,
                    data=row_data
                )
        
        return Response({'status': 'data submitted successfully'})
    
    @action(detail=False, methods=['get'])
    def export_template(self, request):
        if request.user.role != 'iqac_director':
            raise PermissionDenied("Only IQAC Director can export data")

        template_code = request.query_params.get('template_code')
        academic_year_id = request.query_params.get('academic_year')

        if not template_code or not academic_year_id:
            return Response(
                {'error': 'template_code and academic_year are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            template = Template.objects.get(code=template_code)
            academic_year = AcademicYear.objects.get(id=academic_year_id)
        except (Template.DoesNotExist, AcademicYear.DoesNotExist):
            return Response(
                {'error': 'Invalid template_code or academic_year'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get all approved submissions for this template and academic year
        submissions = DataSubmission.objects.filter(
            template=template,
            academic_year=academic_year,
            status='approved'
        ).select_related('department').prefetch_related('data_rows')

        # Create Excel file
        exporter = ExcelExporter(template, academic_year)
        workbook = exporter.export(submissions)

        # Save to buffer
        buffer = io.BytesIO()
        workbook.save(buffer)
        buffer.seek(0)

        # Generate filename
        filename = f"{template.code}_{academic_year.year}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        # Create the HttpResponse object with Excel mime type
        response = HttpResponse(
            buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response
    
class ExportTemplateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        print(f"Request user role: {request.user.role}")
        print(f"Query params: {request.query_params}")

        # Check if user is IQAC director
        if request.user.role != 'iqac_director':
            print("Access denied: User is not IQAC director")
            return Response(
                {"detail": "Only IQAC Director can export data"},
                status=status.HTTP_403_FORBIDDEN
            )

        template_code = request.query_params.get('template_code')
        academic_year_id = request.query_params.get('academic_year')

        print(f"Looking for template: {template_code}, academic year: {academic_year_id}")

        if not template_code or not academic_year_id:
            print("Missing required parameters")
            return Response(
                {'error': 'template_code and academic_year are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            template = Template.objects.get(code=template_code)
            academic_year = AcademicYear.objects.get(id=academic_year_id)
            print(f"Found template: {template.code} and academic year: {academic_year.year}")
        except (Template.DoesNotExist, AcademicYear.DoesNotExist) as e:
            print(f"Error finding template or academic year: {str(e)}")
            return Response(
                {'error': 'Invalid template_code or academic_year'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get all approved submissions
        submissions = DataSubmission.objects.filter(
            template=template,
            academic_year=academic_year,
            status='approved'
        ).select_related('department').prefetch_related('data_rows')

        print(f"Found {submissions.count()} approved submissions")

        # Create Excel file
        try:
            exporter = ExcelExporter(template, academic_year)
            workbook = exporter.export(submissions)
            print("Successfully created Excel file")
        except Exception as e:
            print(f"Error generating Excel file: {str(e)}")
            return Response(
                {'error': f'Error generating Excel file: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Save to buffer
        buffer = io.BytesIO()
        workbook.save(buffer)
        buffer.seek(0)

        # Generate filename
        filename = f"{template.code}_{academic_year.year}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        print(f"Sending file: {filename}")

        response = HttpResponse(
            buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response
    
class NameAutocompleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        query = request.GET.get('q', '')
        if query:
            # Fetch distinct names that contain the query string (case-insensitive)
            # matching_names = (
            #     Template.objects.filter(name__icontains=query)
            #     .values_list('name', flat=True)
            #     .distinct()[:10]  # Limit to top 10 suggestions
            # )
            matching_names = ['John Doe', 'Jane Doe', 'Alice Smith']
            

            return Response(list(matching_names), status=status.HTTP_200_OK)
        
        return Response([], status=status.HTTP_200_OK)
    
class DataSubmissionViewSet(viewsets.ModelViewSet):
    serializer_class = DataSubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_class = DataSubmissionFilter
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ['created_at', 'updated_at', 'academic_year__start_date']
    ordering = ['-academic_year__start_date', '-updated_at']
    
    def get_queryset(self):
        """
        Filter submissions based on user role:
        - Faculty can only see their department's submissions
        - IQAC Director can see all submissions
        """
        user = self.request.user
        queryset = DataSubmission.objects.select_related(
            'template', 'department', 'submitted_by', 'verified_by'
        ).prefetch_related('data_rows')
        
        if user.role == 'faculty':
            return queryset.filter(department=user.department)
        return queryset

    def perform_create(self, serializer):
        """Set the submitted_by field to the current user"""
        serializer.save(submitted_by=self.request.user)
        
    @action(detail=False)
    def current_academic_year(self, request):
        """Get submissions for current academic year"""
        current_year = AcademicYear.objects.filter(is_current=True).first()
        if not current_year:
            return Response({
                'status': 'error',
                'message': 'No current academic year set'
            }, status=status.HTTP_404_NOT_FOUND)

        queryset = self.filter_queryset(self.get_queryset().filter(
            academic_year=current_year
        ))
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False)
    def submission_status(self, request):
        """Get submission status summary for current academic year"""
        current_year = AcademicYear.objects.filter(is_current=True).first()
        if not current_year:
            return Response({
                'status': 'error',
                'message': 'No current academic year set'
            }, status=status.HTTP_404_NOT_FOUND)

        queryset = self.get_queryset().filter(academic_year=current_year)
        
        summary = {
            'total': queryset.count(),
            'draft': queryset.filter(status='draft').count(),
            'submitted': queryset.filter(status='submitted').count(),
            'approved': queryset.filter(status='approved').count(),
            'rejected': queryset.filter(status='rejected').count(),
            'academic_year': AcademicYearSerializer(current_year).data
        }

        return Response(summary)

    @action(detail=True, methods=['post'])
    def add_row(self, request, pk=None):
        """Add a new row to a specific section"""
        submission = self.get_object()
        
        # Check if submission is editable
        if submission.status not in ['draft', 'rejected']:
            return Response({
                'status': 'error',
                'message': 'Cannot modify data in current status'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate section index
        section_index = request.data.get('section_index')
        if section_index is None:
            return Response({
                'status': 'error',
                'message': 'section_index is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                # Get the next row number for this section
                next_row = (SubmissionData.objects.filter(
                    submission=submission,
                    section_index=section_index
                ).count() + 1)

                # Create new submission data
                submission_data = SubmissionData.objects.create(
                    submission=submission,
                    section_index=section_index,
                    row_number=next_row,
                    data=request.data.get('data', {})
                )

                return Response({
                    'status': 'success',
                    'message': 'Row added successfully',
                    'data': SubmissionDataSerializer(submission_data).data
                })

        except ValidationError as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['put'])
    def update_row(self, request, pk=None):
        """Update an existing row"""
        submission = self.get_object()
        
        if submission.status not in ['draft', 'rejected']:
            return Response({
                'status': 'error',
                'message': 'Cannot modify data in current status'
            }, status=status.HTTP_400_BAD_REQUEST)

        row_id = request.data.get('row_id')
        if not row_id:
            return Response({
                'status': 'error',
                'message': 'row_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                submission_data = get_object_or_404(
                    SubmissionData, 
                    submission=submission,
                    id=row_id
                )
                submission_data.data = request.data.get('data', {})
                submission_data.full_clean()
                submission_data.save()

                return Response({
                    'status': 'success',
                    'message': 'Row updated successfully',
                    'data': SubmissionDataSerializer(submission_data).data
                })

        except ValidationError as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'])
    def delete_row(self, request, pk=None):
        """Delete a row and reorder remaining rows"""
        submission = self.get_object()
        
        if submission.status not in ['draft', 'rejected']:
            return Response({
                'status': 'error',
                'message': 'Cannot modify data in current status'
            }, status=status.HTTP_400_BAD_REQUEST)

        row_id = request.query_params.get('row_id')
        if not row_id:
            return Response({
                'status': 'error',
                'message': 'row_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                submission_data = get_object_or_404(
                    SubmissionData, 
                    submission=submission,
                    id=row_id
                )
                
                section_index = submission_data.section_index
                deleted_row_number = submission_data.row_number
                
                # Delete the row
                submission_data.delete()
                
                # Reorder remaining rows
                SubmissionData.objects.filter(
                    submission=submission,
                    section_index=section_index,
                    row_number__gt=deleted_row_number
                ).update(row_number=models.F('row_number') - 1)

                return Response({
                    'status': 'success',
                    'message': 'Row deleted successfully'
                })

        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """Submit the data for approval"""
        submission = self.get_object()
        
        if submission.status not in ['draft', 'rejected']:
            return Response({
                'status': 'error',
                'message': 'Only draft or rejected submissions can be submitted'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Validate all data rows
            for data_row in submission.data_rows.all():
                data_row.full_clean()

            submission.status = 'submitted'
            submission.submitted_at = timezone.now()
            submission.save()

            return Response({
                'status': 'success',
                'message': 'Submission successful'
            })

        except ValidationError as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a submission (IQAC Director only)"""
        if not request.user.role == 'iqac_director':
            return Response({
                'status': 'error',
                'message': 'Only IQAC Director can approve submissions'
            }, status=status.HTTP_403_FORBIDDEN)

        submission = self.get_object()
        if submission.status != 'submitted':
            return Response({
                'status': 'error',
                'message': 'Only submitted data can be approved'
            }, status=status.HTTP_400_BAD_REQUEST)

        submission.status = 'approved'
        submission.verified_by = request.user
        submission.verified_at = timezone.now()
        submission.save()

        return Response({
            'status': 'success',
            'message': 'Submission approved'
        })

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a submission with comments (IQAC Director only)"""
        if not request.user.role == 'iqac_director':
            return Response({
                'status': 'error',
                'message': 'Only IQAC Director can reject submissions'
            }, status=status.HTTP_403_FORBIDDEN)

        submission = self.get_object()
        if submission.status != 'submitted':
            return Response({
                'status': 'error',
                'message': 'Only submitted data can be rejected'
            }, status=status.HTTP_400_BAD_REQUEST)

        reason = request.data.get('reason')
        if not reason:
            return Response({
                'status': 'error',
                'message': 'Rejection reason is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        submission.status = 'rejected'
        submission.verified_by = request.user
        submission.verified_at = timezone.now()
        submission.rejection_reason = reason
        submission.save()

        return Response({
            'status': 'success',
            'message': 'Submission rejected'
        })
        
class AcademicYearTransitionViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated, IsIQACDirector]

    @action(detail=True, methods=['post'])
    def start_transition(self, request, pk=None):
        """Start transition to a new academic year"""
        try:
            from_year = AcademicYear.objects.get(is_current=True)
            to_year = get_object_or_404(AcademicYear, pk=pk)

            transition_service = AcademicYearTransitionService(
                from_year=from_year,
                to_year=to_year,
                user=request.user
            )

            transition = transition_service.start_transition()
            
            # Start async task for processing
            process_academic_year_transition.delay(transition.id)

            return Response({
                'status': 'success',
                'message': 'Academic year transition started',
                'transition_id': transition.id
            })

        except ValidationError as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def transition_status(self, request, pk=None):
        """Get status of academic year transition"""
        transition = get_object_or_404(
            AcademicYearTransition,
            to_year_id=pk
        )

        return Response({
            'status': transition.status,
            'started_at': transition.started_at,
            'completed_at': transition.completed_at,
            'error_log': transition.error_log,
            'processed_by': transition.processed_by.get_full_name()
        })