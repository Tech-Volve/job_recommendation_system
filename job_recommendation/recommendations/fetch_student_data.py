from ucimlrepo import fetch_ucirepo
import json
from recommendations.models import Student

def fetch_and_store_student_data():
    # Fetch dataset
    student_data = fetch_ucirepo(id=467)
    
    # Extract features (X) and targets (y)
    X = student_data.data.features
    y = student_data.data.targets  # Assuming this is the final grade or performance label

    # Iterate through dataset and store in database
    for index, row in X.iterrows():
        student = Student(
            name=f"Student {index}",  # Placeholder name
            student_id=f"S{index}",  # Placeholder student ID
            grades=json.dumps(row.to_dict()),  # Convert row data to JSON
            interests="Not specified",
            skills="Not specified"
        )
        student.save()
    
    print("Student data imported successfully.")


