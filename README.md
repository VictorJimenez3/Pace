# Pace Web App

A simple 3-page web application built with Flask backend and vanilla HTML/CSS/JavaScript frontend.

## Features

- **Home Page**: Welcome page with overview and quick stats
- **Schedule Page**: Manage appointments and events with add/view functionality
- **Resources Page**: Organize helpful links and documentation with filtering

## Project Structure

```
backend/
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── templates/          # HTML templates
│   ├── base.html      # Base template
│   ├── index.html     # Home page
│   ├── schedule.html  # Schedule page
│   └── resources.html # Resources page
└── static/            # Static files
    ├── css/
    │   └── style.css  # Main stylesheet
    └── js/
        └── main.js    # Main JavaScript file
```

## API Endpoints

### Schedule API
- `GET /api/schedule` - Get all schedule items
- `POST /api/schedule` - Add new schedule item

### Resources API
- `GET /api/resources` - Get all resources
- `POST /api/resources` - Add new resource

### Status API
- `GET /api/status` - Get application status

## Installation & Setup

1. **Install Python dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Run the Flask application:**
   ```bash
   python app.py
   ```

3. **Open your browser and visit:**
   ```
   http://localhost:5000
   ```

## Usage

### Adding Schedule Items
1. Go to the Schedule page
2. Click "Add New Event"
3. Fill in the form with title, date, time, and description
4. Click "Add Event"

### Adding Resources
1. Go to the Resources page
2. Click "Add New Resource"
3. Fill in the form with title, URL, category, and description
4. Click "Add Resource"

### Filtering Resources
Use the filter buttons on the Resources page to filter by category:
- All
- Documentation
- Tutorial
- Reference

## Development

The application uses:
- **Backend**: Flask (Python)
- **Frontend**: Vanilla HTML, CSS, JavaScript
- **Styling**: Custom CSS with responsive design
- **Data**: In-memory storage (resets on restart)

## Features Included

- Responsive design for mobile and desktop
- Modal dialogs for adding new items
- Form validation
- Local storage for form auto-save
- Notification system
- Loading states
- Error handling
- Smooth animations and transitions

## Future Enhancements

- Database integration (SQLite/PostgreSQL)
- User authentication
- Edit/delete functionality
- Search functionality
- Calendar view for schedule
- Export functionality
- Dark mode theme