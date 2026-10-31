import unittest
from app import (
    app, Event, Student, Registration,
    DuplicateRegistrationError, EventFullError, EventClosedError, InvalidEventIDError, InvalidStudentIDError,
    generate_charts, get_analytics
)

class CampusEventAppTestCase(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True

    def test_model_classes_exist_and_work(self):
        events = Event.all()
        self.assertGreaterEqual(len(events), 5)
        evt = Event.find('EVT-101')
        self.assertEqual(evt.name, 'AI & Machine Learning Symposium')
        self.assertEqual(evt.max_participants, 50)

        students = Student.all()
        self.assertGreaterEqual(len(students), 8)
        stu = Student.find('STU-001')
        self.assertEqual(stu.name, 'Aarav Patel')

        regs = Registration.find_by_event('EVT-101')
        self.assertGreaterEqual(len(regs), 1)

    def test_search_students(self):
        results = Student.search('Aarav')
        self.assertTrue(any(s.student_id == 'STU-001' for s in results))
        dept_results = Student.search('Computer Science')
        self.assertGreaterEqual(len(dept_results), 2)

    def test_analytics_and_charts(self):
        analytics = get_analytics()
        self.assertGreater(analytics['total_events'], 0)
        self.assertGreater(analytics['total_students'], 0)
        self.assertGreater(analytics['total_registrations'], 0)
        self.assertGreater(analytics['total_feedback'], 0)
        self.assertGreater(analytics['overall_avg_rating'], 0)

        # Test chart generation with Matplotlib
        generate_charts()
        import os
        charts_dir = app.static_folder + '/charts'
        self.assertTrue(os.path.exists(os.path.join(charts_dir, 'avg_rating.png')))
        self.assertTrue(os.path.exists(os.path.join(charts_dir, 'rating_histogram.png')))
        self.assertTrue(os.path.exists(os.path.join(charts_dir, 'participation.png')))

    def test_http_routes(self):
        # 1. Homepage
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Campus Event Management', resp.data)

        # 2. Events list
        resp = self.client.get('/events')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Machine Learning Symposium', resp.data)

        # 3. Event detail
        resp = self.client.get('/events/EVT-101')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Registered Students', resp.data)

        # 4. Students list & search
        resp = self.client.get('/students?q=Aarav')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Aarav Patel', resp.data)

        # 5. Registration page GET
        resp = self.client.get('/register')
        self.assertEqual(resp.status_code, 200)

        # 6. Feedback page GET
        resp = self.client.get('/feedback')
        self.assertEqual(resp.status_code, 200)

        # 7. Analytics dashboard GET
        resp = self.client.get('/analytics')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Charts &amp; Visualizations', resp.data)

    def test_duplicate_registration_prevention(self):
        # STU-001 is already registered for EVT-101
        self.assertTrue(Registration.is_duplicate('EVT-101', 'STU-001'))
        resp = self.client.post('/register', data={
            'event_id': 'EVT-101',
            'student_id': 'STU-001'
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'already registered', resp.data)

    def test_past_event_status_and_prevention(self):
        # EVT-101 is on 2026-10-15 (past)
        evt_past = Event.find('EVT-101')
        self.assertTrue(evt_past.is_past())
        self.assertEqual(evt_past.status, 'Closed')

        # EVT-105 is on 2026-11-20 (future)
        evt_future = Event.find('EVT-105')
        self.assertFalse(evt_future.is_past())

        # Attempt to register STU-004 (not yet registered) for past event EVT-101
        self.assertFalse(Registration.is_duplicate('EVT-101', 'STU-004'))
        resp = self.client.post('/register', data={
            'event_id': 'EVT-101',
            'student_id': 'STU-004'
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Registration is closed', resp.data)

    def test_event_list_filters(self):
        # All events
        resp = self.client.get('/events?filter=all')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'AI &amp; Machine Learning Symposium', resp.data)
        self.assertIn(b'Closed', resp.data)

        # Upcoming filter should not include EVT-101
        resp = self.client.get('/events?filter=upcoming')
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn(b'AI &amp; Machine Learning Symposium', resp.data)

        # Past filter should include EVT-101
        resp = self.client.get('/events?filter=past')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'AI &amp; Machine Learning Symposium', resp.data)

    def test_security_headers(self):
        resp = self.client.get('/')
        self.assertEqual(resp.headers.get('X-Content-Type-Options'), 'nosniff')
        self.assertEqual(resp.headers.get('X-Frame-Options'), 'DENY')
        self.assertIn("default-src 'self'", resp.headers.get('Content-Security-Policy', ''))

if __name__ == '__main__':
    unittest.main()
