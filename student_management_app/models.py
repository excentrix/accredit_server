from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.contrib.auth import get_user_model

#OTP Verification model:
class OTP(models.Model):
    phone_number = models.CharField(max_length=15)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.phone_number} - {self.otp}'


class SessionYearModel(models.Model):
    id = models.AutoField(primary_key=True)
    session_start_year = models.DateField()
    session_end_year = models.DateField()
    objects = models.Manager()



# Overriding the Default Django Auth User and adding One More Field (user_type)
class CustomUser(AbstractUser):
    HOD = '1'
    STAFF = '2'
    STUDENT = '3'
    NAAC = '4'#
    Parent = '5'
    
    # EMAIL_TO_USER_TYPE_MAP = {
    #     'hod': HOD,
    #     'staff': STAFF,
    #     'student': STUDENT,
    #     'naac' : NAAC #
    # }

    user_type_data = ((HOD, "HOD"), (STAFF, "Staff"), (STUDENT, "Student"),(NAAC,"naac"),(Parent,"Parent")) #
    user_type = models.CharField(default=1, choices=user_type_data, max_length=10)
    mobile = models.CharField(max_length=15, default='1234567890')
    #role = models.CharField(max_length=50, blank=True, null=True)


class AdminHOD(models.Model):
    id = models.AutoField(primary_key=True)
    admin = models.OneToOneField(CustomUser, on_delete = models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = models.Manager()

#Am creating a NAAC and Parent model here

class NAAC(models.Model):
    id = models.AutoField(primary_key=True)
    naac_admin = models.OneToOneField(CustomUser, on_delete = models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = models.Manager()

class Parent(models.Model):
    id = models.AutoField(primary_key=True)
    naac_admin = models.OneToOneField(CustomUser, on_delete = models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = models.Manager()

class Staffs(models.Model):
    id = models.AutoField(primary_key=True)
    admin = models.OneToOneField(CustomUser, on_delete = models.CASCADE)
    address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = models.Manager()
#Form Builder
class Form(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Field(models.Model):
    FIELD_TYPES = [
        ('text', 'Text'),
        ('textarea', 'Textarea'),
        ('number', 'Number'),
        ('date', 'Date'),
        ('email', 'Email'),
    ]

    form = models.ForeignKey(Form, related_name='fields', on_delete=models.CASCADE)
    label = models.CharField(max_length=100)
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES)
    required = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.label} ({self.get_field_type_display()})"
    

#File upload
class UploadedFile(models.Model):
    file = models.FileField(upload_to='uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

class Courses(models.Model):
    id = models.AutoField(primary_key=True)
    course_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = models.Manager()

    def __str__(self):
	    return self.course_name

#Bulk Upload
class StudentAdmission(models.Model):
    name = models.CharField(max_length=100)
    mobile = models.CharField(max_length=15)
    email = models.EmailField(blank=True)
    role = models.CharField(max_length=15)
    #course = models.CharField(max_length=50)
    #academic_year = models.CharField(max_length=9)

    def __str__(self):
        return self.name

#Announcements:

class Announcement(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    is_new = models.BooleanField(default=True)
    announced_by = models.CharField(max_length=100,default='Admin')
    audience = models.CharField(max_length=50, choices=[
        ('Principal', 'Principal'),
        ('HoD', 'HoD'),
        ('Staff', 'Staff'),
        ('Students', 'Students'),
        ('Parents', 'Parents'),
        ('All', 'All of the above'),
    ], default='All')
    file = models.FileField(upload_to='announcements/files/', blank=True, null=True)  # File upload field
    link = models.URLField(max_length=200, blank=True, null=True)  # Link field
    created_at = models.DateTimeField(auto_now_add=True)

#Support
class SupportQuery(models.Model):
    user = models.ForeignKey(CustomUser, null=True, blank=True, on_delete=models.SET_NULL)
    email = models.EmailField()
    phone_number = models.CharField(max_length=15)
    issue_type = models.CharField(max_length=20, choices=[('new', 'New Requirement'), ('existing', 'Existing Requirement')])
    contact_time = models.CharField(max_length=50, blank=True)
    query = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

#College details
class CollegeDetails(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    logo = models.ImageField(upload_to='college_logos/', blank=True, null=True)
    links = models.TextField(blank=True, null=True)
    videos = models.TextField(blank=True, null=True)
    images = models.TextField(blank=True, null=True)


class Subjects(models.Model):
    id =models.AutoField(primary_key=True)
    subject_name = models.CharField(max_length=255)
    course_id = models.ForeignKey(Courses, on_delete=models.CASCADE, default=1) #need to give defauult course
    staff_id = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = models.Manager()

    def __str__(self):
        return self.subject_name

class Students(models.Model):
    id = models.AutoField(primary_key=True)
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    gender = models.CharField(max_length=50)
    profile_pic = models.FileField()
    address = models.TextField()
    mobile = models.CharField(max_length=15,default = 9876543210)  # Add this line for mobile number
    course_id = models.ForeignKey(Courses, on_delete=models.DO_NOTHING, default=1)
    session_year_id = models.ForeignKey(SessionYearModel, null=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = models.Manager()


class Attendance(models.Model):
    # Subject Attendance
    id = models.AutoField(primary_key=True)
    subject_id = models.ForeignKey(Subjects, on_delete=models.DO_NOTHING)
    attendance_date = models.DateField()
    session_year_id = models.ForeignKey(SessionYearModel, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = models.Manager()


class AttendanceReport(models.Model):
    # Individual Student Attendance
    id = models.AutoField(primary_key=True)
    student_id = models.ForeignKey(Students, on_delete=models.DO_NOTHING)
    attendance_id = models.ForeignKey(Attendance, on_delete=models.CASCADE)
    status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = models.Manager()


class LeaveReportStudent(models.Model):
    id = models.AutoField(primary_key=True)
    student_id = models.ForeignKey(Students, on_delete=models.CASCADE)
    leave_date = models.CharField(max_length=255)
    leave_message = models.TextField()
    leave_status = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = models.Manager()


class LeaveReportStaff(models.Model):
    id = models.AutoField(primary_key=True)
    staff_id = models.ForeignKey(Staffs, on_delete=models.CASCADE)
    leave_date = models.CharField(max_length=255)
    leave_message = models.TextField()
    leave_status = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = models.Manager()


class FeedBackStudent(models.Model):
    id = models.AutoField(primary_key=True)
    student_id = models.ForeignKey(Students, on_delete=models.CASCADE)
    feedback = models.TextField()
    feedback_reply = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = models.Manager()


class FeedBackStaffs(models.Model):
    id = models.AutoField(primary_key=True)
    staff_id = models.ForeignKey(Staffs, on_delete=models.CASCADE)
    feedback = models.TextField()
    feedback_reply = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = models.Manager()



class NotificationStudent(models.Model):
    id = models.AutoField(primary_key=True)
    student_id = models.ForeignKey(Students, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = models.Manager()


class NotificationStaffs(models.Model):
    id = models.AutoField(primary_key=True)
    stafff_id = models.ForeignKey(Staffs, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = models.Manager()


class StudentResult(models.Model):
    id = models.AutoField(primary_key=True)
    student_id = models.ForeignKey(Students, on_delete=models.CASCADE)
    subject_id = models.ForeignKey(Subjects, on_delete=models.CASCADE, default=1)
    subject_exam_marks = models.FloatField(default=0)
    subject_assignment_marks = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = models.Manager()

class CurriculumItem(models.Model):
    section = models.CharField(max_length=255)
    subsection_id = models.CharField(max_length=255)
    title = models.CharField(max_length=255,blank = True)
    description = models.TextField(blank = True)
    structure = models.TextField(blank = True)

    def __str__(self):
        return f'{self.section} - {self.title}'
    
class SecondItem(models.Model):
    section = models.CharField(max_length=255)
    subsection_id = models.CharField(max_length=255, blank=True, null=True)
    title = models.CharField(max_length=2000, blank=True)
    description = models.TextField(blank=True)
    structure = models.JSONField(default=dict)
    student_data = models.JSONField(default=list)

    def __str__(self):
        return f'{self.section} - {self.title}'

    def save(self, *args, **kwargs):
        if isinstance(self.structure, str):
            self.structure = json.loads(self.structure)
        if isinstance(self.student_data, str):
            self.student_data = json.loads(self.student_data)
        super().save(*args, **kwargs)
    
class ThirdItem(models.Model):
    section = models.CharField(max_length=255)
    subsection_id = models.CharField(max_length=255)
    title = models.CharField(max_length = 2000,blank = True)
    description = models.TextField(blank = True)
    upload_text = models.CharField(max_length=255, default="Upload")
    generate_text = models.CharField(max_length=255, default="Generate")
    progress_percentage = models.IntegerField(default=0)  # New field for progress percentage
    points = models.CharField(max_length=5,blank= True)


    def __str__(self):
        return f'{self.section} - {self.title}'
    
class FourthItem(models.Model):
    section = models.CharField(max_length=255)
    subsection_id = models.CharField(max_length=255)
    title = models.CharField(max_length = 2000,blank = True)
    description = models.TextField(blank = True)
    upload_text = models.CharField(max_length=255, default="Upload")
    generate_text = models.CharField(max_length=255, default="Generate")
    progress_percentage = models.IntegerField(default=0)  # New field for progress percentage
    points = models.CharField(max_length=5,blank= True)


    def __str__(self):
        return f'{self.section} - {self.title}'
    
class FifthItem(models.Model):
    section = models.CharField(max_length=255)
    subsection_id = models.CharField(max_length=255)
    title = models.CharField(max_length = 2000,blank = True)
    description = models.TextField(blank = True)
    upload_text = models.CharField(max_length=255, default="Upload")
    generate_text = models.CharField(max_length=255, default="Generate")
    progress_percentage = models.IntegerField(default=0)  # New field for progress percentage
    points = models.CharField(max_length=5,blank= True)


    def __str__(self):
        return f'{self.section} - {self.title}'
    
class SixthItem(models.Model):
    section = models.CharField(max_length=255)
    subsection_id = models.CharField(max_length=255)
    title = models.CharField(max_length = 2000,blank = True)
    description = models.TextField(blank = True)
    upload_text = models.CharField(max_length=255, default="Upload")
    generate_text = models.CharField(max_length=255, default="Generate")
    progress_percentage = models.IntegerField(default=0)  # New field for progress percentage
    points = models.CharField(max_length=5,blank= True)


    def __str__(self):
        return f'{self.section} - {self.title}'
    
class SeventhItem(models.Model):
    section = models.CharField(max_length=255)
    subsection_id = models.CharField(max_length=255)
    title = models.CharField(max_length = 2000,blank = True)
    description = models.TextField(blank = True)
    upload_text = models.CharField(max_length=255, default="Upload")
    generate_text = models.CharField(max_length=255, default="Generate")
    progress_percentage = models.IntegerField(default=0)  # New field for progress percentage
    points = models.CharField(max_length=5,blank= True)


    def __str__(self):
        return f'{self.section} - {self.title}'
    

# MARKS and RESULT models of staff:
from django.utils import timezone
from datetime import datetime

# class Examination(models.Model):
#     exam_name = models.CharField(max_length=255)
#     associated_courses = models.ManyToManyField('Courses')
#     subjects = models.ManyToManyField('Subjects')
#     exam_date = models.DateField(default= datetime.now )
#     exam_time = models.TimeField(default= datetime.now)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     objects = models.Manager()

#     def __str__(self):
#         return self.exam_name

from django.utils import timezone
from datetime import datetime

class Examination(models.Model):
    exam_name = models.CharField(max_length=255)
    courses = models.ManyToManyField(Courses)  # Allows multiple courses
    subjects = models.ManyToManyField(Subjects)  # Allows multiple subjects
    start_date = models.DateField(default= datetime.now)  # Start date of the exam period
    end_date = models.DateField(default= datetime.now)  # End date of the exam period
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.exam_name


class Marks(models.Model):
    student = models.ForeignKey('Students', on_delete=models.CASCADE)
    examination = models.ForeignKey(Examination, on_delete=models.CASCADE)
    subject = models.ForeignKey('Subjects', on_delete=models.CASCADE)
    marks_obtained = models.FloatField()
    max_marks = models.FloatField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = models.Manager()

    def __str__(self):
        return f"{self.student.admin.first_name} - {self.subject.subject_name} - {self.marks_obtained}/{self.max_marks}"


    
# class NaacItem(models.Model):
#     section = models.CharField(max_length=255)
#     subsection_id = models.CharField(max_length=255)
#     title = models.CharField(max_length=255, blank=True, null=True)
#     description = models.TextField(blank=True, null=True)
#     upload_text = models.CharField(max_length=255, default="Upload")
#     generate_text = models.CharField(max_length=255, default="Generate")
#     parent = models.ForeignKey('self', null=True, blank=True, related_name='subsections', on_delete=models.CASCADE)

#     def __str__(self):
#         return f'{self.section} - {self.title}'


#Creating Django Signals

# It's like trigger in database. It will run only when Data is Added in CustomUser model

@receiver(post_save, sender=CustomUser)
# Now Creating a Function which will automatically insert data in HOD, Staff or Student
def create_user_profile(sender, instance, created, **kwargs):
    # if Created is true (Means Data Inserted)
    if created:
        # Check the user_type and insert the data in respective tables
        if instance.user_type == 1:
            AdminHOD.objects.create(admin=instance)
        if instance.user_type == 2:
            Staffs.objects.create(admin=instance)
        if instance.user_type == 3:
            Students.objects.create(admin=instance, course_id=Courses.objects.get(id=1), session_year_id=SessionYearModel.objects.get(id=1), address="", profile_pic="", gender="")
    

@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    if instance.user_type == 1:
        instance.adminhod.save()
    if instance.user_type == 2:
        instance.staffs.save()
    if instance.user_type == 3:
        instance.students.save()
from django.db import models
import json
#from django.db import models
#import json

def get_default_user():
    User = get_user_model()
    return User.objects.first().id  # Returns the ID of the first user in the database

class StudentOutgoingData(models.Model):
    unique_id = models.CharField(max_length=255, unique=True,null=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    ss_id = models.CharField(max_length=50, null=True, blank=True)
    data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"User: {self.user.username if self.user else 'Anonymous'}, SS ID: {self.ss_id}"

    class Meta:
        ordering = ['-created_at']












