"""
Direct test of LLM functionality without Flask authentication
Tests the Gemini API integration directly
"""

import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


def test_gemini_connection():
    """Test basic Gemini API connection"""
    print("\n=== Testing Gemini API Connection ===")
    
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt = "Say 'Hello, I'm working!' in exactly 3 words."
        response = model.generate_content(prompt)
        
        print(f"✓ Connection successful!")
        print(f"Response: {response.text}")
        return True
        
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False


def test_insights_generation():
    """Test LLM 1: Insights generation logic"""
    print("\n=== Testing Insights Generation ===")
    
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Simulate vent scenario
        transcriptions = [
            "Had a really tough meeting today, feeling stressed about the project deadline",
            "Can't sleep well, too many things on my mind",
            "Managed to take a walk during lunch, felt slightly better"
        ]
        
        prompt = f"""You are a compassionate mental wellness assistant. Based on the user's recent voice reflections below, provide 3-5 short, actionable, and empathetic tips to help them manage their emotions and maintain well-being.

Recent reflections:
{chr(10).join(f"- {t}" for t in transcriptions)}

Provide ONLY a numbered list of 3-5 tips, each on a new line. Keep each tip to 1-2 sentences. Be supportive and practical."""

        response = model.generate_content(prompt)
        suggestions_text = response.text.strip()
        
        # Parse numbered list
        suggestions = []
        for line in suggestions_text.split('\n'):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                cleaned = line.lstrip('0123456789.-•* ').strip()
                if cleaned:
                    suggestions.append(cleaned)
        
        print(f"✓ Generated {len(suggestions)} suggestions:")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"  {i}. {suggestion}")
        
        return len(suggestions) > 0
        
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False


def test_pacing_advice_generation():
    """Test LLM 2: Pacing advice generation logic"""
    print("\n=== Testing Pacing Advice Generation ===")
    
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Simulate scenario
        transcriptions = ["Feeling overwhelmed with back-to-back meetings"]
        event_density = {"2025-10-06": 8, "2025-10-07": 3, "2025-10-08": 5}
        stress_score = 70
        
        prompt = f"""You are a productivity and wellness coach. Help the user design their week intelligently based on the following data:

VOICE REFLECTIONS:
{chr(10).join(f"- {t}" for t in transcriptions) if transcriptions else "No recent reflections"}

CALENDAR OVERVIEW (next 7 days):
- Busiest days: {', '.join(f"{day} ({count} events)" for day, count in sorted(event_density.items(), key=lambda x: x[1], reverse=True)[:3])}

STRESS LEVEL: {stress_score}/100

Based on this, create a personalized pacing plan with three sections:

1. **Focus Rituals**: Specific strategies for deep work and concentration
2. **Recovery Rituals**: Specific ways to recharge and prevent burnout
3. **Connection Rituals**: Specific ways to maintain relationships and community

For each section, write a SHORT paragraph (2-4 sentences) with concrete, actionable advice tailored to their situation.

Format your response as:
**Focus Rituals**
[paragraph]

**Recovery Rituals**
[paragraph]

**Connection Rituals**
[paragraph]"""

        response = model.generate_content(prompt)
        advice_text = response.text.strip()
        
        print(f"✓ Generated pacing advice:")
        print(advice_text[:300] + "..." if len(advice_text) > 300 else advice_text)
        
        return len(advice_text) > 0
        
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False


def test_smart_breaks_generation():
    """Test LLM 3: Smart break generation logic"""
    print("\n=== Testing Smart Breaks Generation ===")
    
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        stress_score = 75
        event_density = {"2025-10-06": 6, "2025-10-07": 4}
        
        prompt = f"""You are a smart calendar assistant. Based on the user's data, suggest break times for the next 7 days.

STRESS LEVEL: {stress_score}/100
CALENDAR DENSITY: {event_density}

RULES:
- High stress (>66): Suggest 4-5 breaks per day
- Medium stress (33-66): Suggest 2-3 breaks per day
- Low stress (<33): Suggest 1-2 breaks per day
- Avoid scheduling between 10pm-7am
- Types: "Recovery Break" (15-30 min), "Focus Sprint" (60-90 min), "Connection Block" (30-60 min)

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
        
        # Try to extract JSON
        import json
        import re
        
        json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if json_match:
            breaks_data = json.loads(json_match.group())
            print(f"✓ Generated {len(breaks_data)} break suggestions:")
            for i, break_item in enumerate(breaks_data[:3], 1):  # Show first 3
                print(f"  {i}. {break_item.get('type')} - {break_item.get('duration_hours')}h")
                print(f"     {break_item.get('description', 'N/A')}")
            return True
        else:
            print(f"✗ Could not parse JSON from response")
            print(f"Response preview: {response_text[:200]}")
            return False
        
    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 70)
    print("Direct LLM Functionality Test (No Authentication Required)")
    print("=" * 70)
    
    # Check API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("\n✗ ERROR: GEMINI_API_KEY not found in .env file")
        print("Please add your Gemini API key to the .env file")
        exit(1)
    else:
        print(f"\n✓ Found API key: {api_key[:10]}...{api_key[-5:]}")
    
    results = []
    
    # Run all tests
    results.append(("Gemini Connection", test_gemini_connection()))
    results.append(("Insights Generation", test_insights_generation()))
    results.append(("Pacing Advice", test_pacing_advice_generation()))
    results.append(("Smart Breaks", test_smart_breaks_generation()))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    for name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{name}: {status}")
    
    total_passed = sum(1 for _, passed in results if passed)
    print(f"\nTotal: {total_passed}/{len(results)} tests passed")
    
    if total_passed == len(results):
        print("\n✓ All tests passed! LLM integration is working correctly.")
    else:
        print(f"\n⚠ {len(results) - total_passed} test(s) failed. Check the errors above.")
