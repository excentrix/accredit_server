# core/models/mixins.py
from django.db import models

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        

class AcademicYear(models.Model):
    year = models.CharField(max_length=9, unique=True)  # Format: 2023-2024
    is_active = models.BooleanField(default=False)
    
    def __str__(self):
        return self.year

    class Meta:
        ordering = ['-year']