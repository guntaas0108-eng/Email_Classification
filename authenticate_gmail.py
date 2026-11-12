from pathlib import Path
import os
import webbrowser
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

BASE_DIR = Path(__file__).resolve().parent
CLIENT_PATH = BASE_DIR / "credentials.json"
TOKEN_PATH = BASE_DIR / "token.json"
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def authenticate():
    if not CLIENT_PATH.exists():
        print("ERROR: credentials.json not found in", BASE_DIR)
        return

    print("=" * 60)
    print("GMAIL AUTHENTICATION WIZARD")
    print("=" * 60)
    print("Starting authentication server...")

    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_PATH), SCOPES)
    
    # Run local server and print url
    print("\nA browser window will open shortly.")
    print("If it does not open automatically, copy and paste the URL from above into your browser.")
    print("\nSign in with your Google account (e.g. gsingh15_be24@thapar.edu).")
    print("When Google warns 'Google hasn't verified this app':")
    print("  1. Click 'Advanced'")
    print("  2. Click 'Go to UniMail Classifier (unsafe)'")
    print("  3. Click 'Continue' to allow read-only access.\n")

    creds = flow.run_local_server(port=0, open_browser=True)

    TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
    print(f"\nSUCCESS! Token saved to: {TOKEN_PATH.name}")

    service = build("gmail", "v1", credentials=creds)
    profile = service.users().getProfile(userId="me").execute()
    print("Authenticated Account:", profile.get("emailAddress"))
    print("Total Messages:", profile.get("messagesTotal"))
    print("=" * 60)
    print("Now return to the web app (http://localhost:8501) and click 'Sign in & Classify Inbox'.")
    print("It will instantly sync your emails without asking for login again!")
    print("=" * 60)

if __name__ == "__main__":
    authenticate()
