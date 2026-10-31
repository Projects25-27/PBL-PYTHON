# Campus Event Management & Feedback Analyzer

A Python web application to manage university events, student registrations, and analyze post-event feedback.

## Tech Stack

- **Backend:** Python 3 + Flask
- **Frontend:** HTML5 + CSS3 (no JavaScript)
- **Data Storage:** CSV files
- **Analytics:** Pandas
- **Visualization:** Matplotlib

## Features

- ✅ Create and manage events (Event ID, name, date, venue, max participants)
- ✅ Add and search students
- ✅ Student registration for events
- ✅ Prevent duplicate registration and registration when event is full
- ✅ Cancel registrations
- ✅ Collect feedback ratings (1-5 stars, CSS-only interactive)
- ✅ Analytics dashboard with Pandas
- ✅ Matplotlib charts (bar chart, histogram, participation graph)
- ✅ Custom exception handling (DuplicateRegistrationError, EventFullError, InvalidEventIDError, InvalidStudentIDError)
- ✅ OOP with classes: Event, Student, Registration

## Project Structure

```
pbl/
├── app.py                    # Main Flask application
├── requirements.txt          # Python dependencies
├── data/                     # CSV data files (auto-created)
│   ├── events.csv
│   ├── students.csv
│   ├── registrations.csv
│   └── feedback.csv
├── static/
│   ├── css/
│   │   └── style.css         # Complete design system
│   └── charts/               # Generated Matplotlib charts
├── templates/
│   ├── base.html             # Base template with navbar
│   ├── index.html            # Dashboard / home page
│   ├── events.html           # Events listing
│   ├── create_event.html     # Create event form
│   ├── event_detail.html     # Event detail + registered students
│   ├── students.html         # Students listing with search
│   ├── add_student.html      # Add student form
│   ├── register.html         # Event registration form
│   ├── feedback.html         # Feedback form with star rating
│   └── analytics.html        # Charts and analytics dashboard
└── venv/                     # Virtual environment
```

## Setup & Run

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

Then open **http://127.0.0.1:5000** in your browser.
