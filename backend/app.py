from flask import Flask, render_template, jsonify, request
from datetime import datetime

app = Flask(__name__)

# Sample data for schedule and resources
schedule_data = [
    {
        "id": 1,
        "title": "Meeting with Team",
        "date": "2025-10-05",
        "time": "10:00 AM",
        "description": "Weekly team sync"
    },
    {
        "id": 2,
        "title": "Project Review",
        "date": "2025-10-06",
        "time": "2:00 PM",
        "description": "Quarterly project review"
    },
    {
        "id": 3,
        "title": "Client Call",
        "date": "2025-10-07",
        "time": "11:30 AM",
        "description": "Discuss project requirements"
    }
]

resources_data = [
    {
        "id": 1,
        "title": "Flask Documentation",
        "url": "https://flask.palletsprojects.com/",
        "category": "Documentation",
        "description": "Official Flask documentation"
    },
    {
        "id": 2,
        "title": "HTML/CSS Guide",
        "url": "https://developer.mozilla.org/en-US/docs/Web/HTML",
        "category": "Tutorial",
        "description": "Complete HTML and CSS guide"
    },
    {
        "id": 3,
        "title": "JavaScript Reference",
        "url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript",
        "category": "Reference",
        "description": "JavaScript language reference"
    }
]

# Routes for serving HTML pages
@app.route('/')
def home():
    """Main page route"""
    return render_template('index.html')

@app.route('/schedule')
def schedule():
    """Schedule page route"""
    return render_template('schedule.html')

@app.route('/resources')
def resources():
    """Resources page route"""
    return render_template('resources.html')

# API endpoints
@app.route('/api/schedule', methods=['GET'])
def get_schedule():
    """API endpoint to get schedule data"""
    return jsonify({
        'status': 'success',
        'data': schedule_data
    })

@app.route('/api/schedule', methods=['POST'])
def add_schedule_item():
    """API endpoint to add a new schedule item"""
    data = request.get_json()
    
    if not data or not all(key in data for key in ['title', 'date', 'time']):
        return jsonify({
            'status': 'error',
            'message': 'Missing required fields: title, date, time'
        }), 400
    
    new_item = {
        'id': len(schedule_data) + 1,
        'title': data['title'],
        'date': data['date'],
        'time': data['time'],
        'description': data.get('description', '')
    }
    
    schedule_data.append(new_item)
    
    return jsonify({
        'status': 'success',
        'message': 'Schedule item added',
        'data': new_item
    }), 201

@app.route('/api/resources', methods=['GET'])
def get_resources():
    """API endpoint to get resources data"""
    return jsonify({
        'status': 'success',
        'data': resources_data
    })

@app.route('/api/resources', methods=['POST'])
def add_resource():
    """API endpoint to add a new resource"""
    data = request.get_json()
    
    if not data or not all(key in data for key in ['title', 'url', 'category']):
        return jsonify({
            'status': 'error',
            'message': 'Missing required fields: title, url, category'
        }), 400
    
    new_resource = {
        'id': len(resources_data) + 1,
        'title': data['title'],
        'url': data['url'],
        'category': data['category'],
        'description': data.get('description', '')
    }
    
    resources_data.append(new_resource)
    
    return jsonify({
        'status': 'success',
        'message': 'Resource added',
        'data': new_resource
    }), 201

@app.route('/api/status', methods=['GET'])
def get_status():
    """API endpoint to get application status"""
    return jsonify({
        'status': 'success',
        'message': 'Flask app is running',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
