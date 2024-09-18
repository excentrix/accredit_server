from django import forms
from .models import Courses, SessionYearModel,UploadedFile
from .models import Announcement
from .models import SupportQuery

#OTP Verification form
from django.core.validators import RegexValidator

class PhoneNumberForm(forms.Form):
        mobile = forms.CharField(
        max_length=16,
        validators=[RegexValidator(r'^\+?91\d{10}$', 'Enter a valid phone number.')]
    )

class OTPForm(forms.Form):
    otp = forms.CharField(max_length=6)

#class PasswordForm(forms.Form):
 #   password = forms.CharField(widget=forms.PasswordInput, max_length=128)



#File upload:
class UploadFileForm(forms.ModelForm):
    class Meta:
        model = UploadedFile
        fields = ['file']


class DateInput(forms.DateInput):
    input_type = "date"

#Bulk upload:
class UploadFileForm(forms.Form):
    file = forms.FileField()

#Add Announcements:

class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['title', 'content', 'announced_by', 'audience', 'file', 'link']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super(AnnouncementForm, self).__init__(*args, **kwargs)
        self.fields['announced_by'].required = True

class EditAnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['title', 'content', 'announced_by', 'audience', 'file', 'link']


class SupportQueryForm(forms.ModelForm):
    class Meta:
        model = SupportQuery
        fields = ['issue_type', 'query', 'email', 'phone_number']  # Include email and phone_number
        widgets = {
            'issue_type': forms.Select(attrs={'class': 'form-control'}),
            'query': forms.Textarea(attrs={'placeholder': 'Describe your issue or question here...', 'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Your email address', 'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'placeholder': 'Your phone number', 'class': 'form-control'}),
        }
    
    name = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'placeholder': 'Your name', 'class': 'form-control'}))

#College Details
from .models import CollegeDetails

class CollegeDetailsForm(forms.ModelForm):
    class Meta:
        model = CollegeDetails
        fields = ['name', 'logo', 'links', 'videos', 'images']
        widgets = {
            'links': forms.Textarea(attrs={'rows': 3}),
            'videos': forms.Textarea(attrs={'rows': 3}),
            'images': forms.Textarea(attrs={'rows': 3}),
        }


from django import forms
from django.core.validators import RegexValidator

class AddStudentForm(forms.Form):
    username = forms.CharField(
        label="Username",
        max_length=50,
        widget=forms.TextInput(attrs={"class":"form-control"}),
        validators=[RegexValidator(regex='^[a-zA-Z0-9]*$', message='Username must be alphanumeric')]
    )
    first_name = forms.CharField(
        label="First Name",
        max_length=50,
        widget=forms.TextInput(attrs={"class":"form-control"}),
        validators=[RegexValidator(regex='^[a-zA-Z]*$', message='First name must contain only letters')]
    )
    last_name = forms.CharField(
        label="Last Name",
        max_length=50,
        widget=forms.TextInput(attrs={"class":"form-control"}),
        validators=[RegexValidator(regex='^[a-zA-Z]*$', message='Last name must contain only letters')]
    )
    mobile = forms.CharField(
        label="Mobile",
        max_length=15,
        widget=forms.TextInput(attrs={"class":"form-control"}),
        validators=[RegexValidator(regex='^\d+$', message='Mobile number must contain only digits')]
    )
    email = forms.EmailField(
        label="Email",
        max_length=50,
        widget=forms.EmailInput(attrs={"class":"form-control"})
    )
    password = forms.CharField(
        label="Password",
        max_length=50,
        widget=forms.PasswordInput(attrs={"class":"form-control"})
    )
    address = forms.CharField(
        label="Address",
        max_length=100,
        widget=forms.Textarea(attrs={"class":"form-control"})
    )

    # For Displaying Courses
    try:
        courses = Courses.objects.all()
        course_list = [(course.id, course.course_name) for course in courses]
    except:
        course_list = []

    # For Displaying Session Years
    try:
        session_years = SessionYearModel.objects.all()
        session_year_list = [(session_year.id, f"{session_year.session_start_year} to {session_year.session_end_year}") for session_year in session_years]
    except:
        session_year_list = []

    gender_list = (
        ('Male', 'Male'),
        ('Female', 'Female')
    )

    course_id = forms.ChoiceField(
        label="Course",
        choices=course_list,
        widget=forms.Select(attrs={"class":"form-control"})
    )
    gender = forms.ChoiceField(
        label="Gender",
        choices=gender_list,
        widget=forms.Select(attrs={"class":"form-control"})
    )
    session_year_id = forms.ChoiceField(
        label="Session Year",
        choices=session_year_list,
        widget=forms.Select(attrs={"class":"form-control"})
    )
    profile_pic = forms.FileField(
        label="Profile Pic",
        required=False,
        widget=forms.FileInput(attrs={"class":"form-control"})
    )

#Forms for MARKS and RESULT in staff:

from student_management_app.models import Examination, Courses, Subjects
from django.core.exceptions import ValidationError


class CreateExaminationForm(forms.ModelForm):
    courses = forms.ModelMultipleChoiceField(queryset=Courses.objects.all(), widget=forms.CheckboxSelectMultiple)
    subjects = forms.ModelMultipleChoiceField(queryset=Subjects.objects.all(), widget=forms.CheckboxSelectMultiple)
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = Examination
        fields = ['exam_name', 'courses', 'subjects', 'start_date', 'end_date']

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date and start_date > end_date:
            raise ValidationError("End date must be after the start date.")

        return cleaned_data

class ExaminationForm(forms.ModelForm):
    courses = forms.ModelMultipleChoiceField(queryset=Courses.objects.all(), widget=forms.CheckboxSelectMultiple)
    subjects = forms.ModelMultipleChoiceField(queryset=Subjects.objects.all(), widget=forms.CheckboxSelectMultiple)

    class Meta:
        model = Examination
        fields = ['exam_name', 'courses', 'subjects', 'start_date', 'end_date']

class BulkUploadMarksForm(forms.Form):
    marks_file = forms.FileField(label="Upload CSV/Excel File", required=True)

# from django import forms
# from student_management_app.models import Examination, Courses, Subjects
# from django.core.exceptions import ValidationError

# class CreateExaminationForm(forms.ModelForm):
#     courses = forms.ModelMultipleChoiceField(queryset=Courses.objects.all(), widget=forms.CheckboxSelectMultiple)
#     subjects = forms.ModelMultipleChoiceField(queryset=Subjects.objects.all(), widget=forms.CheckboxSelectMultiple)
#     start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
#     end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

#     class Meta:
#         model = Examination
#         fields = ['exam_name', 'courses', 'subjects', 'start_date', 'end_date']

#     def clean(self):
#         cleaned_data = super().clean()
#         start_date = cleaned_data.get('start_date')
#         end_date = cleaned_data.get('end_date')

#         if start_date and end_date and start_date > end_date:
#             raise ValidationError("End date must be after the start date.")

#         return cleaned_data




# class AddStudentForm(forms.Form):
    
#     username = forms.CharField(label="Username", max_length=50, widget=forms.TextInput(attrs={"class":"form-control"}))
#     first_name = forms.CharField(label="First Name", max_length=50, widget=forms.TextInput(attrs={"class":"form-control"}),required=True)
#     last_name = forms.CharField(label="Last Name", max_length=50, widget=forms.TextInput(attrs={"class":"form-control"}),required=True)
#     mobile = forms.CharField(label="mobile", max_length=12, widget=forms.TextInput(attrs={"class":"form-control"}),required=True)
#     email = forms.EmailField(label="Email", max_length=50, widget=forms.EmailInput(attrs={"class":"form-control"}),required=True)
#     password = forms.CharField(label="Password", max_length=50, widget=forms.PasswordInput(attrs={"class":"form-control"}),required=True)
#     address = forms.CharField(label="Address", max_length=50, widget=forms.TextInput(attrs={"class":"form-control"}))

#     #For Displaying Courses
#     try:
#         courses = Courses.objects.all()
#         course_list = []
#         for course in courses:
#             single_course = (course.id, course.course_name)
#             course_list.append(single_course)
#     except:
#         print("here")
#         course_list = []
    
#     #For Displaying Session Years
#     try:
#         session_years = SessionYearModel.objects.all()
#         session_year_list = []
#         for session_year in session_years:
#             single_session_year = (session_year.id, str(session_year.session_start_year)+" to "+str(session_year.session_end_year))
#             session_year_list.append(single_session_year)
            
#     except:
#         session_year_list = []
    
#     gender_list = (
#         ('Male','Male'),
#         ('Female','Female')
#     )
    
#     course_id = forms.ChoiceField(label="Course", choices=course_list, widget=forms.Select(attrs={"class":"form-control"}))
#     gender = forms.ChoiceField(label="Gender", choices=gender_list, widget=forms.Select(attrs={"class":"form-control"}))
#     session_year_id = forms.ChoiceField(label="Session Year", choices=session_year_list, widget=forms.Select(attrs={"class":"form-control"}))
#     # session_start_year = forms.DateField(label="Session Start", widget=DateInput(attrs={"class":"form-control"}))
#     # session_end_year = forms.DateField(label="Session End", widget=DateInput(attrs={"class":"form-control"}))
#     profile_pic = forms.FileField(label="Profile Pic", required=False, widget=forms.FileInput(attrs={"class":"form-control"}))



class EditStudentForm(forms.Form):
    email = forms.EmailField(label="Email", max_length=50, widget=forms.EmailInput(attrs={"class":"form-control"}))
    password = forms.CharField(label="Password",widget=forms.PasswordInput(attrs={"class": "form-control"}))
    first_name = forms.CharField(label="First Name", max_length=50, widget=forms.TextInput(attrs={"class":"form-control"}))
    last_name = forms.CharField(label="Last Name", max_length=50, widget=forms.TextInput(attrs={"class":"form-control"}))
    username = forms.CharField(label="Username", max_length=50, widget=forms.TextInput(attrs={"class":"form-control"}))
    mobile = forms.CharField(label="mobile", max_length=15, widget=forms.TextInput(attrs={"class":"form-control"}))
    address = forms.CharField(label="Address", max_length=50, widget=forms.TextInput(attrs={"class":"form-control"}))

    #For Displaying Courses
    try:
        courses = Courses.objects.all()
        course_list = []
        for course in courses:
            single_course = (course.id, course.course_name)
            course_list.append(single_course)
    except:
        course_list = []

    #For Displaying Session Years
    try:
        session_years = SessionYearModel.objects.all()
        session_year_list = []
        for session_year in session_years:
            single_session_year = (session_year.id, str(session_year.session_start_year)+" to "+str(session_year.session_end_year))
            session_year_list.append(single_session_year)
            
    except:
        session_year_list = []

    
    gender_list = (
        ('Male','Male'),
        ('Female','Female')
    )
    
    course_id = forms.ChoiceField(label="Course", choices=course_list, widget=forms.Select(attrs={"class":"form-control"}))
    gender = forms.ChoiceField(label="Gender", choices=gender_list, widget=forms.Select(attrs={"class":"form-control"}))
    #session_year_id = forms.ChoiceField(label="Session Year", choices=session_year_list, widget=forms.Select(attrs={"class":"form-control"}))
    # session_start_year = forms.DateField(label="Session Start", widget=DateInput(attrs={"class":"form-control"}))
    # session_end_year = forms.DateField(label="Session End", widget=DateInput(attrs={"class":"form-control"}))
    profile_pic = forms.FileField(label="Profile Pic", required=False, widget=forms.FileInput(attrs={"class":"form-control"}))

