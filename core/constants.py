from django.db import models

class UserRoles(models.TextChoices):
    ADMIN = 'ADMIN', 'Admin'
    IQAC_DIRECTOR = 'IQAC_DIRECTOR', 'IQAC Director'
    HOD = 'HOD', 'Head of Department'
    FACULTY = 'FACULTY', 'Faculty'

class ApprovalStatus(models.TextChoices):
    DRAFT = 'DRAFT', 'Draft'
    PENDING_APPROVAL = 'PENDING_APPROVAL', 'Pending Approval'
    APPROVED = 'APPROVED', 'Approved'
    REJECTED = 'REJECTED', 'Rejected'

class TemplateType(models.TextChoices):
    CRITERION_1 = 'CRITERION_1', 'Criterion 1'
    CRITERION_2 = 'CRITERION_2', 'Criterion 2'
    CRITERION_3 = 'CRITERION_3', 'Criterion 3'
    CRITERION_4 = 'CRITERION_4', 'Criterion 4'
    CRITERION_5 = 'CRITERION_5', 'Criterion 5'
    CRITERION_6 = 'CRITERION_6', 'Criterion 6'
    CRITERION_7 = 'CRITERION_7', 'Criterion 7'