import csv
import os
from datetime import datetime, timedelta

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
os.makedirs(DATA_DIR, exist_ok=True)

EVENTS_FILE = os.path.join(DATA_DIR, 'events.csv')
STUDENTS_FILE = os.path.join(DATA_DIR, 'students.csv')
REGISTRATIONS_FILE = os.path.join(DATA_DIR, 'registrations.csv')
FEEDBACK_FILE = os.path.join(DATA_DIR, 'feedback.csv')

def seed():
    # 1. Events
    events = [
        ['EVT-101', 'AI & Machine Learning Symposium', '2026-10-15', 'Main Auditorium', '50'],
        ['EVT-102', 'HackCampus 24h Hackathon', '2026-10-22', 'Innovation Lab 3', '30'],
        ['EVT-103', 'Annual Cultural Fest - Rhythm 2026', '2026-11-05', 'Open Air Theatre', '120'],
        ['EVT-104', 'Robotics & IoT Workshop', '2026-11-12', 'ECE Seminar Hall', '25'],
        ['EVT-105', 'Career & Internship Expo', '2026-11-20', 'University Sports Arena', '80'],
    ]
    with open(EVENTS_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['event_id', 'name', 'date', 'venue', 'max_participants'])
        writer.writerows(events)
    print(f"Seeded {len(events)} events.")

    # 2. Students
    students = [
        ['STU-001', 'Aarav Patel', 'aarav.patel@campus.edu', 'Computer Science'],
        ['STU-002', 'Diya Sharma', 'diya.sharma@campus.edu', 'Information Technology'],
        ['STU-003', 'Rohan Mehta', 'rohan.mehta@campus.edu', 'Electronics & Comm.'],
        ['STU-004', 'Ananya Iyer', 'ananya.iyer@campus.edu', 'Mechanical Engineering'],
        ['STU-005', 'Kabir Verma', 'kabir.verma@campus.edu', 'Computer Science'],
        ['STU-006', 'Sneha Nair', 'sneha.nair@campus.edu', 'Data Science'],
        ['STU-007', 'Vikram Singh', 'vikram.singh@campus.edu', 'Electrical Engineering'],
        ['STU-008', 'Pooja Joshi', 'pooja.joshi@campus.edu', 'Business Administration'],
    ]
    with open(STUDENTS_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['student_id', 'name', 'email', 'department'])
        writer.writerows(students)
    print(f"Seeded {len(students)} students.")

    # 3. Registrations
    registrations = [
        ['R001', 'EVT-101', 'STU-001', '2026-09-20 10:15'],
        ['R002', 'EVT-101', 'STU-002', '2026-09-20 11:30'],
        ['R003', 'EVT-101', 'STU-005', '2026-09-21 09:45'],
        ['R004', 'EVT-101', 'STU-006', '2026-09-21 14:20'],
        ['R005', 'EVT-102', 'STU-001', '2026-09-22 16:10'],
        ['R006', 'EVT-102', 'STU-003', '2026-09-22 17:00'],
        ['R007', 'EVT-102', 'STU-005', '2026-09-23 08:30'],
        ['R008', 'EVT-103', 'STU-002', '2026-09-23 12:15'],
        ['R009', 'EVT-103', 'STU-004', '2026-09-24 10:05'],
        ['R010', 'EVT-103', 'STU-007', '2026-09-24 15:40'],
        ['R011', 'EVT-103', 'STU-008', '2026-09-25 11:20'],
        ['R012', 'EVT-104', 'STU-003', '2026-09-25 13:50'],
        ['R013', 'EVT-104', 'STU-007', '2026-09-26 09:10'],
        ['R014', 'EVT-105', 'STU-001', '2026-09-26 14:00'],
        ['R015', 'EVT-105', 'STU-006', '2026-09-26 16:30'],
        ['R016', 'EVT-105', 'STU-008', '2026-09-27 10:45'],
    ]
    with open(REGISTRATIONS_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['reg_id', 'event_id', 'student_id', 'reg_date'])
        writer.writerows(registrations)
    print(f"Seeded {len(registrations)} registrations.")

    # 4. Feedback
    feedback = [
        ['FB001', 'EVT-101', 'STU-001', 5, 'Exceptional keynote speakers and very insightful hands-on sessions!', '2026-09-22 18:00'],
        ['FB002', 'EVT-101', 'STU-002', 4, 'Great event overall. Audio system could be improved.', '2026-09-22 19:15'],
        ['FB003', 'EVT-101', 'STU-005', 5, 'Learned so much about current LLM and ML deployment trends.', '2026-09-23 09:00'],
        ['FB004', 'EVT-102', 'STU-001', 4, 'Intense 24 hours! Mentors were super supportive.', '2026-09-24 11:30'],
        ['FB005', 'EVT-102', 'STU-003', 5, 'Great problem statements and seamless organization.', '2026-09-24 12:45'],
        ['FB006', 'EVT-103', 'STU-002', 5, 'Unforgettable performances and vibrant atmosphere!', '2026-09-26 10:20'],
        ['FB007', 'EVT-103', 'STU-004', 4, 'Loved the stage lighting and student band.', '2026-09-26 14:00'],
        ['FB008', 'EVT-104', 'STU-003', 4, 'Hardware kits were high quality. Wanted more coding time.', '2026-09-27 15:30'],
        ['FB009', 'EVT-105', 'STU-008', 5, 'Connected with three prospective recruiters on the spot!', '2026-09-27 17:10'],
    ]
    with open(FEEDBACK_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['feedback_id', 'event_id', 'student_id', 'rating', 'comment', 'submitted_at'])
        writer.writerows(feedback)
    print(f"Seeded {len(feedback)} feedback entries.")

if __name__ == '__main__':
    seed()
