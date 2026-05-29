"""
Test if the Gemini API key in .env (or env vars) actually works.

Usage:
  python scripts/test_gemini_key.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(ROOT, ".env"))

key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

print("=" * 60)
print("GEMINI API KEY TEST")
print("=" * 60)

if not key:
    print("[FAIL] No GEMINI_API_KEY or GOOGLE_API_KEY found in env / .env")
    sys.exit(1)

masked = key[:10] + "..." + key[-4:]
print(f"Key loaded: {masked}")
print(f"Source: .env file or environment variable")
print()

try:
    from google import genai
    client = genai.Client(api_key=key)
    print("Client initialized. Sending test request to gemini-2.0-flash...")
    print()
    r = client.models.generate_content(
        model="gemini-2.0-flash",
        contents="Reply with the exact text: API KEY OK",
    )
    response_text = (r.text or "").strip()
    print(f"[SUCCESS] Gemini responded: {response_text!r}")
    print()
    print("=" * 60)
    print("KEY IS WORKING. You can run generate_clinical_use.py")
    print("=" * 60)
    sys.exit(0)
except Exception as e:
    print(f"[FAIL] Gemini call raised: {type(e).__name__}")
    print(f"        {str(e)[:500]}")
    print()
    print("=" * 60)
    if "API_KEY_INVALID" in str(e) or "expired" in str(e).lower():
        print("KEY IS EXPIRED OR INVALID. Get a new one at:")
        print("   https://aistudio.google.com/apikey")
    elif "quota" in str(e).lower() or "RESOURCE_EXHAUSTED" in str(e):
        print("KEY HIT A QUOTA / RATE LIMIT. Try again in a minute,")
        print("or use a different key.")
    else:
        print("KEY FAILED. See error above.")
    print("=" * 60)
    sys.exit(1)
