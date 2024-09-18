from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CurriculumItem,SecondItem,ThirdItem,FourthItem,FifthItem,SixthItem,SeventhItem, CustomUser, SessionYearModel,AdminHOD,NAAC,Parent, Staffs, Courses, Subjects, Students, Attendance, AttendanceReport, LeaveReportStudent, LeaveReportStaff, FeedBackStudent, FeedBackStaffs, NotificationStudent, NotificationStaffs
from .models import Announcement

# Register your models here.

class UserModel(UserAdmin):
    # Define the fields to be displayed in the list view
    list_display = ('username', 'email', 'mobile', 'user_type', 'is_staff', 'is_active')

    # Optionally, define fields to be used for searching
    search_fields = ('username', 'email', 'mobile', 'user_type')

    # Optionally, define which fields can be filtered on
    list_filter = ('is_staff', 'is_active', 'user_type')

    # Optionally, define which fields are shown in detail view
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'mobile', 'user_type')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    # Optionally, define which fields are used for adding new users
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'mobile', 'user_type', 'password1', 'password2')}
        ),
    )

admin.site.register(CustomUser, UserModel)
admin.site.register(Announcement)

"""
class UserModel(UserAdmin):
    # Define the fields to be displayed in the list view
    list_display = ('username', 'email', 'mobile', 'is_staff', 'is_active')

    # Optionally, define fields to be used for searching
    search_fields = ('username', 'email', 'mobile')

    # Optionally, define which fields can be filtered on
    list_filter = ('is_staff', 'is_active')

    # Optionally, define which fields are shown in detail view
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'mobile')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    # Optionally, define which fields are used for adding new users
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'mobile', 'password1', 'password2')}
        ),
    )

admin.site.register(CustomUser, UserModel)
"""

admin.site.register(AdminHOD)
admin.site.register(Parent)
admin.site.register(NAAC)
admin.site.register(Staffs)
admin.site.register(Courses)
admin.site.register(Subjects)
admin.site.register(Students)
admin.site.register(Attendance)
admin.site.register(AttendanceReport)
admin.site.register(LeaveReportStudent)
admin.site.register(LeaveReportStaff)
admin.site.register(FeedBackStudent)
admin.site.register(FeedBackStaffs)
admin.site.register(NotificationStudent)
admin.site.register(NotificationStaffs)
admin.site.register(SessionYearModel)
admin.site.register(CurriculumItem)
admin.site.register(SecondItem)
admin.site.register(ThirdItem)
admin.site.register(FourthItem)
admin.site.register(FifthItem)
admin.site.register(SixthItem)
admin.site.register(SeventhItem)


# class NaacItemAdmin(admin.ModelAdmin):
#     list_display = ('section', 'subsection_id', 'title', 'description', 'parent')
#     search_fields = ('section', 'subsection_id', 'title', 'description')
#     list_filter = ('parent',)
#     fields = ('section', 'subsection_id', 'title', 'description', 'upload_text', 'generate_text', 'parent')

#     def formfield_for_foreignkey(self, db_field, request, **kwargs):
#         if db_field.name == "parent":
#             if 'instance' in kwargs:
#                 kwargs['queryset'] = NaacItem.objects.exclude(id=kwargs['instance'].id)
#             else:
#                 kwargs['queryset'] = NaacItem.objects.all()
#         return super().formfield_for_foreignkey(db_field, request, **kwargs)

# admin.site.register(NaacItem,NaacItemAdmin)



