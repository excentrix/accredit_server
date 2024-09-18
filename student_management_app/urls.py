from django.contrib import admin
from django.urls import path, include
from . import views
from .import HodViews, StaffViews, StudentViews, naacViews,ParentViews
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name="home"),
    path('contact', views.contact, name="contact"),
    path('login', views.loginUser, name="login"),
    path('logout_user', views.logout_user, name="logout_user"),
    path('registration', views.registration, name="registration"),
    path('doLogin', views.doLogin, name="doLogin"),
    path('doRegistration', views.doRegistration, name="doRegistration"),
    path('send-otp/', views.send_otp_view, name='send_otp_view'),
    path('verify-otp/', views.verify_otp_view, name='verify_otp_view'),
    
    
    
      # URLS for Student
    path('student_home/', StudentViews.student_home, name="student_home"),
    path('student_view_attendance/', StudentViews.student_view_attendance, name="student_view_attendance"),
    path('student_view_attendance_post/', StudentViews.student_view_attendance_post, name="student_view_attendance_post"),
    path('student_apply_leave/', StudentViews.student_apply_leave, name="student_apply_leave"),
    path('student_apply_leave_save/', StudentViews.student_apply_leave_save, name="student_apply_leave_save"),
    path('student_feedback/', StudentViews.student_feedback, name="student_feedback"),
    path('student_feedback_save/', StudentViews.student_feedback_save, name="student_feedback_save"),
    path('student_profile/', StudentViews.student_profile, name="student_profile"),
    path('student_profile_update/', StudentViews.student_profile_update, name="student_profile_update"),
    path('student_view_result/', StudentViews.student_view_result, name="student_view_result"),


     # URLS for Staff
    path('staff_home/', StaffViews.staff_home, name="staff_home"),
    path('staff_take_attendance/', StaffViews.staff_take_attendance, name="staff_take_attendance"),
    path('get_students/', StaffViews.get_students, name="get_students"),
    path('save_attendance_data/', StaffViews.save_attendance_data, name="save_attendance_data"),
    path('staff_update_attendance/', StaffViews.staff_update_attendance, name="staff_update_attendance"),
    path('get_attendance_dates/', StaffViews.get_attendance_dates, name="get_attendance_dates"),
    path('get_attendance_student/', StaffViews.get_attendance_student, name="get_attendance_student"),
    path('update_attendance_data/', StaffViews.update_attendance_data, name="update_attendance_data"),
    path('staff_apply_leave/', StaffViews.staff_apply_leave, name="staff_apply_leave"),
    path('staff_apply_leave_save/', StaffViews.staff_apply_leave_save, name="staff_apply_leave_save"),
    path('staff_feedback/', StaffViews.staff_feedback, name="staff_feedback"),
    path('staff_feedback_save/', StaffViews.staff_feedback_save, name="staff_feedback_save"),
    path('staff_profile/', StaffViews.staff_profile, name="staff_profile"),
    path('staff_profile_update/', StaffViews.staff_profile_update, name="staff_profile_update"),
    path('staff_add_result/', StaffViews.staff_add_result, name="staff_add_result"),
    path('staff_add_result_save/', StaffViews.staff_add_result_save, name="staff_add_result_save"),
    
    # URL for Admin
    path('admin_home/', HodViews.admin_home, name="admin_home"),
    path('add_staff/', HodViews.add_staff, name="add_staff"),
    path('add_staff_save/', HodViews.add_staff_save, name="add_staff_save"),
    path('manage_staff/', HodViews.manage_staff, name="manage_staff"),
    path('edit_staff/<staff_id>/', HodViews.edit_staff, name="edit_staff"),
    path('edit_staff_save/', HodViews.edit_staff_save, name="edit_staff_save"),
    path('delete_staff/<staff_id>/', HodViews.delete_staff, name="delete_staff"),
    path('add_course/', HodViews.add_course, name="add_course"),
    path('add_course_save/', HodViews.add_course_save, name="add_course_save"),
    path('manage_course/', HodViews.manage_course, name="manage_course"),
    path('edit_course/<course_id>/', HodViews.edit_course, name="edit_course"),
    path('edit_course_save/', HodViews.edit_course_save, name="edit_course_save"),
    path('delete_course/<course_id>/', HodViews.delete_course, name="delete_course"),
    path('manage_session/', HodViews.manage_session, name="manage_session"),
    path('add_session/', HodViews.add_session, name="add_session"),
    path('add_session_save/', HodViews.add_session_save, name="add_session_save"),
    path('edit_session/<session_id>', HodViews.edit_session, name="edit_session"),
    path('edit_session_save/', HodViews.edit_session_save, name="edit_session_save"),
    path('delete_session/<session_id>/', HodViews.delete_session, name="delete_session"),
    path('add_student/', HodViews.add_student, name="add_student"),
    path('add_student_save/', HodViews.add_student_save, name="add_student_save"),
    path('edit_student/<student_id>', HodViews.edit_student, name="edit_student"),
    path('edit_student_save/', HodViews.edit_student_save, name="edit_student_save"),
    path('manage_student/', HodViews.manage_student, name="manage_student"),
    path('delete_student/<student_id>/', HodViews.delete_student, name="delete_student"),
    path('add_subject/', HodViews.add_subject, name="add_subject"),
    path('add_subject_save/', HodViews.add_subject_save, name="add_subject_save"),
    path('manage_subject/', HodViews.manage_subject, name="manage_subject"),
    path('edit_subject/<subject_id>/', HodViews.edit_subject, name="edit_subject"),
    path('edit_subject_save/', HodViews.edit_subject_save, name="edit_subject_save"),
    path('delete_subject/<subject_id>/', HodViews.delete_subject, name="delete_subject"),
    path('check_email_exist/', HodViews.check_email_exist, name="check_email_exist"),
    path('check_username_exist/', HodViews.check_username_exist, name="check_username_exist"),
    path('student_feedback_message/', HodViews.student_feedback_message, name="student_feedback_message"),
    path('student_feedback_message_reply/', HodViews.student_feedback_message_reply, name="student_feedback_message_reply"),
    path('staff_feedback_message/', HodViews.staff_feedback_message, name="staff_feedback_message"),
    path('staff_feedback_message_reply/', HodViews.staff_feedback_message_reply, name="staff_feedback_message_reply"),
    path('student_leave_view/', HodViews.student_leave_view, name="student_leave_view"),
    path('student_leave_approve/<leave_id>/', HodViews.student_leave_approve, name="student_leave_approve"),
    path('student_leave_reject/<leave_id>/', HodViews.student_leave_reject, name="student_leave_reject"),
    path('staff_leave_view/', HodViews.staff_leave_view, name="staff_leave_view"),
    path('staff_leave_approve/<leave_id>/', HodViews.staff_leave_approve, name="staff_leave_approve"),
    path('staff_leave_reject/<leave_id>/', HodViews.staff_leave_reject, name="staff_leave_reject"),
    path('admin_view_attendance/', HodViews.admin_view_attendance, name="admin_view_attendance"),
    path('admin_get_attendance_dates/', HodViews.admin_get_attendance_dates, name="admin_get_attendance_dates"),
    path('admin_get_attendance_student/', HodViews.admin_get_attendance_student, name="admin_get_attendance_student"),
    path('admin_profile/', HodViews.admin_profile, name="admin_profile"),
    path('admin_profile_update/', HodViews.admin_profile_update, name="admin_profile_update"),
    path('view_staff/', HodViews.view_staff, name='view_staff'),
    path('view_students/', HodViews.view_students, name='view_students'),
    path('feedback/', HodViews.feedback, name='feedback'),
    path('create_feedback/',HodViews.create_feedback,name='create_feedback'),
    path('form_list1/',HodViews.form_list,name='form_list1'),
    path('create_form1/',HodViews.create_form,name='create_form1'),
    path('display_form1/<int:form_id>/', HodViews.display_form, name='display_form1'),

    #URLs for bulk upload students

    path('bulk_upload/', HodViews.bulk_upload, name="bulk_upload"),
    path('download_sample_template/', HodViews.download_sample_template, name="download_sample_template"),

    #Staffs
    path('bulk_upload_staff/', HodViews.bulk_upload_staff, name="bulk_upload_staff"),
    path('download_sample_staff_template/', HodViews.download_sample_staff_template, name='download_sample_staff_template'),

    # path('download_sample_template/', HodViews.download_sample_template, name="download_sample_template"),
    # path('bulk_upload_students/', HodViews.bulk_upload_students, name="bulk_upload_students"),
    #path('bulk_upload_students/', HodViews.bulk_upload_students_save, name="bulk_upload_students"),
    # path('bulk_upload_students/', HodViews.bulk_upload_students, name="bulk_upload_students"),
    # path('download_sample_template/', HodViews.download_sample_template, name="download_sample_template"),

    path('naac_home/', naacViews.naac_home, name="naac_home"),

    #URL for parent:

    path('parent_home/', ParentViews.parent_home, name="parent_home"),

    #Naac Pointers
    path('test/',naacViews.test,name = "test"),
    path('curriculum/',naacViews.curriculum,name = "curriculum"),
    path('update-progress/<int:item_id>/', naacViews.update_progress, name='update_progress'),

    path('teaching2/',naacViews.teaching2,name = "teaching2"),
    path('update-progress2/<int:item_id>/', naacViews.update_progress2, name='update_progress2'),

    path('four/',naacViews.four,name = "four"),
    path('update-progress4/<int:item_id>/', naacViews.update_progress4, name='update_progress4'),

    path('five/',naacViews.five,name = "five"),
    path('update-progress5/<int:item_id>/', naacViews.update_progress5, name='update_progress5'),

    path('six/',naacViews.six,name = "six"),
    path('update-progress6/<int:item_id>/', naacViews.update_progress6, name='update_progress6'),
    
    path('research3/',naacViews.research3,name = "research3"),
    path('update-progress3/<int:item_id>/', naacViews.update_progress3, name='update_progress3'),

    path('seven/',naacViews.seven,name = "seven"),
    path('update-progress7/<int:item_id>/', naacViews.update_progress7, name='update_progress7'),

    #Announcements
    path('announcements/',naacViews.announcements,name = "announcements"),
    path('announcements1/',HodViews.announcements,name = "announcements1"),
    path('announcements2/',StaffViews.announcements,name = "announcements2"),
    path('announcements3/',StudentViews.announcements,name = "announcements3"),
    path('add_announcements/', naacViews.add_announcements, name="add_announcements"),
    path('add_announcements1/', HodViews.add_announcements, name="add_announcements1"),
    path('announcements1/edit/<int:pk>/', HodViews.edit_announcements, name='edit_announcements'),
    path('announcements1/delete/<int:pk>/', HodViews.delete_announcements, name='delete_announcements'),

    path('college_details/', HodViews.college_details, name="college_details"),

    #Support

    path('support/', HodViews.support_page, name='support_page'),
    path('support1/', naacViews.support_page1, name='support_page1'),


    path('ss1_1/', naacViews.ss1_1, name='ss1_1'),
    path('ss1_2/', naacViews.ss1_2, name='ss1_2'),
    path('ss1_3/', naacViews.ss1_3, name='ss1_3'),

    #Form Builder
    path('create_form/', naacViews.create_form, name='create_form'),
    path('form_list/', naacViews.form_list, name='form_list'),
    path('<int:form_id>/', naacViews.display_form, name='display_form'),
    
    #File upload
    path('upload/', naacViews.upload_file, name='upload'),  # Set the default route to upload_file view
    path('upload/success/', naacViews.upload_success, name='upload_success'),
    path('files/', naacViews.file_list, name='file_list'), 

    #Bulk upload
    path('download-template/', naacViews.download_excel_template, name='download_template'),
    path('upload_bulk/', naacViews.upload_excel_file, name='upload_excel'),
    path('students/', naacViews.list_students, name='student_list'),


    #MARKS and RESULT in staff

    path('examinations/', StaffViews.examination_list, name='examination_list'),
    path('examinations/create/', StaffViews.create_examination, name='create_examination'),
    path('examinations/edit/<int:exam_id>/', StaffViews.edit_examination, name='edit_examination'),
    path('examinations/delete/<int:exam_id>/', StaffViews.delete_examination, name='delete_examination'),

    path('marks/', StaffViews.marks_list, name='marks_list'),
    path('marks/enter/<int:exam_id>/<int:course_id>/', StaffViews.enter_marks_individual, name='enter_marks_individual'),
    path('enter_marks/<int:exam_id>/<int:course_id>/', StaffViews.enter_marks_individual, name='enter_marks_individual'),
    path('marks/bulk_upload/<int:exam_id>/<int:course_id>/', StaffViews.bulk_upload_marks, name='bulk_upload_marks'),
    path('enter_marks/<int:exam_id>/', StaffViews.enter_marks_individual, name='enter_marks_individual'),



]+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



