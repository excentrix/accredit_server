from django.contrib.auth.models import AbstractUser
from django.db import models
from ..constants import UserRoles

class User(AbstractUser):
    role = models.CharField(
        max_length=20,
        choices=UserRoles.choices,
        default=UserRoles.FACULTY
    )
    department = models.ForeignKey(
        'core.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )
    phone = models.CharField(max_length=15, blank=True)
    
    @property
    def is_admin(self):
        return self.role == UserRoles.ADMIN
    
    @property
    def is_iqac_director(self):
        return self.role == UserRoles.IQAC_DIRECTOR
    
    @property
    def is_hod(self):
        return self.role == UserRoles.HOD

    def __str__(self):
        return f"{self.get_full_name()} ({self.username})"

    class Meta:
        ordering = ['username']