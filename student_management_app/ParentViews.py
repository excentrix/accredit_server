from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import messages
from django.core.files.storage import FileSystemStorage #To upload Profile Picture
# will store media or photos
from django.urls import reverse
import datetime # To Parse input DateTime into Python Date Time Object

from .models import CustomUser, Announcement, Staffs,Parent, Courses, Subjects, Students, Attendance, AttendanceReport, LeaveReportStudent, FeedBackStudent, StudentResult


def parent_home(request):
    print("Parent Dashboard")
    print(request.user.id)
    print(request.user.id)
    parent_obj = Parent.objects.get(admin=request.user.id)
    print("Here")
    total_attendance =   AttendanceReport.objects.filter(student_id=parent_obj).count()
    attendance_present = AttendanceReport.objects.filter(student_id=parent_obj, status=True).count()
    attendance_absent =  AttendanceReport.objects.filter(student_id=parent_obj, status=False).count()

    course_obj = Courses.objects.get(id=parent_obj.course_id.id)
    total_subjects = Subjects.objects.filter(course_id=course_obj).count()

    subject_name = []
    data_present = []
    data_absent = []
    subject_data = Subjects.objects.filter(course_id=parent_obj.course_id)
    for subject in subject_data:
        attendance = Attendance.objects.filter(subject_id=subject.id)
        attendance_present_count = AttendanceReport.objects.filter(attendance_id__in=attendance, status=True, student_id=student_obj.id).count()
        attendance_absent_count = AttendanceReport.objects.filter(attendance_id__in=attendance, status=False, student_id=student_obj.id).count()
        subject_name.append(subject.subject_name)
        data_present.append(attendance_present_count)
        data_absent.append(attendance_absent_count)
    
    context={
        "total_attendance": total_attendance,
        "attendance_present": attendance_present,
        "attendance_absent": attendance_absent,
        "total_subjects": total_subjects,
        "subject_name": subject_name,
        "data_present": data_present,
        "data_absent": data_absent
    }
    return render(request, "parent_template/parent_home_template.html")