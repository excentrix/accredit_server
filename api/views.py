from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import NaacFile
from .serializers import (
    NaacFileSerializer, StructureUpdateSerializer, 
    DataUpdateSerializer, DataItemSerializer, DataItemDeleteSerializer
)

class NaacFileViewSet(viewsets.ModelViewSet):
    queryset = NaacFile.objects.all()
    serializer_class = NaacFileSerializer

    def get_queryset(self):
        queryset = NaacFile.objects.all()
        academic_year = self.request.query_params.get('academic_year')
        section = self.request.query_params.get('section')
        subsection = self.request.query_params.get('subsection')
        
        print(academic_year, section, subsection)
        
        if academic_year:
            queryset = queryset.filter(academic_year=academic_year)
        if section:
            queryset = queryset.filter(section=section)
        if subsection:
            queryset = queryset.filter(subsection=subsection)
        
        return queryset

    @action(detail=True, methods=['post'])
    def update_structure(self, request, pk=None):
        dynamic_data = self.get_object()
        serializer = StructureUpdateSerializer(data=request.data)
        if serializer.is_valid():
            new_structure = serializer.validated_data['structure']
            dynamic_data.update_structure(new_structure)
            return Response({'status': 'structure updated'})
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def update_data(self, request, pk=None):
        dynamic_data = self.get_object()
        serializer = DataUpdateSerializer(data=request.data)
        if serializer.is_valid():
            dynamic_data.data = serializer.validated_data['data']
            dynamic_data.save()
            return Response({'status': 'data updated'})
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def add_data_item(self, request, pk=None):
        dynamic_data = self.get_object()
        serializer = DataItemSerializer(data=request.data)
        if serializer.is_valid():
            new_item = serializer.validated_data['item']
            dynamic_data.data.append(new_item)
            dynamic_data.save()
            return Response({'status': 'data item added'})
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def delete_data_item(self, request, pk=None):
        dynamic_data = self.get_object()
        serializer = DataItemDeleteSerializer(data=request.data)
        if serializer.is_valid():
            item_index = serializer.validated_data['index']
            if 0 <= item_index < len(dynamic_data.data):
                del dynamic_data.data[item_index]
                dynamic_data.save()
                return Response({'status': 'data item deleted'})
            else:
                return Response({'error': 'Invalid index'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)