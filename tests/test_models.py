# tests/test_models.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from core.models.department import Department
from core.models.template import Template, TemplateData
from core.constants import UserRoles, ApprovalStatus, TemplateType

User = get_user_model()

class UserModelTest(TestCase):
    def setUp(self):
        self.department = Department.objects.create(
            name='Computer Science',
            code='CS'
        )
        
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            role=UserRoles.FACULTY,
            department=self.department
        )

    def test_user_creation(self):
        self.assertEqual(self.user.get_full_name(), 'Test User')
        self.assertEqual(self.user.department, self.department)
        self.assertEqual(self.user.role, UserRoles.FACULTY)

    def test_user_properties(self):
        self.assertFalse(self.user.is_iqac_director)
        self.user.role = UserRoles.IQAC_DIRECTOR
        self.user.save()
        self.assertTrue(self.user.is_iqac_director)

class TemplateModelTest(TestCase):
    def setUp(self):
        self.template = Template.objects.create(
            title='Test Template',
            file_code='TEST001',
            type=TemplateType.CRITERION_1,
            columns=['col1', 'col2']
        )

    def test_template_creation(self):
        self.assertEqual(str(self.template), 'TEST001 - Test Template')
        self.assertEqual(self.template.columns, ['col1', 'col2'])

class TemplateDataModelTest(TestCase):
    def setUp(self):
        self.department = Department.objects.create(
            name='Computer Science',
            code='CS'
        )
        
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.template = Template.objects.create(
            title='Test Template',
            file_code='TEST001',
            type=TemplateType.CRITERION_1,
            columns=['col1', 'col2']
        )
        
        self.template_data = TemplateData.objects.create(
            template=self.template,
            department=self.department,
            academic_year='2023-24',
            data={'col1': 'value1', 'col2': 'value2'},
            submitted_by=self.user
        )

    def test_template_data_creation(self):
        self.assertEqual(self.template_data.status, ApprovalStatus.DRAFT)
        self.assertEqual(self.template_data.data['col1'], 'value1')