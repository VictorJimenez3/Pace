"""
Flask App with Firebase Auth + Google Calendar API
Install: pip install flask google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client firebase-admin
"""

from flask import Flask, render_template, redirect, url_for, session, request, jsonify
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import google.auth.transport.requests
import firebase_admin
from firebase_admin import credentials, auth, firestore
import os
import datetime
from functools import wraps
from io import BytesIO
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'  # Change this!

# Get the directory where this file is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Firebase Admin SDK setup
cred = credentials.Certificate(os.path.join(BASE_DIR, 'firebase-adminsdk.json'))
firebase_admin.initialize_app(cred)
db = firestore.client()

# ElevenLabs setup
elevenlabs = ElevenLabs(
    api_key=os.getenv("ELEVENLABS_API_KEY"),
)

# Google OAuth 2.0 configuration
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'  # Remove in production!

CLIENT_SECRETS_FILE = os.path.join(BASE_DIR, "client_secrets.json")
SCOPES = ['https://www.googleapis.com/auth/calendar',
          'https://www.googleapis.com/auth/userinfo.email',
          'https://www.googleapis.com/auth/userinfo.profile',
          'openid']

SAMPLE_INSIGHTS = {
    'vent': [
        "Celebrate that you showed up today—consistency is progress.",
        "Try naming the dominant emotion you felt this week; it can reduce its intensity.",
        "Consider scheduling a five-minute walk after heavy meetings to reset your focus."
    ],
    'stress': [
        "Pair high-effort tasks with restorative breaks to avoid compounding stress.",
        "Look for one commitment you can delegate or postpone this week.",
        "Check whether late-night screen time is affecting your recovery score."
    ],
    'pacing': [
        "Block a protected hour for deep work, then follow it with a deliberate pause.",
        "Use theme days (admin Monday, creative Tuesday, etc.) to reduce context switching.",
        "Stack micro-breaks with existing habits—stretch while coffee brews or load meetings."
    ],
    'general': [
        "Take a mindful breath: inhale for four counts, hold for four, exhale for six.",
        "Document one small win from today to anchor your momentum."
    ]
}

# Decorator to require login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'credentials' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.context_processor
def inject_user_context():
    """Provide user/session context to all templates."""
    return {
        'logged_in': 'credentials' in session,
        'user': session.get('user_info', {})
    }


@app.route('/')
def index():
    """Home page with onboarding and Google sign in."""
    is_logged_in = 'credentials' in session
    primary_cta = url_for('vent') if is_logged_in else url_for('login')
    cta_label = 'Continue to Weekly Vent' if is_logged_in else 'Sign in with Google'

    return render_template(
        'index.html',
        page_id='home',
        active_page='home',
        primary_cta=primary_cta,
        cta_label=cta_label
    )


@app.route('/login')
def login():
    """Initiate Google OAuth flow"""
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=url_for('callback', _external=True)
    )
    
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    
    session['state'] = state
    return redirect(authorization_url)


@app.route('/callback')
def callback():
    """Handle OAuth callback and authenticate with Firebase"""
    state = session['state']
    
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        state=state,
        redirect_uri=url_for('callback', _external=True)
    )
    
    # Get credentials from Google
    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials
    
    # Store credentials in session
    session['credentials'] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }
    
    # Get user info from Google
    oauth2_service = build('oauth2', 'v2', credentials=credentials)
    user_info = oauth2_service.userinfo().get().execute()
    
    session['user_info'] = {
        'email': user_info.get('email'),
        'name': user_info.get('name'),
        'picture': user_info.get('picture')
    }
    
    # Optional: Create/update Firebase user
    try:
        firebase_user = auth.get_user_by_email(user_info['email'])
    except:
        # Create new Firebase user if doesn't exist
        firebase_user = auth.create_user(
            email=user_info['email'],
            display_name=user_info.get('name'),
            photo_url=user_info.get('picture')
        )
    
    session['firebase_uid'] = firebase_user.uid
    
    return redirect(url_for('vent'))


@app.route('/logout')
def logout():
    """Clear session and logout"""
    session.clear()
    return redirect(url_for('index'))


@app.route('/vent')
@login_required
def vent():
    """Primary reflection page for voice venting."""
    return render_template('vent.html', page_id='vent', active_page='vent')


@app.route('/stress-check')
@login_required
def stress_check():
    """Interactive stress score checkpoint."""
    return render_template('stress.html', page_id='stress', active_page='stress')


@app.route('/pacing-advice')
@login_required
def pacing_advice():
    """Page with pacing guidance and routines."""
    return render_template('advice.html', page_id='pacing', active_page='pacing')


@app.route('/calendar')
@login_required
def calendar():
    """Display user's calendar events"""
    credentials = Credentials(**session['credentials'])
    
    # Build calendar service
    service = build('calendar', 'v3', credentials=credentials)
    
    # Get events from 1 month past to 1 month future
    now = datetime.datetime.utcnow()
    time_min = (now - datetime.timedelta(days=30)).isoformat() + 'Z'
    time_max = (now + datetime.timedelta(days=30)).isoformat() + 'Z'
    
    events_result = service.events().list(
        calendarId='primary',
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    
    events = events_result.get('items', [])
    
    return render_template(
        'calendar.html',
        events=events,
        page_id='calendar',
        active_page='calendar'
    )


@app.route('/api/events', methods=['GET'])
@login_required
def get_events():
    """Get calendar events and store in Firebase"""
    credentials = Credentials(**session['credentials'])
    service = build('calendar', 'v3', credentials=credentials)
    
    # Get events from 1 month past to 1 month future
    now = datetime.datetime.utcnow()
    time_min = (now - datetime.timedelta(days=30)).isoformat() + 'Z'
    time_max = (now + datetime.timedelta(days=30)).isoformat() + 'Z'
    
    events_result = service.events().list(
        calendarId='primary',
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    
    events = events_result.get('items', [])
    
    # Store in Firebase for this user
    user_uid = session.get('firebase_uid')
    if user_uid and events:
        # Store events in user's document
        user_ref = db.collection('users').document(user_uid)
        user_ref.set({
            'events': events,
            'last_sync': datetime.datetime.utcnow(),
            'email': session.get('user_info', {}).get('email')
        }, merge=True)
    
    return jsonify(events)

#likely need an agent to schedule events properly 
@app.route('/api/events/add', methods=['POST'])
@login_required
def add_event():
    """API endpoint to add calendar event"""
    credentials = Credentials(**session['credentials'])
    service = build('calendar', 'v3', credentials=credentials)
    
    data = request.json
    
    # Calculate times
    hours_from_now = data.get('hours_from_now', 1)
    duration_hours = data.get('duration_hours', 1)
    
    start_time = datetime.datetime.utcnow() + datetime.timedelta(hours=hours_from_now)
    end_time = start_time + datetime.timedelta(hours=duration_hours)
    
    event = {
        'summary': data.get('summary', 'New Event'),
        'description': data.get('description', ''),
        'start': {
            'dateTime': start_time.isoformat() + 'Z',
            'timeZone': 'UTC',
        },
        'end': {
            'dateTime': end_time.isoformat() + 'Z',
            'timeZone': 'UTC',
        },
    }
    
    created_event = service.events().insert(
        calendarId='primary',
        body=event
    ).execute()
    
    return jsonify(created_event)


@app.route('/api/events/<event_id>', methods=['DELETE'])
@login_required
def delete_event(event_id):
    """API endpoint to delete calendar event"""
    credentials = Credentials(**session['credentials'])
    service = build('calendar', 'v3', credentials=credentials)
    
    service.events().delete(
        calendarId='primary',
        eventId=event_id
    ).execute()
    
    return jsonify({'success': True})

#recieves audio and stores in DB
# Support both new and legacy endpoint paths. Some older frontend code (or cached JS)
# may still POST to '/transcribe'. To avoid 404 responses (which return an HTML page
# and cause "Unexpected token '<'" when parsed as JSON), we expose both routes.
@app.route('/api/transcribe', methods=['POST'])
@app.route('/transcribe', methods=['POST'])  # legacy alias
@login_required
def transcribe_audio():
    """Record audio and transcribe with ElevenLabs"""
    audio_file = request.files.get('audio')
    if not audio_file:
        return jsonify({'error': 'No audio file provided'}), 400

    try:
        # Convert audio file to BytesIO for ElevenLabs
        audio_data = BytesIO(audio_file.read())
        
        # Transcribe with ElevenLabs
        transcription = elevenlabs.speech_to_text.convert(
            file=audio_data,
            model_id="scribe_v1",
            tag_audio_events=True,
            language_code="eng",
            diarize=False,
        )

        # Get user info from session
        user_info = session.get('user_info', {})
        user_email = user_info.get('email', '')
        user_uid = session.get('firebase_uid')

        # Store in Firebase under user's document (consistent with schedule data)
        transcription_data = {
            'text': transcription.text,
            'created_at': datetime.datetime.utcnow(),
            'audio_processed_at': datetime.datetime.utcnow(),
            'language': transcription.language_code,
            'email': user_email
        }

        # Add to user's transcriptions subcollection
        user_ref = db.collection('users').document(user_uid)
        transcription_ref = user_ref.collection('transcriptions').add(transcription_data)
        
        return jsonify({
            'text': transcription.text,
            'transcription_id': transcription_ref[1].id,
            'language': transcription.language_code,
            'email': user_email,
            'timestamp': transcription_data['created_at'].isoformat()
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

#returns transcriptions for front end
@app.route('/api/transcriptions', methods=['GET'])
@login_required
def get_transcriptions():
    """Get all transcriptions for the current user"""
    user_uid = session.get('firebase_uid')
    user_email = session.get('user_info', {}).get('email', '')
    
    try:
        # Query transcriptions from user's subcollection (no index needed)
        user_ref = db.collection('users').document(user_uid)
        transcriptions_ref = user_ref.collection('transcriptions').order_by('created_at', direction=firestore.Query.DESCENDING)
        transcriptions = []
        
        for doc in transcriptions_ref.stream():
            data = doc.to_dict()
            transcriptions.append({
                'id': doc.id,
                'text': data.get('text', ''),
                'created_at': data.get('created_at').isoformat() if data.get('created_at') else '',
                'language': data.get('language', ''),
                'email': data.get('email', '')
            })
        
        return jsonify(transcriptions)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/insights', methods=['POST'])
@login_required
def get_insights():
    """Return placeholder LLM-style insights for different focus areas."""
    payload = request.json or {}
    topic = payload.get('topic', 'general')
    hints = payload.get('inputs', {})

    suggestions = SAMPLE_INSIGHTS.get(topic, SAMPLE_INSIGHTS['general'])

    return jsonify({
        'topic': topic,
        'inputs': hints,
        'suggestions': suggestions
    })


if __name__ == '__main__':
    app.run(debug=True, port=5000, host='localhost')
