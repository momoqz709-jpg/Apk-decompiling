import os
import time
import json
import subprocess
import io
from google import genai
from google.genai import types
from PIL import Image

print("[Vision AI] Initializing Gemini client...")
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

SERIAL = os.environ["TARGET_DEVICE"]
PACKAGE = os.environ["PACKAGE"]
EMAIL = os.environ["TEST_EMAIL"]
PASSWORD = os.environ["TEST_PASSWORD"]
ADB = ["adb", "-s", SERIAL]


def sh(args):
    return subprocess.run(ADB + args, capture_output=True, text=True)


def take_screenshot():
    print("[Vision AI] Taking screenshot...")
    sh(["shell", "screencap", "-p", "/sdcard/screen.png"])
    sh(["pull", "/sdcard/screen.png", "screen.png"])
    return Image.open("screen.png")


def ask_ai(prompt, img):
    try:
        print("[Vision AI] Sending image to Gemini...")
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_bytes = img_byte_arr.getvalue()
        image_part = types.Part.from_bytes(data=img_bytes, mime_type="image/png")
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=[prompt, image_part],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                timeout=30.0
            )
        )
        print("[Vision AI] Response received")
        return json.loads(response.text)
    except Exception as e:
        print(f"[Vision AI] AI Error: {e}")
        return None


print("[Vision AI] Starting app...")
sh(["shell", "am", "force-stop", PACKAGE])
time.sleep(2)
sh(["shell", "monkey", "-p", PACKAGE, "1"])
time.sleep(10)

for step in range(15):
    print(f"\n[Vision AI] Step {step}: Capturing screen...")
    img = take_screenshot()
    prompt_text = (
        "Analysiere diesen Android-Screenshot der App " + PACKAGE + ". "
        "Identifiziere UI-Elemente für den Login. "
        "Gib NUR JSON zurück im Format: "
        "{\"action\": \"tap_email|tap_password|tap_login|wait|success|dismiss_dialog\", "
        "\"x\": <pixel_x>, \"y\": <pixel_y>, \"reason\": \"<text>\"} "
        "Regeln: "
        "1. Wenn die App nicht im Vordergrund ist oder ein Dialog erscheint: Tippe auf die App oder dismiss_dialog. "
        "2. Login-Screen: Tippe Email-Feld, dann Passwort-Feld, dann Login-Button. "
        "3. Splash/Loading: Warte (wait, x=0, y=0). "
        "4. Home/Dashboard DER APP sichtbar: Erfolg (success). "
        "Nutze diese Email: " + EMAIL + " und dieses Passwort: " + PASSWORD
    )
    result = ask_ai(prompt_text, img)
    if not result:
        print("[Vision AI] No result, waiting...")
        time.sleep(3)
        continue
    action = result.get("action", "wait")
    x = result.get("x", 0)
    y = result.get("y", 0)
    reason = result.get("reason", "")
    print(f"[Vision AI] Action: {action} at ({x},{y}) | Reason: {reason}")
    if action == "success":
        print("[Vision AI] Login erfolgreich abgeschlossen!")
        break
    elif action == "wait":
        time.sleep(4)
        continue
    elif action == "dismiss_dialog":
        sh(["shell", "input", "tap", str(x), str(y)])
        time.sleep(2)
    elif action in ["tap_email", "tap_password", "tap_login"]:
        if x > 0 and y > 0:
            sh(["shell", "input", "tap", str(x), str(y)])
            time.sleep(1)
            if action == "tap_email":
                sh(["shell", "input", "text", EMAIL])
                sh(["shell", "input", "keyevent", "66"])
            elif action == "tap_password":
                sh(["shell", "input", "text", PASSWORD])
                sh(["shell", "input", "keyevent", "66"])
            time.sleep(2)

print("[Vision AI] Warte auf finale Netzwerk-Requests...")
time.sleep(15)
