from datetime import datetime, timedelta
import random

def generate_programme_data():
    programmes = [
        ('BCS', 'Bachelor of Computer Science'),
        ('BEE', 'Bachelor of Electrical Engineering'),
        ('BME', 'Bachelor of Mechanical Engineering'),
        ('BCE', 'Bachelor of Civil Engineering'),
        ('MBA', 'Master of Business Administration')
    ]
    return random.choice(programmes)

def generate_course_data():
    courses = [
        {
            'name': 'Advanced Python Programming',
            'code': 'CS301',
            'activities': 'Python programming, Web development, Data analysis, Machine Learning applications',
        },
        {
            'name': 'Digital Marketing',
            'code': 'MKT202',
            'activities': 'Social media marketing, SEO, Content marketing, Analytics',
        },
        {
            'name': 'Entrepreneurship Fundamentals',
            'code': 'ENT101',
            'activities': 'Business planning, Market research, Financial management, Leadership skills',
        },
        {
            'name': 'IoT Systems',
            'code': 'IOT301',
            'activities': 'Sensor programming, Network protocols, Data collection, Edge computing',
        }
    ]
    return random.choice(courses)

def generate_value_added_course_data():
    courses = [
        {
            'name': 'Professional Communication Skills',
            'code': 'VAC101',
            'times_offered': 2,
            'duration': 45,
            'enrolled': random.randint(30, 100),
        },
        {
            'name': 'Data Science Bootcamp',
            'code': 'VAC202',
            'times_offered': 1,
            'duration': 60,
            'enrolled': random.randint(25, 80),
        },
        {
            'name': 'Soft Skills Development',
            'code': 'VAC103',
            'times_offered': 3,
            'duration': 40,
            'enrolled': random.randint(40, 120),
        }
    ]
    course = random.choice(courses)
    course['completed'] = random.randint(
        int(course['enrolled'] * 0.7),
        course['enrolled']
    )
    return course