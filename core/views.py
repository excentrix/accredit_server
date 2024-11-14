from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.http import HttpResponse
from .utils.excel_export import ExcelExporter
from datetime import datetime
import io
from rest_framework.views import APIView

from .models import (
    User, Department, AcademicYear, Template, 
    DataSubmission, SubmissionData
)
from .serializers import (
    UserSerializer, DepartmentSerializer, AcademicYearSerializer,
    TemplateSerializer, DataSubmissionSerializer, SubmissionDataSerializer
)

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