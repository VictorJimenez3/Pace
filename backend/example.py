import os
from dotenv import load_dotenv
from io import BytesIO
import requests
from elevenlabs.client import ElevenLabs
import firebase_admin
from firebase_admin import credentials, firestore
import datetime

load_dotenv()

# Firebase setup
if not firebase_admin._apps:
    cred = credentials.Certificate('firebase-adminsdk.json')
    firebase_admin.initialize_app(cred)
db = firestore.client()

elevenlabs = ElevenLabs(
  api_key=os.getenv("ELEVENLABS_API_KEY"),
)

audio_url = (
    "https://storage.googleapis.com/eleven-public-cdn/audio/marketing/nicole.mp3"
)
response = requests.get(audio_url)
audio_data = BytesIO(response.content)

transcription = elevenlabs.speech_to_text.convert(
    file=audio_data,
    model_id="scribe_v1",
    tag_audio_events=True,
    language_code="eng",
    diarize=False,
)

# Store transcription in Firebase
user_id = "test_user_123"  # Replace with actual user ID from session
transcription_data = {
    'text': transcription.text,
    'created_at': datetime.datetime.utcnow(),
    'audio_processed_at': datetime.datetime.utcnow(),
    'language': transcription.language_code,
    'user_id': user_id
}

# Add to 'transcriptions' collection
transcription_ref = db.collection('transcriptions').add(transcription_data)
print(f"Transcription stored with ID: {transcription_ref[1].id}")
print(f"Text: {transcription.text}")