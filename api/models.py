from django.db import models
from django.contrib.auth.models import Group
from django.contrib.auth.models import AbstractUser, BaseUserManager

class Department(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name
    
class CustomUserManager(BaseUserManager):
    def create_user(self, id, password=None, role=None, **extra_fields):
        if not id:
            raise ValueError("The USN must be set")
        # if not extra_fields.get('department'):
        #     raise ValueError("The Department must be set")
        
        if not role:
            role = User.Role.FACULTY

        user = self.model(id=id, role=role, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        
        try:
            if role == User.Role.ADMIN:
                group = Group.objects.get(name='Admin')
            elif role == User.Role.NH:
                group = Group.objects.get(name='NH')
            elif role == User.Role.FACULTY:
                group = Group.objects.get(name='Faculty')
            else:
                raise ValueError("Invalid role")
        except Group.DoesNotExist:
            # Handle the case where the group does not exist
            raise ValueError(f"{role} group does not exist. Please create it in the admin panel.")
            
        user.groups.add(group)
        
        return user

    def create_superuser(self, id, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(id, password, role=User.Role.ADMIN, **extra_fields)
    
class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        NH = 'NH', 'NH'
        FACULTY = 'FACULTY', 'Faculty'
        
        
    base_role = Role.ADMIN

    id = models.CharField(max_length=12, unique=True, primary_key=True )
    name = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, null=True, blank=True, default=None)
    role = models.CharField(max_length=10, choices=Role.choices, default=base_role)
    
    username = None
    first_name = None   
    last_name = None
    email = None
    
    USERNAME_FIELD = 'id'
    REQUIRED_FIELDS = ['name']
    objects = CustomUserManager() # type: ignore

    
    def __str__(self):
        return self.id + " - " + self.name

class NaacFile(models.Model):
    section = models.CharField(max_length=100)
    subsection = models.CharField(max_length=100, blank=True)
    heading = models.TextField()
    structure = models.JSONField(blank=True)
    data = models.JSONField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    academic_year = models.CharField(max_length=9)

    def __str__(self):
        if self.subsection == "":
            return f"{self.section} - {self.heading}"
        else:
            return f"{self.section} - {self.subsection} - {self.heading}"

    class Meta:
        verbose_name_plural = "NAAC Files"
        unique_together = ('section', 'subsection')
        
    def update_structure(self, new_structure):
        old_structure = self.structure
        self.structure = new_structure
        self.save()

        # Update existing data to match new structure
        updated_data = []
        for item in self.data:
            new_item = {}
            for key, value_type in new_structure.items():
                if key in item:
                    new_item[key] = item[key]
                else:
                    new_item[key] = None
            updated_data.append(new_item)
        
        self.data = updated_data
        self.save()