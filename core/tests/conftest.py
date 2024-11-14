# core/tests/conftest.py
import pytest
from core.models import Template

@pytest.fixture
def template_1_1():
    return Template.objects.create(
        code="1.1",
        name="Number of programmes offered during the year",
        headers=["1.1. Number of programmes offered during the year"],
        columns=[
            {
                "name": "programme_code",
                "display_name": "Programme Code",
                "type": "string"
            },
            {
                "name": "programme_name",
                "display_name": "Programme Name",
                "type": "string"
            }
        ]
    )

@pytest.fixture
def template_1_1_3():
    return Template.objects.create(
        code="1.1.3",
        name="Details of courses offered",
        headers=[
            "1.1.3 Details of courses offered by the institution that focus on employability/ entrepreneurship/ skill development during the year.",
            "1.2.1 Details of courses introduced across all programmes offered during the year"
        ],
        columns=[
            {
                "name": "course_name",
                "display_name": "Name of the Course",
                "type": "string"
            },
            {
                "name": "course_code",
                "display_name": "Course Code",
                "type": "string"
            },
            {
                "name": "activities",
                "display_name": "Activities/Content with a direct bearing on Employability/ Entrepreneurship/ Skill development",
                "type": "text"
            },
            {
                "name": "document_link",
                "display_name": "Link to the relevant document",
                "type": "url"
            }
        ]
    )