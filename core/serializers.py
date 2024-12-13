from rest_framework import serializers
from .models import Criteria,  AcademicYear, DashboardActivity, Template, DataSubmission, SubmissionData, SubmissionHistory, Template, Board

from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class AcademicYearSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicYear
        fields = ['id', 'name', 'start_date', 'end_date', 'is_current']

class TemplateSerializer(serializers.ModelSerializer):
    board = serializers.SerializerMethodField()
    criteria = serializers.PrimaryKeyRelatedField(queryset=Criteria.objects.all())

    class Meta:
        model = Template
        fields = ['id', 'code', 'name', 'metadata', 'board', 'criteria']

    def get_board(self, obj):
        if obj.criteria and obj.criteria.board:
            return {
                'id': obj.criteria.board.id,
                'name': obj.criteria.board.name,
                'code': obj.criteria.board.code
            }
        return None

    def validate(self, data):
        request = self.context.get('request')
        if not request:
            return data

        board_id = request.data.get('board')
        criteria = data.get('criteria')

        if board_id and criteria:
            # Compare board IDs
            if criteria.board.id != int(board_id):
                raise serializers.ValidationError({
                    'board': f'Criteria {criteria.number} belongs to board {criteria.board.id}, not {board_id}'
                })

        return data

    def create(self, validated_data):
        return super().create(validated_data)

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)

    # def validate_columns(self, value):
    #     required_keys = {'name', 'display_name', 'type'}
    #     for column in value:
    #         if not all(key in column for key in required_keys):
    #             raise serializers.ValidationError(
    #                 "Each column must contain 'name', 'display_name', and 'type'"
    #             )
    #     return value

class SubmissionDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubmissionData
        fields = ['section_index', 'row_number', 'data']
        
class SubmissionHistorySerializer(serializers.ModelSerializer):
    performed_by_name = serializers.CharField(source='performed_by.get_full_name')
    
    class Meta:
        model = SubmissionHistory
        fields = ['id', 'action', 'performed_by_name', 'performed_at', 'details']


class DataSubmissionSerializer(serializers.ModelSerializer):
    data_rows = SubmissionDataSerializer(many=True, read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    template_name = serializers.CharField(source='template.name', read_only=True)
    template_code = serializers.CharField(source='template.code', read_only=True)
    submitted_by_name = serializers.CharField(source='submitted_by.get_full_name', read_only=True)
    academic_year_name = serializers.CharField(source='academic_year.name', read_only=True)
    history = SubmissionHistorySerializer(many=True, read_only=True)
    
    class Meta:
        model = DataSubmission
        fields = [
            'id', 'template', 'department', 'academic_year', 'academic_year_name',
            'status', 'submitted_at', 'verified_by', 'verified_at', 
            'rejection_reason', 'data_rows', 'department_name', 
            'template_name', 'template_code','submitted_by_name', 'history'
        ]
        read_only_fields = ['submitted_by', 'verified_by', 'verified_at']

    def validate(self, data):
        # Ensure user can only submit for their department
        user = self.context['request'].user
        if user.roles.filter('Faculty').exists and data['department'] != user.department:
            raise serializers.ValidationError(
                "You can only submit data for your own department"
            )
        return data


class CriteriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Criteria
        fields = ['id', 'number', 'name', 'description']
        
class BoardSerializer(serializers.ModelSerializer):
    

    class Meta:
        model = Board
        fields = ['id', 'name', 'code']
        
class DashboardStatsSerializer(serializers.Serializer):
    total_submissions = serializers.IntegerField()
    pending_review = serializers.IntegerField()
    approved_submissions = serializers.IntegerField()
    rejected_submissions = serializers.IntegerField()
    completion_rate = serializers.FloatField()

class ActivityTimelineSerializer(serializers.Serializer):
    date = serializers.DateField()
    submissions = serializers.IntegerField()
    approvals = serializers.IntegerField()
    rejections = serializers.IntegerField()

class CriteriaCompletionSerializer(serializers.Serializer):
    criterion_number = serializers.IntegerField()
    criterion_name = serializers.CharField()
    completed = serializers.IntegerField()
    total = serializers.IntegerField()
    percentage = serializers.SerializerMethodField()

    def get_percentage(self, obj):
        return round((obj['completed'] / obj['total'] * 100) if obj['total'] > 0 else 0, 2)

class FacultyStatsSerializer(serializers.Serializer):
    total_submissions = serializers.IntegerField()
    pending_templates = serializers.IntegerField()
    approved_submissions = serializers.IntegerField()
    rejected_submissions = serializers.IntegerField()
    department_progress = serializers.FloatField()
    
class DashboardActivitySerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(source=User.get_full_name)
    department = serializers.StringRelatedField(source='department.name', allow_null=True)
    template = serializers.SerializerMethodField()

    class Meta:
        model = DashboardActivity
        fields = ['id', 'user', 'department', 'template', 'action', 'timestamp']

    def get_template(self, obj):
        return {
            'code': obj.template.code,
            'name': obj.template.name
        }
        