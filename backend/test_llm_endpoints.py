"""
Test script for the three LLM endpoints
Run this after logging in and getting a valid session
"""

import requests
import json

BASE_URL = "http://localhost:5000"

def test_insights_vent():
    """Test LLM 1: Assistant Insights for /vent page"""
    print("\n=== Testing LLM 1: Assistant Insights (Vent) ===")
    
    response = requests.post(
        f"{BASE_URL}/api/insights",
        json={
            "topic": "vent",
            "inputs": {}
        }
    )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Topic: {data.get('topic')}")
        print("Suggestions:")
        for i, suggestion in enumerate(data.get('suggestions', []), 1):
            print(f"  {i}. {suggestion}")
    else:
        print(f"Error: {response.text}")
    
    return response.status_code == 200


def test_insights_stress():
    """Test LLM 1: Assistant Insights for /stress-check page"""
    print("\n=== Testing LLM 1: Assistant Insights (Stress) ===")
    
    response = requests.post(
        f"{BASE_URL}/api/insights",
        json={
            "topic": "stress",
            "inputs": {
                "stress": 7,
                "overwhelm": 8,
                "energy": 3,
                "notes": "Feeling overwhelmed with deadlines and not sleeping well"
            }
        }
    )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Topic: {data.get('topic')}")
        print("Suggestions:")
        for i, suggestion in enumerate(data.get('suggestions', []), 1):
            print(f"  {i}. {suggestion}")
    else:
        print(f"Error: {response.text}")
    
    return response.status_code == 200


def test_pacing_advice():
    """Test LLM 2: Pacing Advice Generator"""
    print("\n=== Testing LLM 2: Pacing Advice Generator ===")
    
    response = requests.post(
        f"{BASE_URL}/api/pacing-advice",
        json={
            "stress_score": 65
        }
    )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("\nFocus Rituals:")
        print(f"  {data.get('focus', 'N/A')}")
        print("\nRecovery Rituals:")
        print(f"  {data.get('recovery', 'N/A')}")
        print("\nConnection Rituals:")
        print(f"  {data.get('connection', 'N/A')}")
        if 'raw_advice' in data:
            print("\n--- Raw Advice ---")
            print(data['raw_advice'])
    else:
        print(f"Error: {response.text}")
    
    return response.status_code == 200


def test_smart_breaks():
    """Test LLM 3: Smart Break Scheduler"""
    print("\n=== Testing LLM 3: Smart Break Scheduler ===")
    
    response = requests.post(
        f"{BASE_URL}/api/smart-breaks",
        json={
            "stress_score": 75,
            "auto_schedule": False  # Don't actually schedule for testing
        }
    )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Stress Level: {data.get('stress_level')}/100")
        print(f"Number of suggestions: {len(data.get('suggestions', []))}")
        print("\nBreak Suggestions:")
        for i, break_item in enumerate(data.get('suggestions', []), 1):
            print(f"  {i}. {break_item.get('type')} - {break_item.get('duration_hours')}h")
            print(f"     In {break_item.get('hours_from_now')} hours")
            print(f"     Description: {break_item.get('description', 'N/A')}")
    else:
        print(f"Error: {response.text}")
    
    return response.status_code == 200


if __name__ == "__main__":
    print("=" * 60)
    print("LLM Endpoints Testing Suite")
    print("=" * 60)
    print("\nNOTE: You must be logged in for these tests to work.")
    print("If you get 302 redirects, open http://localhost:5000 in a browser")
    print("and log in first, then run these tests.")
    print("=" * 60)
    
    results = []
    
    # Test all endpoints
    results.append(("Insights (Vent)", test_insights_vent()))
    results.append(("Insights (Stress)", test_insights_stress()))
    results.append(("Pacing Advice", test_pacing_advice()))
    results.append(("Smart Breaks", test_smart_breaks()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{name}: {status}")
    
    total_passed = sum(1 for _, passed in results if passed)
    print(f"\nTotal: {total_passed}/{len(results)} tests passed")
