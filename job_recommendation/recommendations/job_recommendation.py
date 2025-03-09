import json
from recommendations.models import Student

# Define job categories with relevant subjects
JOB_MATCHING_CRITERIA = {
    "Software Engineer": ["Programming Fundamentals", "Data Structures", "Algorithms", "Web Development"],
    "AI Engineer": ["Artificial Intelligence", "Machine Learning", "Data Structures", "Computer Vision"],
    "Cybersecurity Analyst": ["Cybersecurity", "Computer Networks", "Operating Systems"],
    "Cloud Engineer": ["Cloud Computing", "Computer Networks", "Big Data Analytics"],
    "Mobile Developer": ["Mobile App Development", "Programming Fundamentals"],
    "Blockchain Developer": ["Blockchain Technology", "Cryptography", "Distributed Systems"]
}

def recommend_jobs(student_id):
    """ Recommend jobs based on student's grades """
    try:
        student = Student.objects.get(student_id=student_id)
        grades = json.loads(student.grades)  # Convert JSON string to dictionary
        recommended_jobs = []

        for job, required_courses in JOB_MATCHING_CRITERIA.items():
            score = sum(1 for course in required_courses if grades.get(course) in ["A", "B"])
            
            if score >= 2:  # If the student has at least 2 strong grades
                recommended_jobs.append(job)

        return recommended_jobs if recommended_jobs else ["No strong matches found"]

    except Student.DoesNotExist:
        return ["Student not found"]
