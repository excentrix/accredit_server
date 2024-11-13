# api/views/template.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from core.models.template import Template, TemplateData
from api.serializers.template import TemplateSerializer, TemplateDataSerializer
from core.constants import ApprovalStatus, UserRoles

class TemplateViewSet(viewsets.ModelViewSet):
    queryset = Template.objects.filter(is_active=True)
    serializer_class = TemplateSerializer
    filterset_fields = ['type']

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.role != UserRoles.ADMIN:
            return queryset.filter(is_active=True)
        return queryset

class TemplateDataViewSet(viewsets.ModelViewSet):
    serializer_class = TemplateDataSerializer
    filterset_fields = ['template', 'department', 'academic_year', 'status']

    def get_queryset(self):
        user = self.request.user
        queryset = TemplateData.objects.all()

        if user.role == UserRoles.FACULTY:
            return queryset.filter(department=user.department)
        elif user.role == UserRoles.HOD:
            return queryset.filter(department=user.headed_department)
        return queryset

    def perform_create(self, serializer):
        serializer.save(
            submitted_by=self.request.user,
            department=self.request.user.department
        )

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        template_data = self.get_object()
        if template_data.status != ApprovalStatus.DRAFT:
            return Response(
                {'error': 'Only draft submissions can be submitted'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        template_data.status = ApprovalStatus.PENDING_APPROVAL
        template_data.save()
        return Response({'status': 'submitted'})

    @action(detail=True, methods=['post'])
    def review(self, request, pk=None):
        if not request.user.is_iqac_director:
            return Response(
                {'error': 'Only IQAC Director can review submissions'},
                status=status.HTTP_403_FORBIDDEN
            )

        template_data = self.get_object()
        status = request.data.get('status')
        comments = request.data.get('comments', '')

        if status not in [ApprovalStatus.APPROVED, ApprovalStatus.REJECTED]:
            return Response(
                {'error': 'Invalid status'},
                status=status.HTTP_400_BAD_REQUEST
            )

        template_data.status = status
        template_data.review_comments = comments
        template_data.reviewed_by = request.user
        template_data.review_date = timezone.now()
        template_data.save()

        return Response({'status': 'reviewed'})