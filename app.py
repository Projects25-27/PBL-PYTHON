import csv
import io
import os
import secrets
import logging
from datetime import datetime, timedelta

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server-side rendering
import matplotlib.pyplot as plt
import pandas as pd
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, send_file, Response
)

app = Flask(__name__)

def _get_secret_key():
    env_key = os.environ.get('FLASK_SECRET_KEY')
    if env_key:
        return env_key
    secret_file = os.path.join(os.path.dirname(__file__), '.flask_secret')
    if os.path.exists(secret_file):
        with open(secret_file, 'r') as f:
            return f.read().strip()
    generated = secrets.token_hex(32)
    logging.warning(
        "No FLASK_SECRET_KEY found. Generated ephemeral secret. "
        "Sessions will not survive restarts."
    )
    return generated

app.secret_key = _get_secret_key()
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
# TODO(security): Enable Secure flag when serving over HTTPS in production.
# app.config['SESSION_COOKIE_SECURE'] = True

# ---------------------------------------------------------------------------
# Data Directory & File Paths
# ---------------------------------------------------------------------------
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
os.makedirs(DATA_DIR, exist_ok=True)

EVENTS_FILE = os.path.join(DATA_DIR, 'events.csv')
STUDENTS_FILE = os.path.join(DATA_DIR, 'students.csv')
REGISTRATIONS_FILE = os.path.join(DATA_DIR, 'registrations.csv')
FEEDBACK_FILE = os.path.join(DATA_DIR, 'feedback.csv')

CHARTS_DIR = os.path.join(app.static_folder, 'charts')
os.makedirs(CHARTS_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# CSV Headers
# ---------------------------------------------------------------------------
EVENT_HEADERS = ['event_id', 'name', 'date', 'venue', 'max_participants']
STUDENT_HEADERS = ['student_id', 'name', 'email', 'department']
REGISTRATION_HEADERS = ['reg_id', 'event_id', 'student_id', 'reg_date']
FEEDBACK_HEADERS = ['feedback_id', 'event_id', 'student_id', 'rating', 'comment', 'submitted_at']


# ---------------------------------------------------------------------------
# Helper: Initialise CSV files with headers if they don't exist
# ---------------------------------------------------------------------------
def _init_csv(filepath, headers):
    if not os.path.exists(filepath):
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)

_init_csv(EVENTS_FILE, EVENT_HEADERS)
_init_csv(STUDENTS_FILE, STUDENT_HEADERS)
_init_csv(REGISTRATIONS_FILE, REGISTRATION_HEADERS)
_init_csv(FEEDBACK_FILE, FEEDBACK_HEADERS)


# ===================================================================
# MODEL CLASSES
# ===================================================================
class Event:
    """Represents a campus event."""

    def __init__(self, event_id, name, date, venue, max_participants):
        self.event_id = str(event_id).strip()
        self.name = str(name).strip()
        self.date = str(date).strip()
        self.venue = str(venue).strip()
        self.max_participants = int(max_participants)

    def to_row(self):
        return [self.event_id, self.name, self.date, self.venue, self.max_participants]

    @staticmethod
    def all():
        """Return all events as a list of Event objects."""
        events = []
        with open(EVENTS_FILE, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                events.append(Event(
                    row['event_id'], row['name'], row['date'],
                    row['venue'], row['max_participants']
                ))
        return events

    @staticmethod
    def find(event_id):
        """Find an event by ID. Raises ValueError if not found."""
        for ev in Event.all():
            if ev.event_id == str(event_id).strip():
                return ev
        raise ValueError(f"Event with ID '{event_id}' not found.")

    def save(self):
        """Append this event to the CSV file."""
        with open(EVENTS_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(self.to_row())

    def registered_count(self):
        """Count current registrations for this event."""
        count = 0
        with open(REGISTRATIONS_FILE, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['event_id'] == self.event_id:
                    count += 1
        return count

    def is_full(self):
        return self.registered_count() >= self.max_participants

    @staticmethod
    def delete(event_id):
        """Delete an event by rewriting the CSV without it."""
        events = Event.all()
        with open(EVENTS_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(EVENT_HEADERS)
            for ev in events:
                if ev.event_id != str(event_id).strip():
                    writer.writerow(ev.to_row())


class Student:
    """Represents a student."""

    def __init__(self, student_id, name, email, department):
        self.student_id = str(student_id).strip()
        self.name = str(name).strip()
        self.email = str(email).strip()
        self.department = str(department).strip()

    def to_row(self):
        return [self.student_id, self.name, self.email, self.department]

    @staticmethod
    def all():
        students = []
        with open(STUDENTS_FILE, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                students.append(Student(
                    row['student_id'], row['name'], row['email'], row['department']
                ))
        return students

    @staticmethod
    def find(student_id):
        for s in Student.all():
            if s.student_id == str(student_id).strip():
                return s
        raise ValueError(f"Student with ID '{student_id}' not found.")

    @staticmethod
    def search(query):
        """Search students by name, ID, or department (case-insensitive)."""
        query_lower = query.lower().strip()
        results = []
        for s in Student.all():
            if (query_lower in s.name.lower() or
                    query_lower in s.student_id.lower() or
                    query_lower in s.department.lower()):
                results.append(s)
        return results

    def save(self):
        with open(STUDENTS_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(self.to_row())

    @staticmethod
    def exists(student_id):
        try:
            Student.find(student_id)
            return True
        except ValueError:
            return False


class Registration:
    """Represents a student's registration for an event."""

    def __init__(self, reg_id, event_id, student_id, reg_date=None):
        self.reg_id = str(reg_id).strip()
        self.event_id = str(event_id).strip()
        self.student_id = str(student_id).strip()
        self.reg_date = reg_date or datetime.now().strftime('%Y-%m-%d %H:%M')

    def to_row(self):
        return [self.reg_id, self.event_id, self.student_id, self.reg_date]

    @staticmethod
    def all():
        registrations = []
        with open(REGISTRATIONS_FILE, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                registrations.append(Registration(
                    row['reg_id'], row['event_id'],
                    row['student_id'], row['reg_date']
                ))
        return registrations

    @staticmethod
    def find_by_event(event_id):
        return [r for r in Registration.all() if r.event_id == str(event_id).strip()]

    @staticmethod
    def is_duplicate(event_id, student_id):
        """Check if a student is already registered for the event."""
        for r in Registration.all():
            if r.event_id == str(event_id).strip() and r.student_id == str(student_id).strip():
                return True
        return False

    def save(self):
        with open(REGISTRATIONS_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(self.to_row())

    @staticmethod
    def cancel(event_id, student_id):
        """Cancel a registration by rewriting CSV without it."""
        regs = Registration.all()
        cancelled = False
        with open(REGISTRATIONS_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(REGISTRATION_HEADERS)
            for r in regs:
                if r.event_id == str(event_id).strip() and r.student_id == str(student_id).strip():
                    cancelled = True
                    continue
                writer.writerow(r.to_row())
        if not cancelled:
            raise ValueError("Registration not found.")

    @staticmethod
    def next_id():
        regs = Registration.all()
        if not regs:
            return 'R001'
        max_num = max(int(r.reg_id.replace('R', '')) for r in regs)
        return f'R{max_num + 1:03d}'


class DuplicateRegistrationError(Exception):
    """Raised when a student tries to register for the same event twice."""
    pass


class EventFullError(Exception):
    """Raised when an event has reached its maximum participant limit."""
    pass


class InvalidEventIDError(Exception):
    """Raised when a provided event ID does not exist."""
    pass


class InvalidStudentIDError(Exception):
    """Raised when a provided student ID does not exist."""
    pass


# ===================================================================
# CHART GENERATION (Matplotlib)
# ===================================================================
def generate_charts():
    """Generate analysis charts using Matplotlib and save as PNG files."""
    plt.style.use('seaborn-v0_8-darkgrid')

    # --- Load data with Pandas ---
    try:
        df_feedback = pd.read_csv(FEEDBACK_FILE)
        df_registrations = pd.read_csv(REGISTRATIONS_FILE)
        df_events = pd.read_csv(EVENTS_FILE)
    except Exception:
        return

    if df_events.empty:
        return

    # Ensure correct types
    if not df_feedback.empty:
        df_feedback['rating'] = pd.to_numeric(df_feedback['rating'], errors='coerce')

    # --- 1. Bar Chart: Average Rating per Event ---
    fig1, ax1 = plt.subplots(figsize=(10, 5))
    if not df_feedback.empty:
        avg_ratings = df_feedback.groupby('event_id')['rating'].mean()
        event_names = []
        ratings = []
        for eid, rating in avg_ratings.items():
            try:
                ev = Event.find(str(eid))
                event_names.append(ev.name)
            except ValueError:
                event_names.append(str(eid))
            ratings.append(rating)

        colors = plt.cm.viridis([i / max(len(event_names), 1) for i in range(len(event_names))])
        bars = ax1.bar(event_names, ratings, color=colors, edgecolor='white', linewidth=0.8)
        ax1.set_xlabel('Event', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Average Rating', fontsize=12, fontweight='bold')
        ax1.set_title('Average Feedback Rating per Event', fontsize=14, fontweight='bold')
        ax1.set_ylim(0, 5.5)
        ax1.tick_params(axis='x', rotation=30)
        for bar, val in zip(bars, ratings):
            ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
                     f'{val:.1f}', ha='center', va='bottom', fontweight='bold')
    else:
        ax1.text(0.5, 0.5, 'No feedback data yet', ha='center', va='center',
                 transform=ax1.transAxes, fontsize=14, color='gray')
        ax1.set_title('Average Feedback Rating per Event', fontsize=14, fontweight='bold')

    fig1.tight_layout()
    fig1.savefig(os.path.join(CHARTS_DIR, 'avg_rating.png'), dpi=120, bbox_inches='tight')
    plt.close(fig1)

    # --- 2. Histogram: Distribution of Ratings ---
    fig2, ax2 = plt.subplots(figsize=(8, 5))
    if not df_feedback.empty:
        ax2.hist(df_feedback['rating'].dropna(), bins=[0.5, 1.5, 2.5, 3.5, 4.5, 5.5],
                 color='#6C5CE7', edgecolor='white', linewidth=1.2, rwidth=0.85)
        ax2.set_xlabel('Rating', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Number of Responses', fontsize=12, fontweight='bold')
        ax2.set_title('Distribution of Feedback Ratings', fontsize=14, fontweight='bold')
        ax2.set_xticks([1, 2, 3, 4, 5])
        ax2.set_xticklabels(['1 Star', '2 Star', '3 Star', '4 Star', '5 Star'])
    else:
        ax2.text(0.5, 0.5, 'No feedback data yet', ha='center', va='center',
                 transform=ax2.transAxes, fontsize=14, color='gray')
        ax2.set_title('Distribution of Feedback Ratings', fontsize=14, fontweight='bold')

    fig2.tight_layout()
    fig2.savefig(os.path.join(CHARTS_DIR, 'rating_histogram.png'), dpi=120, bbox_inches='tight')
    plt.close(fig2)

    # --- 3. Bar Chart: Event-wise Participation ---
    fig3, ax3 = plt.subplots(figsize=(10, 5))
    if not df_registrations.empty:
        participation = df_registrations.groupby('event_id').size()
        event_names = []
        counts = []
        max_caps = []
        for eid, count in participation.items():
            try:
                ev = Event.find(str(eid))
                event_names.append(ev.name)
                max_caps.append(ev.max_participants)
            except ValueError:
                event_names.append(str(eid))
                max_caps.append(0)
            counts.append(count)

        x = range(len(event_names))
        bars1 = ax3.bar([i - 0.15 for i in x], counts, width=0.3,
                        label='Registered', color='#00B894', edgecolor='white')
        bars2 = ax3.bar([i + 0.15 for i in x], max_caps, width=0.3,
                        label='Max Capacity', color='#FDCB6E', edgecolor='white')
        ax3.set_xticks(list(x))
        ax3.set_xticklabels(event_names, rotation=30)
        ax3.set_xlabel('Event', fontsize=12, fontweight='bold')
        ax3.set_ylabel('Number of Participants', fontsize=12, fontweight='bold')
        ax3.set_title('Event-wise Participation', fontsize=14, fontweight='bold')
        ax3.legend()
    else:
        ax3.text(0.5, 0.5, 'No registration data yet', ha='center', va='center',
                 transform=ax3.transAxes, fontsize=14, color='gray')
        ax3.set_title('Event-wise Participation', fontsize=14, fontweight='bold')

    fig3.tight_layout()
    fig3.savefig(os.path.join(CHARTS_DIR, 'participation.png'), dpi=120, bbox_inches='tight')
    plt.close(fig3)


# ===================================================================
# ANALYTICS HELPER (Pandas)
# ===================================================================
def get_analytics():
    """Compute analytics using Pandas and return a dictionary."""
    try:
        df_events = pd.read_csv(EVENTS_FILE)
        df_registrations = pd.read_csv(REGISTRATIONS_FILE)
        df_feedback = pd.read_csv(FEEDBACK_FILE)
    except Exception:
        return {
            'total_events': 0, 'total_students': 0, 'total_registrations': 0,
            'total_feedback': 0, 'overall_avg_rating': 0, 'event_stats': []
        }

    total_events = len(df_events)
    total_registrations = len(df_registrations)
    total_feedback = len(df_feedback)

    try:
        df_students = pd.read_csv(STUDENTS_FILE)
        total_students = len(df_students)
    except Exception:
        total_students = 0

    overall_avg = 0
    if not df_feedback.empty:
        df_feedback['rating'] = pd.to_numeric(df_feedback['rating'], errors='coerce')
        overall_avg = round(df_feedback['rating'].mean(), 2)

    # Per-event stats
    event_stats = []
    for _, ev_row in df_events.iterrows():
        eid = str(ev_row['event_id'])
        reg_count = len(df_registrations[df_registrations['event_id'].astype(str) == eid])
        fb_subset = df_feedback[df_feedback['event_id'].astype(str) == eid]
        fb_count = len(fb_subset)
        if not fb_subset.empty:
            avg_r = round(fb_subset['rating'].mean(), 2)
        else:
            avg_r = 'N/A'

        event_stats.append({
            'event_id': eid,
            'name': ev_row['name'],
            'date': ev_row['date'],
            'venue': ev_row['venue'],
            'max_participants': ev_row['max_participants'],
            'registered': reg_count,
            'feedback_count': fb_count,
            'avg_rating': avg_r
        })

    return {
        'total_events': total_events,
        'total_students': total_students,
        'total_registrations': total_registrations,
        'total_feedback': total_feedback,
        'overall_avg_rating': overall_avg,
        'event_stats': event_stats
    }


# ===================================================================
# SECURITY MIDDLEWARE
# ===================================================================
@app.after_request
def set_security_headers(response):
    """Set security headers on every response."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "style-src 'self'; "
        "img-src 'self'; "
        "script-src 'none'; "
        "object-src 'none'; "
        "frame-ancestors 'none';"
    )
    response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
    return response


# ===================================================================
# ROUTES
# ===================================================================

# -- Home / Dashboard --
@app.route('/')
def index():
    analytics = get_analytics()
    return render_template('index.html', analytics=analytics)


# -- Events CRUD --
@app.route('/events')
def events_list():
    events = Event.all()
    return render_template('events.html', events=events)


@app.route('/events/create', methods=['GET', 'POST'])
def create_event():
    if request.method == 'POST':
        event_id = request.form.get('event_id', '').strip()
        name = request.form.get('name', '').strip()
        date = request.form.get('date', '').strip()
        venue = request.form.get('venue', '').strip()
        max_p = request.form.get('max_participants', '').strip()

        # Input validation
        if not all([event_id, name, date, venue, max_p]):
            flash('All fields are required.', 'error')
            return redirect(url_for('create_event'))

        # Validate max_participants is a positive integer
        try:
            max_p_int = int(max_p)
            if max_p_int <= 0:
                raise ValueError
        except ValueError:
            flash('Maximum participants must be a positive number.', 'error')
            return redirect(url_for('create_event'))

        # Validate date format and ensure it is not in the past
        try:
            event_date = datetime.strptime(date, '%Y-%m-%d').date()
            if event_date < datetime.today().date():
                flash('Event date cannot be in the past. Please select today or a future date.', 'error')
                return redirect(url_for('create_event'))
        except ValueError:
            flash('Invalid date format. Please use the date picker.', 'error')
            return redirect(url_for('create_event'))

        # Check for duplicate event ID
        try:
            Event.find(event_id)
            flash(f'Event ID "{event_id}" already exists.', 'error')
            return redirect(url_for('create_event'))
        except ValueError:
            pass  # Good — ID is unique

        # Validate event_id format (alphanumeric, max 20 chars)
        if not event_id.replace('-', '').replace('_', '').isalnum() or len(event_id) > 20:
            flash('Event ID must be alphanumeric (hyphens/underscores allowed), max 20 characters.', 'error')
            return redirect(url_for('create_event'))

        event = Event(event_id, name, date, venue, max_p_int)
        event.save()
        flash(f'Event "{name}" created successfully!', 'success')
        return redirect(url_for('events_list'))

    today_date = datetime.today().strftime('%Y-%m-%d')
    return render_template('create_event.html', today_date=today_date)


@app.route('/events/<event_id>')
def event_detail(event_id):
    try:
        event = Event.find(event_id)
    except ValueError:
        flash('Event not found.', 'error')
        return redirect(url_for('events_list'))

    registrations = Registration.find_by_event(event_id)
    students = []
    for reg in registrations:
        try:
            student = Student.find(reg.student_id)
            students.append({'student': student, 'reg': reg})
        except ValueError:
            continue

    return render_template('event_detail.html', event=event, students=students)


@app.route('/events/<event_id>/delete', methods=['POST'])
def delete_event(event_id):
    try:
        event = Event.find(event_id)
        Event.delete(event_id)
        flash(f'Event "{event.name}" deleted.', 'success')
    except ValueError:
        flash('Event not found.', 'error')
    return redirect(url_for('events_list'))


# -- Students --
@app.route('/students')
def students_list():
    query = request.args.get('q', '').strip()
    if query:
        students = Student.search(query)
    else:
        students = Student.all()
    return render_template('students.html', students=students, query=query)


@app.route('/students/add', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        student_id = request.form.get('student_id', '').strip()
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        department = request.form.get('department', '').strip()

        if not all([student_id, name, email, department]):
            flash('All fields are required.', 'error')
            return redirect(url_for('add_student'))

        # Validate student_id format
        if not student_id.replace('-', '').replace('_', '').isalnum() or len(student_id) > 20:
            flash('Student ID must be alphanumeric (hyphens/underscores allowed), max 20 characters.', 'error')
            return redirect(url_for('add_student'))

        if Student.exists(student_id):
            flash(f'Student ID "{student_id}" already exists.', 'error')
            return redirect(url_for('add_student'))

        # Basic email validation
        if '@' not in email or '.' not in email.split('@')[-1]:
            flash('Please enter a valid email address.', 'error')
            return redirect(url_for('add_student'))

        student = Student(student_id, name, email, department)
        student.save()
        flash(f'Student "{name}" added successfully!', 'success')
        return redirect(url_for('students_list'))

    return render_template('add_student.html')


# -- Registration --
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        event_id = request.form.get('event_id', '').strip()
        student_id = request.form.get('student_id', '').strip()

        try:
            # Validate event exists
            try:
                event = Event.find(event_id)
            except ValueError:
                raise InvalidEventIDError(f"Event ID '{event_id}' does not exist.")

            # Validate student exists
            try:
                student = Student.find(student_id)
            except ValueError:
                raise InvalidStudentIDError(f"Student ID '{student_id}' does not exist.")

            # Check for duplicate registration
            if Registration.is_duplicate(event_id, student_id):
                raise DuplicateRegistrationError(
                    f"Student '{student.name}' is already registered for '{event.name}'."
                )

            # Check if event is full
            if event.is_full():
                raise EventFullError(
                    f"Event '{event.name}' is full ({event.max_participants}/{event.max_participants})."
                )

            # Create registration
            reg = Registration(Registration.next_id(), event_id, student_id)
            reg.save()
            flash(f"'{student.name}' registered for '{event.name}' successfully!", 'success')

        except (InvalidEventIDError, InvalidStudentIDError,
                DuplicateRegistrationError, EventFullError) as e:
            flash(str(e), 'error')

        return redirect(url_for('register'))

    events = Event.all()
    students = Student.all()
    return render_template('register.html', events=events, students=students)


@app.route('/register/cancel', methods=['POST'])
def cancel_registration():
    event_id = request.form.get('event_id', '').strip()
    student_id = request.form.get('student_id', '').strip()

    try:
        Registration.cancel(event_id, student_id)
        flash('Registration cancelled successfully.', 'success')
    except ValueError as e:
        flash(str(e), 'error')

    return redirect(url_for('event_detail', event_id=event_id))


# -- Feedback --
@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        event_id = request.form.get('event_id', '').strip()
        student_id = request.form.get('student_id', '').strip()
        rating = request.form.get('rating', '').strip()
        comment = request.form.get('comment', '').strip()

        # Validation
        try:
            Event.find(event_id)
        except ValueError:
            flash('Invalid event ID.', 'error')
            return redirect(url_for('feedback'))

        try:
            Student.find(student_id)
        except ValueError:
            flash('Invalid student ID.', 'error')
            return redirect(url_for('feedback'))

        # Check student is registered
        if not Registration.is_duplicate(event_id, student_id):
            flash('Student must be registered for the event to give feedback.', 'error')
            return redirect(url_for('feedback'))

        try:
            rating_int = int(rating)
            if rating_int < 1 or rating_int > 5:
                raise ValueError
        except ValueError:
            flash('Rating must be between 1 and 5.', 'error')
            return redirect(url_for('feedback'))

        # Generate feedback ID
        try:
            df = pd.read_csv(FEEDBACK_FILE)
            if df.empty:
                fb_id = 'FB001'
            else:
                max_num = df['feedback_id'].str.replace('FB', '', regex=False).astype(int).max()
                fb_id = f'FB{max_num + 1:03d}'
        except Exception:
            fb_id = 'FB001'

        # Sanitise comment (remove commas to prevent CSV issues, limit length)
        comment = comment.replace(',', ' ').strip()[:500]

        with open(FEEDBACK_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([fb_id, event_id, student_id, rating_int,
                             comment, datetime.now().strftime('%Y-%m-%d %H:%M')])

        flash('Feedback submitted successfully!', 'success')
        return redirect(url_for('feedback'))

    events = Event.all()
    students = Student.all()
    return render_template('feedback.html', events=events, students=students)


# -- Analytics Dashboard --
@app.route('/analytics')
def analytics():
    generate_charts()
    analytics_data = get_analytics()
    return render_template('analytics.html', analytics=analytics_data)


# ===================================================================
# MAIN
# ===================================================================
if __name__ == '__main__':
    # Listen on localhost only for security.
    app.run(host='127.0.0.1', port=5000, debug=True)
