# api/serializers/template.py
from rest_framework import serializers
from core.models.template import Template, TemplateData
from core.models.department import Department

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name', 'code']

class TemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Template
        fields = '__all__'

class TemplateDataSerializer(serializers.ModelSerializer):
    department = DepartmentSerializer(read_only=True)
    template = TemplateSerializer(read_only=True)
    submitted_by_name = serializers.CharField(source='submitted_by.get_full_name', read_only=True)
    reviewed_by_name = serializers.CharField(source='reviewed_by.get_full_name', read_only=True)

    class Meta:
        model = TemplateData
        fields = '__all__'
        read_only_fields = ['submitted_by', 'reviewed_by', 'review_date']

    def validate_data(self, value):
        template = self.instance.template if self.instance else self.context['template']
        required_columns = set(template.columns)
        provided_columns = set(value.keys())
        
        if not required_columns.issubset(provided_columns):
            missing_columns = required_columns - provided_columns
            raise serializers.ValidationError(
                f"Missing required columns: {', '.join(missing_columns)}"
            )
        return value