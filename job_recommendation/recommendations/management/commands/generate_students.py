import random
import json
from django.core.management.base import BaseCommand
from faker import Faker
from recommendations.models import Student  # Import the Student model

# Initialize Faker
fake = Faker()

courses = [
    'Programming Fundamentals', 'Data Structures', 'Algorithms', 'Database Systems', 
    'Operating Systems', 'Computer Networks', 'Software Engineering', 
    'Artificial Intelligence', 'Machine Learning', 'Computer Vision', 
    'Cybersecurity', 'Cloud Computing', 'Mobile App Development', 
    'Web Development', 'Blockchain Technology', 'Big Data Analytics', 
    'Internet of Things (IoT)', 'Computer Graphics', 'Parallel Computing',
    'Human-Computer Interaction'
]


# List of possible skills and career aspirations
skills_list = ['Python', 'Java', 'C++', 'Data Analysis', 'Machine Learning', 'AI', 'Web Development', 'Software Engineering']
career_goals = ['Software Engineer', 'Data Scientist', 'Product Manager', 'Researcher', 'Civil Engineer', 'Graphic Designer']

# Function to generate random grades
def generate_grades():
    grades = {course: random.choice(['A', 'B', 'C', 'D', 'F']) for course in courses}
    return json.dumps(grades)  # Store as JSON

# Function to generate random extracurricular activities
def generate_extracurricular_activities():
    activities = ['Sports', 'Music', 'Drama', 'Volunteering', 'Tech Club', 'Art Club']
    return random.choice(activities)

# Function to generate random career aspirations
def generate_career_aspiration():
    return random.choice(career_goals)

# Command class for Django management command
class Command(BaseCommand):
    help = "Generate dummy student data"

    def handle(self, *args, **kwargs):
        num_students = 100  # Adjust this number as needed

        students = []
        for _ in range(num_students):
            student = Student(
                name=fake.name(),
                student_id=fake.unique.random_number(digits=6),
                grades=generate_grades(),
                skills=', '.join(random.sample(skills_list, k=3)),  # Store as comma-separated string
                interests=random.choice(['Software Development', 'Data Science', 'Engineering']),
            )
            students.append(student)

        # Bulk insert all students
        Student.objects.bulk_create(students)

        self.stdout.write(self.style.SUCCESS(f"Successfully created {num_students} students!"))
