# Text-to-Speech Feature for Insights

## ✅ What Was Added

Added ElevenLabs text-to-speech functionality for the **Assistant Insights** on the `/vent` and `/stress-check` pages.

---

## 🎯 How It Works

### Backend (`app.py`)
**New Endpoint:** `/api/insights/tts` (POST)
- Accepts JSON with `text` field
- Uses ElevenLabs API to convert text to speech
- Uses "Adam" voice (calm and professional)
- Returns MP3 audio file

```python
@app.route('/api/insights/tts', methods=['POST'])
@login_required
def insights_text_to_speech():
    # Generates audio using ElevenLabs
    audio_generator = elevenlabs.text_to_speech.convert(
        text=text,
        voice_id="pNInz6obpgDQGcFmaJgB",  # Adam voice
        model_id="eleven_multilingual_v2"
    )
```

### Frontend (`main.js`)
**Updated Function:** `handleInsights()`
- Adds 🔊 speaker button next to each insight
- Only appears for `vent` and `stress` topics
- Click to hear the insight spoken aloud

**New Function:** `playInsightAudio(text, buttonEl)`
- Fetches audio from backend
- Manages audio playback
- Shows ⏸️ while playing
- Stops previous audio when new one starts
- Auto-cleans up when finished

### Styling (`style.css`)
**New Class:** `.tts-button`
- Transparent background
- Hover effect (enlarges slightly)
- Smooth transitions
- Disabled state when playing

---

## 🎨 User Experience

### Before
- User reads insights silently
- No audio feedback

### After
1. User gets insights on `/vent` or `/stress-check`
2. Each insight has a 🔊 speaker button
3. Click button to hear insight read aloud
4. Button changes to ⏸️ while playing
5. Audio auto-stops when finished
6. Click another button to hear different insight (stops previous audio)

---

## 🔊 Voice Details

**Voice:** Adam (pNInz6obpgDQGcFmaJgB)
- Calm and professional tone
- Good for wellness/mental health content
- Clear articulation

**Model:** eleven_multilingual_v2
- High-quality speech synthesis
- Natural intonation
- Supports multiple languages

---

## 🧪 Testing

**To Test:**
1. Go to `/vent` page
2. Record a voice reflection (or use existing ones)
3. Insights will appear with 🔊 buttons
4. Click speaker icon to hear the insight
5. Verify:
   - ✓ Audio plays clearly
   - ✓ Button changes to ⏸️ while playing
   - ✓ Button returns to 🔊 when finished
   - ✓ Clicking another button stops previous audio

**To Test Stress:**
1. Go to `/stress-check` page
2. Complete the stress assessment
3. Submit to see insights
4. Click 🔊 buttons to hear insights

---

## 📝 Technical Notes

- **Audio Format:** MP3 (widely supported)
- **Playback:** HTML5 Audio API
- **Error Handling:** Graceful fallback with alert message
- **Resource Cleanup:** Audio URLs are revoked after playback
- **Single Audio:** Only one insight plays at a time
- **Session Required:** TTS endpoint requires login

---

## 🎯 Pages Affected

- ✅ `/vent` - Vent page insights (TTS enabled)
- ✅ `/stress-check` - Stress test insights (TTS enabled)
- ⚪ `/pacing-advice` - Pacing advice (TTS NOT enabled - can be added if needed)

---

## 🚀 Status: ✅ READY

Restart your Flask server and test the TTS feature on the vent and stress-check pages!
