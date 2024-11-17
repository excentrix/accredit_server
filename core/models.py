# core/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
# from django.contrib.postgres.fields import JSONField

class User(AbstractUser):
    ROLE_CHOICES = [
        ('faculty', 'Faculty'),
        ('iqac_director', 'IQAC Director'),
        ('admin', 'Admin'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    department = models.ForeignKey(
        'Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )

    class Meta:
        ordering = ['username']

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
class Department(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    
    def __str__(self):
        return self.name

class AcademicYear(models.Model):
    year = models.CharField(max_length=7, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)

    class Meta:
        ordering = ['-year']

    def __str__(self):
        return self.year

    def save(self, *args, **kwargs):
        if self.is_current:
            # Set all other years to not current
            AcademicYear.objects.all().update(is_current=False)
        super().save(*args, **kwargs)

class Template(models.Model):
    """Stores the structure of different NAAC document templates"""
    id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=500)
    # description = models.TextField(null=True, blank=True)
    # headers = models.JSONField()
    metadata = models.JSONField()
    # columns = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # column_groups = models.JSONField(default=list)
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    
    # class Meta:
    #     ordering = ['code']

class DataSubmission(models.Model):
    """Tracks the submission status of data for each department"""
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('submitted', 'Submitted for Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    template = models.ForeignKey(Template, on_delete=models.CASCADE)
    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submissions')
    verified_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='verifications'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    submitted_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(null=True, blank=True)
    
    class Meta:
        unique_together = ['department', 'academic_year', 'template']
        
    def __str__(self):
        return f"{self.department} - {self.template.code} ({self.academic_year})"

class SubmissionData(models.Model):
    """Stores the actual data submitted by departments"""
    submission = models.ForeignKey(DataSubmission, on_delete=models.CASCADE, related_name='data_rows')
    data = models.JSONField()
    row_number = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['submission', 'row_number']
        ordering = ['row_number']
        
    def __str__(self):
        return f"{self.submission} - Row {self.row_number}"