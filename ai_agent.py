# ai_agent.py - Autonomous Vision AI for Android UI Automation (Gemini Edition)
import os
import subprocess
import json
import time
import sys
from PIL import Image
import google.generativeai as genai

# Initialize Gemini Client (Uses the API key from GitHub Secrets)
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# gemini-2.0-flash is extremely fast and has excellent vision/spatial reasoning
model = genai.GenerativeModel("gemini-2.0-flash")

def run_cmd(cmd):
    subprocess.run(cmd, shell=True, check=True)

def take_screenshot():
    """Captures the current emulator screen and loads it as a PIL Image."""
    run_cmd("adb exec-out screencap -p > screen.png")
    return Image.open("screen.png")

def ask_ai(prompt, max_retries=3):
    """Sends the screenshot to Gemini and asks for element coordinates."""
    img = take_screenshot()
    for i in range(max_retries):
        try:
            # Force Gemini to return strict JSON
            response = model.generate_content(
                [prompt, img],
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json"
                )
            )
            # Parse the JSON response
            data = json.loads(response.text)
            box = data['box']
            # Calculate the center of the bounding box to tap
            x = (box[0] + box[2]) // 2
            y = (box[1] + box[3]) // 2
            return x, y
        except Exception as e:
            print(f"⚠️ Gemini attempt {i+1} failed: {e}")
            time.sleep(2)
    raise Exception("❌ AI failed to return valid coordinates after retries.")

def tap(x, y):
    print(f"👆 Tapping ({x}, {y})")
    run_cmd(f"adb shell input tap {x} {y}")

def type_text(text):
    # ADB input text requires escaping spaces. 
    text = text.replace(" ", "%s")
    run_cmd(f"adb shell input text '{text}'")
    # Hide the keyboard so it doesn't block the next element
    run_cmd("adb shell input keyevent 111") 

def check_success():
    """Asks Gemini to verify if the login was successful."""
    img = take_screenshot()
    response = model.generate_content(
        ["Does this screen indicate a successful login? (e.g., shows a Home screen, Dashboard, Welcome message, or Feed). Answer with ONLY a JSON object: {\"success\": true/false, \"reason\": \"...\"}", img],
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json"
        )
    )
    data = json.loads(response.text)
    return data.get('success', False), data.get('reason', '')

# ==========================================
# 🤖 AUTONOMOUS EXECUTION FLOW
# ==========================================
print("🤖 AI Vision Agent Started (Powered by Gemini)")

# 1. Find and fill Username
print("👁️ Looking for Username/Email field...")
x, y = ask_ai("Find the bounding box of the Username, Email, or Phone input field. Return JSON: {\"box\": [x1, y1, x2, y2]}")
tap(x, y)
time.sleep(1)
type_text("test_user@example.com")

# 2. Find and fill Password
print("👁️ Looking for Password field...")
x, y = ask_ai("Find the bounding box of the Password input field. Return JSON: {\"box\": [x1, y1, x2, y2]}")
tap(x, y)
time.sleep(1)
# Using a simple alphanumeric password to avoid ADB input text special character bugs
type_text("TestPassword123") 

# 3. Find and tap Login Button
print("👁️ Looking for Login/Sign In button...")
x, y = ask_ai("Find the bounding box of the Login, Sign In, or Submit button. Return JSON: {\"box\": [x1, y1, x2, y2]}")
tap(x, y)

# 4. Verify Success
print("⏳ Waiting for login to process...")
time.sleep(5)
print("👁️ Verifying login success...")
success, reason = check_success()
if success:
    print(f"✅ Login successful! Reason: {reason}")
else:
    print(f"❌ Login failed or stuck. Reason: {reason}")
    sys.exit(1)
