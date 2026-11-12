from pathlib import Path
import json
import base64
from bs4 import BeautifulSoup
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import joblib
import pandas as pd

ROOT = Path(__file__).resolve().parent
TOKEN_PATH = ROOT / "token.json"
MODEL_PATH = ROOT / "models" / "best_email_classifier.joblib"
FRAUD_MODEL_PATH = ROOT / "models" / "best_fraud_detector.joblib"
OUT_CSV = ROOT / "outputs" / "cached_classified_inbox.csv"
OUT_ACC = ROOT / "outputs" / "cached_user_account.json"

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def decode_part(data):
    if not data:
        return ""
    data += "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

def extract_body(payload):
    plain, html_parts = [], []
    def walk(part):
        mime = part.get("mimeType", "")
        data = part.get("body", {}).get("data")
        if data and mime == "text/plain":
            plain.append(decode_part(data))
        elif data and mime == "text/html":
            html_parts.append(BeautifulSoup(decode_part(data), "html.parser").get_text(" ", strip=True))
        for child in part.get("parts", []):
            walk(child)
    walk(payload)
    return "\n".join(plain or html_parts)

def get_header(headers, wanted):
    for h in headers:
        if h.get("name", "").lower() == wanted.lower():
            return h.get("value", "")
    return ""

def main():
    if not TOKEN_PATH.exists():
        print("token.json not found")
        return
    creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    service = build("gmail", "v1", credentials=creds)

    profile = service.users().getProfile(userId="me").execute()
    account = profile.get("emailAddress", "")
    print(f"Connecting to: {account}")

    # Fetch 100 recent emails
    resp = service.users().messages().list(userId="me", maxResults=100, includeSpamTrash=False).execute()
    messages = resp.get("messages", [])
    print(f"Found {len(messages)} messages. Fetching contents...")

    rows = []
    for item in messages:
        m = service.users().messages().get(userId="me", id=item["id"], format="full").execute()
        p = m.get("payload", {})
        h = p.get("headers", [])
        body = extract_body(p)
        rows.append({
            "email_id": item["id"],
            "date": get_header(h, "Date"),
            "received_at": m.get("internalDate"),
            "sender": get_header(h, "From"),
            "subject": get_header(h, "Subject"),
            "body": body,
        })

    print(f"Fetched {len(rows)} messages. Classifying...")
    m_cat = joblib.load(MODEL_PATH)
    m_fraud = joblib.load(FRAUD_MODEL_PATH)

    texts = [f"{r.get('subject', '')} {r.get('body', '')}".strip() for r in rows]
    df = pd.DataFrame(rows)
    df["predicted_category"] = [str(x) for x in m_cat.predict(texts)]

    preds = m_fraud.predict(texts)
    df["is_fraud"] = preds
    df["fraud_status"] = ["Fraudulent" if p == 1 else "Legitimate" for p in preds]
    if hasattr(m_fraud, "predict_proba"):
        probs = m_fraud.predict_proba(texts)[:, 1]
        df["fraud_confidence_pct"] = (probs * 100).round(1)
    else:
        df["fraud_confidence_pct"] = [95.0 if p == 1 else 5.0 for p in preds]

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CSV, index=False)
    print(f"Successfully saved {len(df)} classified emails to: {OUT_CSV}")

    with open(OUT_ACC, "w", encoding="utf-8") as f:
        json.dump({"account": account, "total_messages": profile.get("messagesTotal", 0)}, f)
    print(f"Saved account profile for: {account}")

if __name__ == "__main__":
    main()
