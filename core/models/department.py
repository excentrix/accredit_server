# core/models/department.py
from django.db import models
from core.models.mixins import TimeStampedModel

class Department(TimeStampedModel):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    hod = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='headed_department'
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Convert department code to uppercase
        self.code = self.code.upper()
        super().save(*args, **kwargs)