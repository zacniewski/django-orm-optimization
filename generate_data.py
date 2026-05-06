import json
import random


def generate_data():
    mentors = []
    specializations = ["Python", "Java", "Data", "Frontend"]

    for i in range(1, 101):
        mentors.append(
            {
                "model": "university.mentor",
                "pk": i,
                "fields": {
                    "name": f"Mentor {i}",
                    "specialization": random.choice(specializations),
                },
            }
        )

    students = []
    for i in range(1, 100001):
        students.append(
            {
                "model": "university.student",
                "pk": i,
                "fields": {
                    "name": f"Student {i}",
                    "bio": f"Bio for student {i}. This is a sample description for testing Django ORM optimization.",
                    "mentor": random.randint(1, 100),
                },
            }
        )

    data = mentors + students

    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)


if __name__ == "__main__":
    generate_data()
    print("Successfully generated data.json with 100 mentors and 100,000 students.")
