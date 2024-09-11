from rest_framework import serializers
from .models import NaacFile

class NaacFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = NaacFile
        fields = '__all__'

class StructureUpdateSerializer(serializers.Serializer):
    structure = serializers.JSONField()

class DataUpdateSerializer(serializers.Serializer):
    data = serializers.JSONField()  # type: ignore

class DataItemSerializer(serializers.Serializer):
    item = serializers.JSONField()

class DataItemDeleteSerializer(serializers.Serializer):
    index = serializers.IntegerField(min_value=0)