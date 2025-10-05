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
import google.generativeai as genai

load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

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


# ============================================================================
# HELPER FUNCTIONS FOR LLM DATA GATHERING
# ============================================================================

def get_user_transcriptions_text(user_uid, limit=10):
    """Fetch recent transcription texts for the user."""
    try:
        user_ref = db.collection('users').document(user_uid)
        transcriptions_ref = user_ref.collection('transcriptions').order_by(
            'created_at', direction=firestore.Query.DESCENDING
        ).limit(limit)
        
        texts = []
        for doc in transcriptions_ref.stream():
            data = doc.to_dict()
            if data.get('text'):
                texts.append(data['text'])
        return texts
    except Exception as e:
        print(f"Error fetching transcriptions: {e}")
        return []


def get_user_calendar_events(credentials_dict, days_ahead=7):
    """Fetch upcoming calendar events."""
    try:
        credentials = Credentials(**credentials_dict)
        service = build('calendar', 'v3', credentials=credentials)
        
        now = datetime.datetime.utcnow()
        time_min = now.isoformat() + 'Z'
        time_max = (now + datetime.timedelta(days=days_ahead)).isoformat() + 'Z'
        
        events_result = service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        return events_result.get('items', [])
    except Exception as e:
        print(f"Error fetching calendar events: {e}")
        return []


def count_events_by_day(events):
    """Count events per day for calendar density analysis."""
    day_counts = {}
    for event in events:
        start = event.get('start', {})
        date_str = start.get('dateTime', start.get('date', ''))
        if date_str:
            day = date_str.split('T')[0]
            day_counts[day] = day_counts.get(day, 0) + 1
    return day_counts


# ============================================================================
# LLM 1: ASSISTANT INSIGHTS (Generic)
# Pages: /vent AND /stress-check
# ============================================================================

@app.route('/api/insights', methods=['POST'])
@login_required
def get_insights():
    """LLM 1: Generate generic actionable tips based on vent transcriptions or stress scores."""
    try:
        payload = request.json or {}
        topic = payload.get('topic', 'general')
        inputs = payload.get('inputs', {})
        user_uid = session.get('firebase_uid')
        
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        if topic == 'vent':
            # Get recent transcriptions
            transcriptions = get_user_transcriptions_text(user_uid, limit=5)
            
            if not transcriptions:
                return jsonify({
                    'topic': topic,
                    'suggestions': ["Start by recording your first reflection to get personalized insights."]
                })
            
            prompt = f"""You are a compassionate mental wellness assistant. Based on the user's recent voice reflections below, provide 3-5 short, actionable, and empathetic tips to help them manage their emotions and maintain well-being.

Recent reflections:
{chr(10).join(f"- {t}" for t in transcriptions)}

Provide ONLY a numbered list of 3-5 tips, each on a new line. Keep each tip to 1-2 sentences. Be supportive and practical."""

        elif topic == 'stress':
            # Use stress score and notes from inputs
            stress_level = inputs.get('stress', 0)
            overwhelm = inputs.get('overwhelm', 0)
            energy = inputs.get('energy', 0)
            notes = inputs.get('notes', '')
            
            score = round(((stress_level + overwhelm + (10 - energy)) / 30) * 100)
            
            prompt = f"""You are a mental wellness assistant. A user just completed a stress check with the following results:

Stress Score: {score}/100
Stress Level: {stress_level}/10
Overwhelm Level: {overwhelm}/10
Energy Level: {energy}/10
Additional Notes: {notes if notes else "None provided"}

Provide 3-5 short, actionable tips to help them manage their current stress level. Keep each tip to 1-2 sentences. Be practical and supportive.

Provide ONLY a numbered list of 3-5 tips, each on a new line."""

        else:
            # Generic fallback
            prompt = """Provide 3 general wellness tips for maintaining balance and managing stress. Keep each tip to 1-2 sentences.

Provide ONLY a numbered list of 3 tips, each on a new line."""
        
        response = model.generate_content(prompt)
        suggestions_text = response.text.strip()
        
        # Parse numbered list into array
        suggestions = []
        for line in suggestions_text.split('\n'):
            line = line.strip()
            # Remove numbering (1. 2. etc) or bullets
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                # Strip leading number/bullet
                cleaned = line.lstrip('0123456789.-•* ').strip()
                if cleaned:
                    suggestions.append(cleaned)
        
        return jsonify({
            'topic': topic,
            'suggestions': suggestions if suggestions else [suggestions_text]
        })
        
    except Exception as e:
        print(f"Error generating insights: {e}")
        return jsonify({
            'topic': topic,
            'suggestions': SAMPLE_INSIGHTS.get(topic, SAMPLE_INSIGHTS['general'])
        })


# ============================================================================
# LLM 2: PACING ADVICE GENERATOR
# Page: /pacing-advice
# ============================================================================

@app.route('/api/pacing-advice', methods=['POST'])
@login_required
def generate_pacing_advice():
    """LLM 2: Generate personalized pacing paragraphs for focus/recovery/connection rituals."""
    try:
        user_uid = session.get('firebase_uid')
        credentials_dict = session.get('credentials')
        
        # Gather all inputs
        transcriptions = get_user_transcriptions_text(user_uid, limit=10)
        events = get_user_calendar_events(credentials_dict, days_ahead=7)
        event_density = count_events_by_day(events)
        
        # Get latest stress score from request or default
        payload = request.json or {}
        latest_stress = payload.get('stress_score', 50)
        
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt = f"""You are a productivity and wellness coach. Help the user design their week intelligently based on the following data:

VOICE REFLECTIONS:
{chr(10).join(f"- {t}" for t in transcriptions) if transcriptions else "No recent reflections"}

CALENDAR OVERVIEW (next 7 days):
- Total upcoming events: {len(events)}
- Busiest days: {', '.join(f"{day} ({count} events)" for day, count in sorted(event_density.items(), key=lambda x: x[1], reverse=True)[:3]) if event_density else "No events scheduled"}

STRESS LEVEL: {latest_stress}/100

Based on this, create a personalized pacing plan with three sections:

1. **Focus Rituals**: Specific strategies for deep work and concentration
2. **Recovery Rituals**: Specific ways to recharge and prevent burnout
3. **Connection Rituals**: Specific ways to maintain relationships and community

For each section, write a SHORT paragraph (2-4 sentences) with concrete, actionable advice tailored to their situation. Consider their stress level, calendar density, and recent reflections.

Format your response as:
**Focus Rituals**
[paragraph]

**Recovery Rituals**
[paragraph]

**Connection Rituals**
[paragraph]"""

        response = model.generate_content(prompt)
        advice_text = response.text.strip()
        
        # Parse sections
        sections = {
            'focus': '',
            'recovery': '',
            'connection': ''
        }
        
        # Simple parsing
        current_section = None
        lines = advice_text.split('\n')
        for line in lines:
            line_lower = line.lower()
            if 'focus' in line_lower and '**' in line:
                current_section = 'focus'
            elif 'recovery' in line_lower and '**' in line:
                current_section = 'recovery'
            elif 'connection' in line_lower and '**' in line:
                current_section = 'connection'
            elif current_section and line.strip() and not line.startswith('**'):
                sections[current_section] += line.strip() + ' '
        
        return jsonify({
            'focus': sections['focus'].strip() or 'Block dedicated time for deep work daily.',
            'recovery': sections['recovery'].strip() or 'Schedule regular breaks between tasks.',
            'connection': sections['connection'].strip() or 'Make time for meaningful relationships.',
            'raw_advice': advice_text
        })
        
    except Exception as e:
        print(f"Error generating pacing advice: {e}")
        return jsonify({
            'focus': 'Block a protected hour for deep work, then follow it with a deliberate pause.',
            'recovery': 'Pair high-effort tasks with restorative breaks to avoid compounding stress.',
            'connection': 'Schedule time for meaningful connections with colleagues or friends.',
            'error': str(e)
        }), 500


# ============================================================================
# LLM 3: SMART BREAK SCHEDULER
# Page: /calendar
# ============================================================================

@app.route('/api/smart-breaks', methods=['POST'])
@login_required
def generate_smart_breaks():
    """LLM 3: Generate and optionally schedule smart breaks based on stress and calendar."""
    try:
        user_uid = session.get('firebase_uid')
        credentials_dict = session.get('credentials')
        payload = request.json or {}
        
        # Gather inputs
        transcriptions = get_user_transcriptions_text(user_uid, limit=5)
        events = get_user_calendar_events(credentials_dict, days_ahead=7)
        event_density = count_events_by_day(events)
        
        # Get stress level
        stress_score = payload.get('stress_score', 50)
        auto_schedule = payload.get('auto_schedule', False)
        
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt = f"""You are a smart calendar assistant. Based on the user's data, suggest break times for the next 7 days.

STRESS LEVEL: {stress_score}/100
UPCOMING EVENTS: {len(events)} events in next 7 days
CALENDAR DENSITY: {event_density}

RECENT REFLECTIONS:
{chr(10).join(f"- {t[:100]}..." for t in transcriptions) if transcriptions else "No recent reflections"}

RULES:
- NEVER SCHEDULE between 12am-7am
- High stress (>66): Suggest 4-5 breaks per day
- Medium stress (33-66): Suggest 2-3 breaks per day
- Low stress (<33): Suggest 1-2 breaks per day

- Types: "Recovery Break" (15-30 min), "Focus Sprint" (60-90 min), "Connection Block" (30-60 min)
- Schedule breaks between existing events when possible

Provide a JSON array of break suggestions with this format:
[
  {{
    "type": "Recovery Break",
    "duration_hours": 0.5,
    "hours_from_now": 2,
    "description": "Brief description of what to do"
  }}
]

Provide ONLY valid JSON, no other text."""

        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Extract JSON from response
        import json
        import re
        
        # Try to find JSON array in response
        json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if json_match:
            breaks_data = json.loads(json_match.group())
        else:
            # Fallback: create default breaks
            num_breaks = 2 if stress_score < 33 else (3 if stress_score < 66 else 4)
            breaks_data = []
            for i in range(num_breaks):
                breaks_data.append({
                    "type": "Recovery Break" if i % 2 == 0 else "Focus Sprint",
                    "duration_hours": 0.5,
                    "hours_from_now": 8 + (i * 3),
                    "description": "Take a mindful break to recharge"
                })
        
        # Filter out breaks that would be scheduled in night hours (10pm-7am)
        now = datetime.datetime.utcnow()
        filtered_breaks = []
        for break_item in breaks_data:
            scheduled_time = now + datetime.timedelta(hours=break_item['hours_from_now'])
            hour = scheduled_time.hour
            if 7 <= hour < 22:  # Only between 7am-10pm
                filtered_breaks.append(break_item)
        
        # Auto-schedule if requested
        scheduled_events = []
        if auto_schedule and filtered_breaks:
            credentials = Credentials(**credentials_dict)
            service = build('calendar', 'v3', credentials=credentials)
            
            for break_item in filtered_breaks[:5]:  # Limit to 5 auto-scheduled breaks
                try:
                    start_time = now + datetime.timedelta(hours=break_item['hours_from_now'])
                    end_time = start_time + datetime.timedelta(hours=break_item['duration_hours'])
                    
                    event = {
                        'summary': f"🌿 {break_item['type']}",
                        'description': break_item.get('description', ''),
                        'start': {
                            'dateTime': start_time.isoformat() + 'Z',
                            'timeZone': 'UTC',
                        },
                        'end': {
                            'dateTime': end_time.isoformat() + 'Z',
                            'timeZone': 'UTC',
                        },
                    }
                    
                    created = service.events().insert(calendarId='primary', body=event).execute()
                    scheduled_events.append(created.get('id'))
                except Exception as e:
                    print(f"Error scheduling break: {e}")
        
        return jsonify({
            'suggestions': filtered_breaks,
            'scheduled_count': len(scheduled_events),
            'scheduled_ids': scheduled_events,
            'stress_level': stress_score
        })
        
    except Exception as e:
        print(f"Error generating smart breaks: {e}")
        return jsonify({
            'suggestions': [],
            'error': str(e)
        }), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000, host='localhost')
