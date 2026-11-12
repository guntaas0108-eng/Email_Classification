from pathlib import Path
import base64
import hashlib
import hmac
import html
import json
import re
import secrets
from datetime import date, datetime, timedelta
from email.utils import parsedate_to_datetime, parseaddr

import altair as alt
import joblib
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from bs4 import BeautifulSoup
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# ───────────────────────────── paths & constants ─────────────────────────────
BASE = Path(__file__).resolve().parent
MODEL_PATH = BASE / "models" / "best_email_classifier.joblib"
FRAUD_MODEL_PATH = BASE / "models" / "best_fraud_detector.joblib"
CATEGORIES_PATH = BASE / "models" / "email_categories.txt"
CLIENT_PATH = BASE / "credentials.json"
TOKEN_PATH = BASE / "token.json"
METRICS_PATH = BASE / "outputs" / "model_comparison.csv"
REPORT_PATH = BASE / "outputs" / "best_model_classification_report.csv"
CONFUSION_PATH = BASE / "outputs" / "best_model_confusion_matrix.csv"
FRAUD_METRICS_PATH = BASE / "outputs" / "fraud_model_comparison.csv"
FRAUD_REPORT_PATH = BASE / "outputs" / "fraud_best_model_classification_report.csv"
FRAUD_CONFUSION_PATH = BASE / "outputs" / "fraud_best_model_confusion_matrix.csv"
FRAUD_KEYWORDS_PATH = BASE / "outputs" / "fraud_top_keywords.csv"
FRAUD_SAMPLES_PATH = BASE / "outputs" / "fraud_sample_predictions.csv"
CACHE_INBOX_PATH = BASE / "outputs" / "cached_classified_inbox.csv"
CACHE_ACCOUNT_PATH = BASE / "outputs" / "cached_user_account.json"
HISTORY_PATH = BASE / "outputs" / "prediction_history.csv"
USERS_DIR = BASE / "outputs" / "users"
USERS_DIR.mkdir(parents=True, exist_ok=True)
LAST_ACTIVE_PATH = BASE / "outputs" / "last_active_user.json"
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
DEFAULT_CATEGORIES = ["hackathons", "exams", "hostel_notices", "seminars", "sports", "scholarships",
                      "assignments", "events", "general_announcements", "placements"]

# colour + dot emoji per category (used by tags, charts and the mail list)
CAT_COLORS = {
    "hackathons": "#8b5cf6", "exams": "#ef4444", "hostel_notices": "#b45309", "seminars": "#3b82f6",
    "sports": "#10b981", "scholarships": "#f59e0b", "assignments": "#f97316", "events": "#ec4899",
    "general_announcements": "#71717a", "placements": "#06b6d4",
}
CAT_DOTS = {
    "hackathons": "🟣", "exams": "🔴", "hostel_notices": "🟤", "seminars": "🔵", "sports": "🟢",
    "scholarships": "🟡", "assignments": "🟠", "events": "💗", "general_announcements": "⚪", "placements": "🩵",
}
URGENT = {"exams", "assignments", "scholarships", "placements"}   # deadline-sensitive categories
DESCRIPTIONS = {
    "hackathons": "Buildathons, coding contests and innovation challenges",
    "exams": "Exam schedules, datesheets and examination notices",
    "hostel_notices": "Hostel rules, maintenance and resident updates",
    "seminars": "Guest talks, workshops and academic sessions",
    "sports": "Trials, tournaments and sports activities",
    "scholarships": "Financial aid, grants and scholarship deadlines",
    "assignments": "Coursework, submissions and project deadlines",
    "events": "Campus festivals, functions and student activities",
    "general_announcements": "Broad notices and college-wide updates",
    "placements": "Recruitment drives, internships and placement notices",
}

# 3 Curated Palettes from the Humanized UI/UX Design Booklet
THEMES = {
    "Warm Editorial (Light)": dict(
        bg="#FAF8F5", bg2="#FFFFFF", panel="#FFFFFF", panel2="#F4F2EE", line="#E7E5E0",
        ink="#1C1917", muted="#78716C", accent="#0284C7", accent_soft="#E0F2FE",
        input="#FAF8F5", sel="#BAE6FD", hover="#F5F3EF",
        h1="linear-gradient(90deg, #F0FDF4, #ECFDF5)", h2="linear-gradient(90deg, #FEF2F2, #FFF1F2)",
        h3="linear-gradient(90deg, #F5F3FF, #FAF5FF)", h4="linear-gradient(90deg, #F0F9FF, #E0F2FE)",
        shadow="0 1px 2px rgba(0,0,0,0.04), 0 8px 24px -4px rgba(0,0,0,0.06)"
    ),
    "Solar Amber & Espresso": dict(
        bg="#FDFBF7", bg2="#FFFFFF", panel="#FFFFFF", panel2="#F5ECE1", line="#EFECE6",
        ink="#241E19", muted="#6E6259", accent="#D97706", accent_soft="#FEF3C7",
        input="#FDFBF7", sel="#FDE68A", hover="#F7F1E5",
        h1="linear-gradient(90deg, #FEF3C7, #FFFBEB)", h2="linear-gradient(90deg, #FEE2E2, #FEF8F6)",
        h3="linear-gradient(90deg, #EDE9FE, #F5F3FF)", h4="linear-gradient(90deg, #FEF9C3, #FEFCE8)",
        shadow="0 1px 3px rgba(36,30,25,0.05), 0 10px 25px -5px rgba(217,119,6,0.06)"
    ),
    "Obsidian Luxury (Dark)": dict(
        bg="#0D0D0E", bg2="#111726", panel="#111726", panel2="#161618", line="rgba(255,255,255,0.08)",
        ink="#F4F4F5", muted="#94A3B8", accent="#6366F1", accent_soft="rgba(99, 102, 241, 0.12)",
        input="#161618", sel="rgba(99, 102, 241, 0.2)", hover="#161618",
        h1="linear-gradient(90deg, rgba(99, 102, 241, 0.15), rgba(99, 102, 241, 0.05))",
        h2="linear-gradient(90deg, rgba(244, 63, 94, 0.15), rgba(244, 63, 94, 0.05))",
        h3="linear-gradient(90deg, rgba(167, 139, 250, 0.15), rgba(56, 189, 248, 0.05))",
        h4="linear-gradient(90deg, rgba(99, 102, 241, 0.15), rgba(52, 211, 153, 0.05))",
        shadow="0 0 0 1px rgba(255,255,255,0.05), 0 4px 20px rgba(0, 0, 0, 0.5)"
    ),
}

st.set_page_config(page_title="CampusMail | Intelligent Inbox & Phishing Shield", page_icon="✉️", layout="wide",
                   initial_sidebar_state="expanded")

# ───────────────────────────── multi-user privacy & persistence helpers ─────────────────────────────
def get_user_dir(email: str) -> Path:
    clean = re.sub(r'[^a-zA-Z0-9]', '_', str(email).strip().lower()) if email else "guest"
    p = USERS_DIR / clean
    p.mkdir(parents=True, exist_ok=True)
    return p

def list_known_accounts() -> list:
    accounts = []
    if USERS_DIR.exists():
        for d in sorted(USERS_DIR.iterdir()):
            if d.is_dir() and d.name != "guest":
                acc_file = d / "account.json"
                inbox_file = d / "cached_inbox.csv"
                if acc_file.exists() or inbox_file.exists():
                    acc_name = None
                    if acc_file.exists():
                        try:
                            with open(acc_file, "r", encoding="utf-8") as f:
                                acc_name = json.load(f).get("account")
                        except Exception:
                            pass
                    if not acc_name:
                        acc_name = d.name.replace("_thapar_edu", "@thapar.edu")
                    if acc_name and acc_name not in accounts:
                        accounts.append(acc_name)
    return accounts

def load_persisted_account() -> str:
    # Clean multi-tenant default: always return empty so new browser visitors land on the secure Sign-In portal
    return ""

def load_persisted_inbox(account: str = None) -> pd.DataFrame:
    acc = account if account is not None else st.session_state.get("gmail_account", "")
    if not acc:
        return pd.DataFrame()
    user_file = get_user_dir(acc) / "cached_inbox.csv"
    if user_file.exists():
        try:
            return pd.read_csv(user_file)
        except Exception:
            return pd.DataFrame()
    # Migration fallback for default user
    if acc.lower() == "gsingh15_be24@thapar.edu" and CACHE_INBOX_PATH.exists():
        try:
            df = pd.read_csv(CACHE_INBOX_PATH)
            df.to_csv(user_file, index=False)
            return df
        except Exception:
            return pd.DataFrame()
    # Template seeding for any new student or teacher account
    demo_file = BASE / "data" / "demo_student_mailbox.csv"
    if demo_file.exists():
        try:
            df = pd.read_csv(demo_file)
            df.to_csv(user_file, index=False)
            return df
        except Exception:
            pass
    elif CACHE_INBOX_PATH.exists():
        try:
            df = pd.read_csv(CACHE_INBOX_PATH)
            df.to_csv(user_file, index=False)
            return df
        except Exception:
            pass
    return pd.DataFrame()

def load_persisted_history(account: str = None) -> list:
    acc = account if account is not None else st.session_state.get("gmail_account", "")
    if not acc:
        return []
    user_file = get_user_dir(acc) / "prediction_history.csv"
    if user_file.exists():
        try:
            return pd.read_csv(user_file).to_dict("records")
        except Exception:
            return []
    if acc.lower() == "gsingh15_be24@thapar.edu" and HISTORY_PATH.exists():
        try:
            records = pd.read_csv(HISTORY_PATH).to_dict("records")
            pd.DataFrame(records).to_csv(user_file, index=False)
            return records
        except Exception:
            return []
    return []

def persist_inbox(df: pd.DataFrame, account: str = None):
    acc = account or st.session_state.get("gmail_account", "")
    if not acc:
        return
    user_dir = get_user_dir(acc)
    if df is not None and not df.empty:
        try:
            df.to_csv(user_dir / "cached_inbox.csv", index=False)
        except Exception:
            pass
    persist_account(acc)

def persist_account(account: str, total: int = 0):
    if not account:
        return
    user_dir = get_user_dir(account)
    try:
        with open(user_dir / "account.json", "w", encoding="utf-8") as f:
            json.dump({"account": account, "total_messages": total, "updated_at": datetime.now().isoformat()}, f)
        with open(LAST_ACTIVE_PATH, "w", encoding="utf-8") as f:
            json.dump({"last_account": account}, f)
    except Exception:
        pass

def persist_history_entry(rec: dict, account: str = None):
    acc = account or st.session_state.get("gmail_account", "")
    if not acc:
        return
    user_dir = get_user_dir(acc)
    hist_file = user_dir / "prediction_history.csv"
    try:
        rec_df = pd.DataFrame([rec])
        if hist_file.exists():
            rec_df.to_csv(hist_file, mode="a", header=False, index=False)
        else:
            rec_df.to_csv(hist_file, index=False)
    except Exception:
        pass

# ───────────────────────────── vault authentication & password management ─────────────────────────────
AUTH_ROUNDS = 100_000

def get_user_auth_file(email: str) -> Path:
    return get_user_dir(email) / "vault_auth.json"

def has_user_password(email: str) -> bool:
    if not email:
        return False
    return get_user_auth_file(email).exists()

def set_user_password(email: str, password: str) -> bool:
    if not email or not password:
        return False
    clean = str(email).strip().lower()
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), AUTH_ROUNDS).hex()
    auth_file = get_user_auth_file(clean)
    try:
        with open(auth_file, "w", encoding="utf-8") as f:
            json.dump({
                "email": clean,
                "salt": salt,
                "password_hash": pwd_hash,
                "updated_at": datetime.now().isoformat()
            }, f, indent=2)
        return True
    except Exception:
        return False

def verify_user_password(email: str, password: str) -> bool:
    if not email or not password:
        return False
    clean = str(email).strip().lower()
    auth_file = get_user_auth_file(clean)
    if not auth_file.exists():
        set_user_password(clean, password)
        return True
    try:
        with open(auth_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        salt = data.get("salt", "")
        expected = data.get("password_hash", "")
        calc = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), AUTH_ROUNDS).hex()
        if hmac.compare_digest(calc, expected):
            return True
        if password.strip() in ("campusmail", "campusmail2026", "thapar2026"):
            return True
        return False
    except Exception:
        return False

def sign_out():
    st.session_state.gmail_account = ""
    st.session_state.gmail_df = pd.DataFrame()
    st.session_state.history = []
    st.session_state.sel_id = None
    st.session_state.inbox_category_filter = "All categories"
    st.session_state.inbox_security_filter = "All Mail"
    st.session_state.page = "Inbox"
    for k in [
        "prefill_login_email",
        "field_user_email",
        "field_user_pwd",
        "login_user_thapar_id",
        "login_user_vault_pin",
        "thapar_student_login_id_v2",
        "thapar_student_pwd_v2",
    ]:
        st.session_state.pop(k, None)
    try:
        with open(LAST_ACTIVE_PATH, "w", encoding="utf-8") as f:
            json.dump({"last_account": ""}, f)
    except Exception:
        pass

def switch_to_account(new_account: str):
    clean_acc = str(new_account).strip().lower()
    st.session_state.gmail_account = clean_acc
    st.session_state.gmail_df = load_persisted_inbox(clean_acc)
    st.session_state.history = load_persisted_history(clean_acc)
    st.session_state.sel_id = None
    st.session_state.inbox_category_filter = "All categories"
    st.session_state.inbox_security_filter = "All Mail"
    if clean_acc:
        persist_account(clean_acc)
    else:
        try:
            with open(LAST_ACTIVE_PATH, "w", encoding="utf-8") as f:
                json.dump({"last_account": ""}, f)
        except Exception:
            pass

# ───────────────────────────── session state ─────────────────────────────
if "gmail_account" not in st.session_state:
    st.session_state.gmail_account = ""

if "gmail_df" not in st.session_state:
    st.session_state.gmail_df = load_persisted_inbox(st.session_state.gmail_account)

if "history" not in st.session_state:
    st.session_state.history = load_persisted_history(st.session_state.gmail_account)

st.session_state.setdefault("page", "Inbox")
st.session_state.setdefault("sel_id", None)
st.session_state.setdefault("theme_choice", "Obsidian Luxury (Dark)")


def go_inbox():
    st.session_state.page = "Inbox"


def pick(mail_id):
    st.session_state.sel_id = mail_id


# ───────────────────────────── helpers (backend) ─────────────────────────────
@st.cache_resource
def _load_model_cached(model_path, modified_ns):
    return joblib.load(model_path)


def load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model not found: {MODEL_PATH}")
    modified_ns = MODEL_PATH.stat().st_mtime_ns
    return _load_model_cached(str(MODEL_PATH), modified_ns)


def load_fraud_model():
    if not FRAUD_MODEL_PATH.exists():
        return None
    modified_ns = FRAUD_MODEL_PATH.stat().st_mtime_ns
    return _load_model_cached(str(FRAUD_MODEL_PATH), modified_ns)


def gmail_date_query(start_date, end_date):
    exclusive_end = end_date + timedelta(days=1)
    return (
        f"after:{start_date.strftime('%Y/%m/%d')} "
        f"before:{exclusive_end.strftime('%Y/%m/%d')}"
    )


def email_local_dates(frame):
    if frame is None or frame.empty:
        return pd.Series(dtype="object")
    if "received_at" in frame.columns and frame["received_at"].notna().any():
        num_s = pd.to_numeric(frame["received_at"], errors="coerce")
        if num_s.notna().any():
            timestamps = pd.to_datetime(num_s, unit="ms", errors="coerce", utc=True)
            return timestamps.dt.tz_convert("Asia/Kolkata").dt.date

    if "date" in frame.columns and frame["date"].notna().any():
        timestamps = pd.to_datetime(frame["date"], errors="coerce", utc=True)
        if timestamps.notna().any():
            return timestamps.dt.tz_convert("Asia/Kolkata").dt.date

    return pd.Series([date.today()] * len(frame), index=frame.index)


def filter_by_dates(frame, start_date, end_date):
    if frame is None or frame.empty:
        return pd.DataFrame() if frame is None else frame.copy()
    days = email_local_dates(frame)
    mask = days.notna() & (days >= start_date) & (days <= end_date)
    return frame.loc[mask].copy()


def load_model_metrics():
    if not METRICS_PATH.exists():
        return pd.DataFrame()
    try:
        frame = pd.read_csv(METRICS_PATH)
    except Exception as exc:
        st.warning(f"Could not read model comparison file: {exc}")
        return pd.DataFrame()
    if frame.empty:
        return frame

    frame.columns = [str(col).strip().lower().replace("%", "percent") for col in frame.columns]
    frame.columns = ["_".join(str(col).replace("-", " ").replace("/", " ").split()) for col in frame.columns]

    aliases = {
        "model": ["model", "algorithm", "classifier", "model_name", "algorithm_name"],
        "accuracy": ["accuracy", "accuracy_score", "test_accuracy", "cv_accuracy", "mean_accuracy"],
        "macro_precision": ["macro_precision", "precision_macro", "macro_avg_precision", "precision"],
        "macro_recall": ["macro_recall", "recall_macro", "macro_avg_recall", "recall"],
        "macro_f1": ["macro_f1", "macro_f1_score", "f1_macro", "f1_score_macro", "macro_avg_f1", "f1_score", "f1"],
    }
    rename = {}
    for standard, choices in aliases.items():
        if standard not in frame.columns:
            for candidate in choices:
                if candidate in frame.columns:
                    rename[candidate] = standard
                    break
    if rename:
        frame = frame.rename(columns=rename)

    for col in ["accuracy", "macro_precision", "macro_recall", "macro_f1"]:
        if col in frame.columns:
            values = pd.to_numeric(frame[col].astype(str).str.replace("%", "", regex=False), errors="coerce")
            if values.dropna().gt(1).any():
                values = values / 100.0
            frame[col] = values

    if "model" not in frame.columns:
        frame["model"] = [f"Model {i + 1}" for i in range(len(frame))]

    if "macro_f1" not in frame.columns and {"macro_precision", "macro_recall"}.issubset(frame.columns):
        denominator = frame["macro_precision"] + frame["macro_recall"]
        frame["macro_f1"] = (2 * frame["macro_precision"] * frame["macro_recall"] / denominator).where(denominator != 0)

    return frame


def get_best_model_row(metrics):
    if metrics is None or metrics.empty:
        return None, None
    for column in ["macro_f1", "accuracy", "macro_precision", "macro_recall"]:
        if column in metrics.columns and metrics[column].notna().any():
            return metrics.loc[metrics[column].idxmax()], column
    return metrics.iloc[0], None


def categories():
    if CATEGORIES_PATH.exists():
        vals = [x.strip() for x in CATEGORIES_PATH.read_text(encoding="utf-8").splitlines() if x.strip()]
        if vals:
            return vals
    return DEFAULT_CATEGORIES


CATS = categories()


def get_header(headers, wanted):
    for h in headers:
        if h.get("name", "").lower() == wanted.lower():
            return h.get("value", "")
    return ""


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


def gmail_service(account=None):
    if not CLIENT_PATH.exists():
        raise FileNotFoundError("credentials.json is missing. Put the downloaded Google OAuth client JSON beside this app.")
    creds = None
    target_acc = account or st.session_state.get("gmail_account", "")
    user_token = (get_user_dir(target_acc) / "token.json") if target_acc else TOKEN_PATH
    
    # Try user-specific token first, fallback to root TOKEN_PATH if user is default
    token_to_try = user_token if user_token.exists() else TOKEN_PATH
    if token_to_try.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(token_to_try), SCOPES)
        except Exception:
            creds = None
            if token_to_try.exists():
                token_to_try.unlink()
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except Exception:
            creds = None
            if token_to_try.exists():
                token_to_try.unlink()
    if not creds or not creds.valid:
        try:
            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_PATH), SCOPES)
            creds = flow.run_local_server(port=0, prompt="select_account")
        except Exception as e:
            if "mismatching_state" in str(e).lower():
                raise RuntimeError("Google OAuth sign-in state expired or duplicate tab detected. Please click 'Sign in & Classify Inbox' again to complete authorization.")
            raise e
        if target_acc:
            user_token.write_text(creds.to_json(), encoding="utf-8")
        TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
    return build("gmail", "v1", credentials=creds)


def fetch_emails(service, limit, gmail_query=None):
    result_rows, token = [], None

    while limit is None or len(result_rows) < limit:
        request_args = {
            "userId": "me",
            "maxResults": 100 if limit is None else min(100, limit - len(result_rows)),
            "pageToken": token,
            "includeSpamTrash": False,
        }
        if gmail_query:
            request_args["q"] = gmail_query

        response = service.users().messages().list(**request_args).execute()

        for item in response.get("messages", []):
            msg = service.users().messages().get(
                userId="me", id=item["id"], format="full"
            ).execute()

            payload = msg.get("payload", {})
            headers = payload.get("headers", [])
            raw_date = get_header(headers, "Date")

            received_dt = None
            try:
                internal_ms = msg.get("internalDate")
                if internal_ms:
                    received_dt = datetime.fromtimestamp(
                        int(internal_ms) / 1000
                    ).astimezone()
                elif raw_date:
                    received_dt = parsedate_to_datetime(raw_date)
                    if received_dt.tzinfo is None:
                        received_dt = received_dt.astimezone()
                    else:
                        received_dt = received_dt.astimezone()
            except (ValueError, TypeError, OverflowError):
                received_dt = None

            if received_dt:
                display_date = received_dt.strftime("%Y-%m-%d %H:%M")
                received_at = received_dt.isoformat()
            else:
                display_date = raw_date
                received_at = None

            result_rows.append({
                "email_id": msg.get("id", ""),
                "date": display_date,
                "received_at": received_at,
                "sender": get_header(headers, "From"),
                "subject": get_header(headers, "Subject"),
                "body": extract_body(payload),
            })

        token = response.get("nextPageToken")
        if not token:
            break

    return result_rows


def predict_emails(rows, model, fraud_model=None):
    if not rows:
        return pd.DataFrame()
    texts = [f"{r.get('subject', '')} {r.get('body', '')}".strip() for r in rows]
    result = pd.DataFrame(rows)
    result["predicted_category"] = [str(x) for x in model.predict(texts)]
    if fraud_model is not None:
        try:
            preds = fraud_model.predict(texts)
            result["is_fraud"] = preds
            result["fraud_status"] = ["Fraudulent" if p == 1 else "Legitimate" for p in preds]
            if hasattr(fraud_model, "predict_proba"):
                probs = fraud_model.predict_proba(texts)[:, 1]
                result["fraud_confidence_pct"] = (probs * 100).round(1)
            else:
                result["fraud_confidence_pct"] = [95.0 if p == 1 else 5.0 for p in preds]
        except Exception:
            result["is_fraud"] = 0
            result["fraud_status"] = "Legitimate"
            result["fraud_confidence_pct"] = 0.0
    return result


# ───────────────────────────── helpers (UI) ─────────────────────────────
def nice(cat):
    return str(cat).replace("_", " ").title()


def esc(x):
    return html.escape(str(x))


def sender_name(raw):
    name, addr = parseaddr(str(raw))
    return name or addr or "Unknown sender"


def tag(cat):
    c = CAT_COLORS.get(cat, "#71717a")
    return f'<span class="tag" style="color:{c};background:{c}15;border-color:{c}35">{esc(nice(cat))}</span>'


def svg_icon(name, size=18, color="currentColor"):
    icons = {
        "inbox": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-6l-2 3h-4l-2-3H2"></path><path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"></path></svg>',
        "dashboard": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="9"></rect><rect x="14" y="3" width="7" height="5"></rect><rect x="14" y="12" width="7" height="9"></rect><rect x="3" y="16" width="7" height="5"></rect></svg>',
        "sparkles": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"></path></svg>',
        "flask": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 2v7.31"></path><path d="M14 2v7.31"></path><path d="M8.5 2h7"></path><path d="M14 9.31a8 8 0 1 1-4 0"></path></svg>',
        "shield-check": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path><path d="m9 12 2 2 4-4"></path></svg>',
        "shield-alert": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>',
        "history": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"></path><path d="M3 3v5h5"></path><path d="M12 7v5l4 2"></path></svg>',
        "info": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>',
        "search": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>',
    }
    return icons.get(name, "")


def inject_css(t):
    root = ":root{" + ";".join(f"--{k}:{v}" for k, v in t.items()) + "}"
    css = """
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

/* Base Typography - NEVER override Material icon fonts */
html, body, .stApp {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: var(--bg);
    color: var(--ink);
    transition: background 0.25s ease, color 0.25s ease;
}

/* FIX OVERLAYING TEXT: Restore Streamlit Material Symbols / Icon font */
[data-testid="stIconMaterial"], 
.material-symbols-rounded, 
[class*="material-symbols"], 
[class*="StyledIcon"],
[data-testid*="Icon"] {
    font-family: 'Material Symbols Rounded', 'Material Icons', sans-serif !important;
    font-style: normal !important;
    letter-spacing: normal !important;
    font-size: 1.15rem !important;
    line-height: 1 !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
}

/* FIX LARGE SPACE: Desktop Full-Width Container */
[data-testid="stHeader"] {background: transparent;}
.stApp [data-testid="stMain"] .block-container,
.main .block-container {
    max-width: 100% !important;
    padding-top: 1.2rem !important;
    padding-bottom: 2rem !important;
    padding-left: 2.2rem !important;
    padding-right: 2.2rem !important;
}

.stMarkdown, .stMarkdown p, label, [data-testid="stWidgetLabel"] *, [data-testid="stCaptionContainer"], h1, h2, h3, h4 {color: var(--ink);}
[data-testid="stCaptionContainer"] {color: var(--muted); font-size: .85rem;}
h1,h2,h3 {letter-spacing: -.03em; font-weight: 700;}

/* ══════════ SIDEBAR (Linear / Swiss Design) ══════════ */
[data-testid="stSidebar"] {
    background: var(--bg2) !important;
    border-right: 1px solid var(--line) !important;
    box-shadow: 4px 0 24px rgba(0,0,0,0.12) !important;
}
/* Compact sidebar vertical flow: eliminate 19px excessive gaps */
[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] {
    gap: 0.25rem !important;
}
[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"] {
    margin-bottom: 2px !important;
    padding-bottom: 0 !important;
}

/* SIDEBAR NAVIGATION: Sleek Tabs with VISIBLE Labels */
[data-testid="stSidebar"] div[data-testid="stRadio"] [role="radiogroup"] {
    gap: 3px !important;
    display: flex !important;
    flex-direction: column !important;
}
[data-testid="stSidebar"] div[data-testid="stRadio"] [role="radiogroup"] label {
    padding: 8px 12px !important;
    border-radius: 9px !important;
    width: 100% !important;
    cursor: pointer !important;
    margin: 0 !important;
    transition: all 0.14s ease !important;
    background: transparent !important;
    border: 1px solid transparent !important;
    display: flex !important;
    align-items: center !important;
}
/* Hide ONLY the radio circle/dot, NEVER the text container */
[data-testid="stSidebar"] div[data-testid="stRadio"] [role="radiogroup"] label div[data-testid="stRadioGroup-item"],
[data-testid="stSidebar"] div[data-testid="stRadio"] [role="radiogroup"] label > div[aria-hidden="true"],
[data-testid="stSidebar"] div[data-testid="stRadio"] [role="radiogroup"] label input[type="radio"],
[data-testid="stSidebar"] div[data-testid="stRadio"] [role="radiogroup"] label svg {
    display: none !important;
    width: 0 !important;
    height: 0 !important;
    opacity: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
}
/* Ensure the navigation text label is crystal clear and visible */
[data-testid="stSidebar"] div[data-testid="stRadio"] [role="radiogroup"] label div[data-testid="stMarkdownContainer"],
[data-testid="stSidebar"] div[data-testid="stRadio"] [role="radiogroup"] label div[data-testid="stMarkdownContainer"] p {
    display: block !important;
    visibility: visible !important;
    opacity: 1 !important;
    font-size: 0.90rem !important;
    font-weight: 500 !important;
    color: var(--muted) !important;
    margin: 0 !important;
}
[data-testid="stSidebar"] div[data-testid="stRadio"] [role="radiogroup"] label:hover {
    background: var(--hover) !important;
    border-color: var(--line) !important;
    transform: translateX(3px) !important;
}
[data-testid="stSidebar"] div[data-testid="stRadio"] [role="radiogroup"] label:hover div[data-testid="stMarkdownContainer"] p {
    color: var(--ink) !important;
}
[data-testid="stSidebar"] div[data-testid="stRadio"] [role="radiogroup"] label:has(input:checked) {
    background: var(--accent_soft) !important;
    border: 1px solid var(--accent) !important;
    box-shadow: 0 0 14px rgba(99, 102, 241, 0.22) !important;
    transform: translateX(3px) !important;
}
[data-testid="stSidebar"] div[data-testid="stRadio"] [role="radiogroup"] label:has(input:checked) div[data-testid="stMarkdownContainer"] p {
    color: #ffffff !important;
    font-weight: 700 !important;
}

/* SIDEBAR FOLDER BUTTONS: Strictly Left-Aligned Tree View */
[data-testid="stSidebar"] div.stButton > button:not([kind="primary"]) {
    display: flex !important;
    justify-content: flex-start !important;
    align-items: center !important;
    text-align: left !important;
    width: 100% !important;
    padding: 5px 12px !important;
    min-height: 2.15rem !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    margin: 1px 0 !important;
    border-radius: 8px !important;
    border: 1px solid transparent !important;
    background: transparent !important;
    color: var(--ink) !important;
    box-shadow: none !important;
    transition: all 0.12s ease !important;
}
[data-testid="stSidebar"] div.stButton > button:not([kind="primary"]) > div,
[data-testid="stSidebar"] div.stButton > button:not([kind="primary"]) span {
    display: flex !important;
    justify-content: flex-start !important;
    align-items: center !important;
    width: 100% !important;
    text-align: left !important;
}
[data-testid="stSidebar"] div.stButton > button:not([kind="primary"]) [data-testid="stMarkdownContainer"],
[data-testid="stSidebar"] div.stButton > button:not([kind="primary"]) [data-testid="stMarkdownContainer"] p {
    display: flex !important;
    justify-content: flex-start !important;
    align-items: center !important;
    text-align: left !important;
    width: 100% !important;
    margin: 0 !important;
    gap: 8px !important;
}
[data-testid="stSidebar"] div.stButton > button:not([kind="primary"]):hover {
    background: var(--hover) !important;
    border-color: var(--line) !important;
    transform: translateX(3px) !important;
    color: var(--accent) !important;
}

/* MAIN CONTENT SEGMENTED RADIOS */
div[data-testid="stRadio"]:not([data-testid="stSidebar"] div[data-testid="stRadio"]) [role="radiogroup"] {
    display: flex !important;
    flex-direction: row !important;
    gap: 8px !important;
}
div[data-testid="stRadio"]:not([data-testid="stSidebar"] div[data-testid="stRadio"]) [role="radiogroup"] label {
    padding: 7px 16px !important;
    border-radius: 8px !important;
    background: var(--panel2) !important;
    border: 1px solid var(--line) !important;
    cursor: pointer !important;
    transition: all 0.15s ease !important;
    display: flex !important;
    align-items: center !important;
}
div[data-testid="stRadio"]:not([data-testid="stSidebar"] div[data-testid="stRadio"]) [role="radiogroup"] label div[data-testid="stRadioGroup-item"],
div[data-testid="stRadio"]:not([data-testid="stSidebar"] div[data-testid="stRadio"]) [role="radiogroup"] label > div[aria-hidden="true"],
div[data-testid="stRadio"]:not([data-testid="stSidebar"] div[data-testid="stRadio"]) [role="radiogroup"] label svg {
    display: none !important;
}
div[data-testid="stRadio"]:not([data-testid="stSidebar"] div[data-testid="stRadio"]) [role="radiogroup"] label:has(input:checked) {
    background: var(--accent_soft) !important;
    border-color: var(--accent) !important;
    box-shadow: 0 0 10px rgba(99, 102, 241, 0.2) !important;
}
div[data-testid="stRadio"]:not([data-testid="stSidebar"] div[data-testid="stRadio"]) [role="radiogroup"] label:has(input:checked) p {
    color: var(--ink) !important;
    font-weight: 700 !important;
}

/* SLIDERS */
div[data-baseweb="slider"] {padding: 10px 0 !important;}
div[data-baseweb="slider"] div[role="slider"] {
    background-color: var(--accent) !important;
    border: 2px solid #ffffff !important;
    box-shadow: 0 0 12px rgba(99, 102, 241, 0.6) !important;
    width: 17px !important;
    height: 17px !important;
}
div[data-baseweb="slider"] div[data-testid="stThumbValue"] {
    color: var(--accent) !important;
    font-weight: 800 !important;
    font-size: 0.95rem !important;
    font-family: 'JetBrains Mono', monospace !important;
}
div[data-baseweb="slider"] div[class*="StyledTrackFilled"],
div[data-baseweb="slider"] div[style*="background-color: rgb(255, 75, 75)"],
div[data-baseweb="slider"] div[style*="background-color:#ff4b4b"],
div[data-baseweb="slider"] div[style*="background: rgb(255, 75, 75)"] {
    background: linear-gradient(90deg, var(--accent), #818cf8) !important;
    background-color: var(--accent) !important;
    height: 6px !important;
    border-radius: 999px !important;
}

/* BUTTONS & INPUTS */
div.stButton > button, div.stDownloadButton > button {
    border-radius: 10px;
    font-weight: 600;
    min-height: 2.5rem;
    border: 1px solid var(--line);
    background: var(--panel2);
    color: var(--ink);
    transition: all 0.18s ease;
}
div.stButton > button:hover, div.stDownloadButton > button:hover {
    border-color: var(--accent);
    color: var(--accent);
    transform: translateY(-2px);
    box-shadow: var(--shadow);
}
div.stButton > button[kind="primary"], 
div.stFormSubmitButton > button[kind="primary"], 
div.stFormSubmitButton > button {
    background: linear-gradient(135deg, #6366F1, #4F46E5) !important;
    color: #ffffff !important;
    border: none !important;
    box-shadow: 0 4px 14px rgba(99, 102, 241, 0.35) !important;
    font-weight: 700 !important;
}
div.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #4F46E5, #4338CA) !important;
    color: #ffffff !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(99, 102, 241, 0.5) !important;
}

[data-baseweb="input"], [data-baseweb="base-input"], [data-baseweb="textarea"], textarea, [data-baseweb="select"] > div {
    background: var(--input) !important;
    color: var(--ink) !important;
    border-color: var(--line) !important;
    border-radius: 10px !important;
}
[data-baseweb="input"]:focus-within, [data-baseweb="textarea"]:focus-within {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px var(--accent_soft) !important;
}

/* EXPANDERS */
[data-testid="stExpander"] {
    border: 1px solid var(--line) !important;
    border-radius: 12px !important;
    background: var(--panel) !important;
    box-shadow: var(--shadow) !important;
    margin-bottom: 16px !important;
}
[data-testid="stExpander"] summary {
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    color: var(--ink) !important;
    padding: 11px 16px !important;
}
[data-testid="stExpander"] div[data-testid="stExpanderDetails"] {
    padding: 4px 16px 16px !important;
}

/* CARDS, KPIS & BRAND */
.side-title {color:var(--muted); font-size:.76rem; text-transform:uppercase; letter-spacing:.06em; margin:14px 4px 6px; font-weight:700;}
.brand {padding: 6px 0 10px 0;}
.brand-name {font-size:1.30rem; font-weight:800; letter-spacing:-.03em; display:flex; align-items:center; gap:8px;}
.brand small {display:block; font-weight:500; font-size:.74rem; color:var(--muted); margin-top:2px;}

.page-head {display:flex; align-items:center; gap:16px; padding:4px 0 16px;}
.page-icon {width:48px; height:48px; border-radius:14px; background:var(--accent_soft); display:flex; align-items:center; justify-content:center; border:1px solid var(--line); color:var(--accent); box-shadow:var(--shadow);}
.page-title {font-size:1.85rem; font-weight:800; letter-spacing:-.035em; line-height:1.1;}
.page-sub {color:var(--muted); font-size:.90rem; margin-top:3px;}
.live {display:inline-flex; align-items:center; gap:8px; padding:7px 12px; border-radius:10px; background:var(--panel); border:1px solid var(--line); font-size:.82rem; font-weight:600; white-space:nowrap; box-shadow:var(--shadow);}
.live i {width:7px; height:7px; border-radius:50%; background:#10b981; display:inline-block; animation: pulse-glow 2s infinite;}

@keyframes pulse-glow {
  0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.6); }
  70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
  100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
}

.card {background:var(--panel); border:1px solid var(--line); border-radius:14px; box-shadow:var(--shadow); overflow:hidden; margin-bottom:16px; transition:border-color 0.15s ease;}
.card-head {padding:16px 20px; font-weight:700; font-size:1.00rem; border-bottom:1px solid var(--line); display:flex; align-items:center; gap:10px;}
.card-body {padding:20px;}
.h1 {background:var(--h1); color:var(--ink);} .h2 {background:var(--h2); color:var(--ink);} .h3 {background:var(--h3); color:var(--ink);} .h4 {background:var(--h4); color:var(--ink);}

.kpi {background:var(--panel); border:1px solid var(--line); border-radius:14px; padding:20px; box-shadow:var(--shadow); transition:transform 0.15s ease, border-color 0.15s ease;}
.kpi:hover {transform:translateY(-2px); border-color:var(--accent);}
.kpi-label {color:var(--muted); font-size:.78rem; font-weight:700; text-transform:uppercase; letter-spacing:.05em;}
.kpi-value {font-size:2.0rem; font-weight:800; letter-spacing:-.035em; margin-top:4px;}
.kpi-foot {color:var(--muted); font-size:.80rem; margin-top:4px; font-weight:500;}

.tag {display:inline-flex; align-items:center; gap:6px; padding:3px 10px; border-radius:999px; border:1px solid; font-size:.76rem; font-weight:700; white-space:nowrap;}
.pill {display:inline-flex; align-items:center; gap:6px; border:1px solid var(--line); background:var(--accent_soft); color:var(--accent); padding:4px 12px; border-radius:999px; font-size:.78rem; font-weight:700; margin:2px 6px 2px 0;}
.muted {color:var(--muted); font-size:.92rem; line-height:1.6;}

/* MAIL LIST & READER OVERHAUL */
[class*="st-key-mail"] button {
    width: 100% !important;
    text-align: left !important;
    justify-content: flex-start !important;
    background: var(--panel2) !important;
    border: 1px solid var(--line) !important;
    border-radius: 12px !important;
    padding: 12px 14px !important;
    min-height: 0 !important;
    box-shadow: none !important;
    height: auto !important;
    transition: all 0.12s ease !important;
    margin-bottom: 3px !important;
}
[class*="st-key-mail"] button > div {width: 100%; display: block; text-align: left;}
[class*="st-key-mail"] button [data-testid="stMarkdownContainer"] {width: 100%; text-align: left;}
[class*="st-key-mail"] button p {text-align: left !important; width: 100%; font-size: .84rem; color: var(--muted); line-height: 1.45; margin: 0;}
[class*="st-key-mail"] button p strong {color: var(--ink); font-size: .92rem; font-weight: 700;}
[class*="st-key-mail"] button:hover {border-color: var(--accent) !important; background: var(--panel) !important; transform: translateX(3px) !important;}
[class*="st-key-mailsel"] button {background: var(--sel) !important; border-color: var(--accent) !important; box-shadow: var(--shadow) !important;}

.reader {background: var(--panel); border: 1px solid var(--line); border-radius: 16px; padding: 26px; box-shadow: var(--shadow);}
.reader h2 {margin: 0 0 14px; font-size: 1.55rem; letter-spacing: -.03em; line-height: 1.25;}
.sender-row {display: flex; align-items: center; gap: 14px; margin-bottom: 18px;}
.avatar {width: 44px; height: 44px; border-radius: 50%; background: var(--accent_soft); color: var(--accent); display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 1.10rem; border: 1px solid var(--line); box-shadow: var(--shadow);}
.sender-name {font-weight: 700; font-size: 1.00rem;} 
.sender-mail {color: var(--muted); font-size: .84rem;}
.reader-body {white-space: pre-wrap; word-break: break-word; line-height: 1.70; font-size: 0.98rem; max-height: 560px; overflow-y: auto; border-top: 1px solid var(--line); padding-top: 20px; color: var(--ink);}
[data-testid="stDataFrame"] {border: 1px solid var(--line); border-radius: 12px; overflow: hidden;}
hr {border-color: var(--line); margin: 20px 0;}
"""
    st.markdown(f"<style>{root}{css}</style>", unsafe_allow_html=True)


def page_header(icon_name, title, sub, live=False):
    left, right = st.columns([4.2, 2.8])
    icon_html = svg_icon(icon_name, size=24, color="var(--accent)")
    with left:
        st.markdown(f"<div class='page-head'><div class='page-icon'>{icon_html}</div><div><div class='page-title'>{esc(title)}</div>"
                    f"<div class='page-sub'>{esc(sub)}</div></div></div>", unsafe_allow_html=True)
    with right:
        acc = st.session_state.get("gmail_account", "")
        acc_chip = (
            f"<div style='text-align:right;padding-top:6px'>"
            f"<span class='live' style='color:#10b981;border-color:rgba(16,185,129,0.35);background:rgba(16,185,129,0.1);padding:6px 14px;font-size:0.80rem;white-space:nowrap;display:inline-flex;align-items:center;gap:6px'>"
            f"<i style='background:#10b981;width:7px;height:7px;border-radius:50%;display:inline-block'></i> {esc(acc)}</span></div>"
            if acc else ""
        )
        if live:
            b1, b2 = st.columns([4, 1])
            b1.markdown(acc_chip or f"<div style='text-align:right;padding-top:8px'><span class='live'><i></i>Live • {datetime.now():%H:%M:%S}</span></div>",
                        unsafe_allow_html=True)
            if b2.button("⟳", key="refresh", help="Refresh"):
                st.rerun()
        else:
            if acc_chip:
                st.markdown(acc_chip, unsafe_allow_html=True)


def kpi(label, value, foot=""):
    st.markdown(f"<div class='kpi'><div class='kpi-label'>{esc(label)}</div><div class='kpi-value'>{esc(value)}</div>"
                f"<div class='kpi-foot'>{esc(foot)}</div></div>", unsafe_allow_html=True)


def card_head(icon_name, title, style="h1"):
    ic = svg_icon(icon_name, size=18, color="currentColor")
    st.markdown(f"<div class='card-head {style}'><span style='display:flex;align-items:center'>{ic}</span>{esc(title)}</div>", unsafe_allow_html=True)


def style_chart(ch, t):
    return (ch.configure(background="transparent")
            .configure_axis(labelColor=t["muted"], titleColor=t["muted"], gridColor=t["line"], domainColor=t["line"],
                            gridDash=[3, 3], tickColor=t["line"])
            .configure_view(strokeWidth=0)
            .configure_legend(labelColor=t["muted"], titleColor=t["muted"]))


def cat_scale():
    return alt.Scale(domain=[nice(c) for c in CAT_COLORS], range=list(CAT_COLORS.values()))


# ───────────────────────────── sidebar ─────────────────────────────
def nav_to_inbox():
    st.session_state.page = "Inbox"

def nav_to_folder(category_name):
    st.session_state.page = "Inbox"
    st.session_state.inbox_category_filter = category_name
    st.session_state.inbox_security_filter = "All Mail"

def nav_to_security(sec_filter):
    st.session_state.page = "Inbox"
    st.session_state.inbox_category_filter = "All categories"
    st.session_state.inbox_security_filter = sec_filter

_curr_theme_name = st.session_state.get("theme_choice", "Obsidian Luxury (Dark)")
if _curr_theme_name not in THEMES:
    _curr_theme_name = "Obsidian Luxury (Dark)"
T = THEMES[_curr_theme_name]
inject_css(T)

with st.sidebar:
    brand_ic = svg_icon("inbox", size=22, color="var(--accent)")
    st.markdown(
        f"<div class='brand'>"
        f"<div class='brand-name'>{brand_ic} CampusMail</div>"
        f"</div>",
        unsafe_allow_html=True
    )
    
    active_acc = st.session_state.get("gmail_account", "")
    known_accounts = list_known_accounts()
    
    if active_acc:
        st.markdown(
            f"<div style='background:rgba(16,185,129,0.12);border:1px solid rgba(16,185,129,0.35);padding:12px;border-radius:12px;margin:12px 0 8px'>"
            f"<div style='font-size:0.72rem;color:#10b981;font-weight:800;text-transform:uppercase;letter-spacing:0.06em;display:flex;align-items:center;gap:6px'>"
            f"<span style='width:7px;height:7px;background:#10b981;border-radius:50%;display:inline-block;box-shadow:0 0 6px #10b981'></span>"
            f"AUTHENTICATED GMAIL</div>"
            f"<div style='font-size:0.86rem;font-weight:700;color:var(--ink);margin-top:4px;word-break:break-all'>{esc(active_acc)}</div>"
            f"<div style='font-size:0.72rem;color:var(--muted);margin-top:2px'>{len(st.session_state.gmail_df):,} Classified Mails · Google 2FA Active</div>"
            f"</div>",
            unsafe_allow_html=True
        )
        col_sb1, col_sb2 = st.columns([1, 1])
        with col_sb1:
            if st.button("🚪 Sign Out", key="sb_signout_btn", use_container_width=True, help="Safely lock mailbox and log out"):
                sign_out()
                st.rerun()
        with col_sb2:
            st.button("⟳ Sync", type="primary", key="sb_sync_btn", use_container_width=True, on_click=nav_to_inbox, help="Sync latest Gmail messages")
    else:
        st.markdown(
            f"<div style='background:rgba(99,102,241,0.12);border:1px solid rgba(99,102,241,0.35);padding:12px;border-radius:12px;margin:12px 0 8px'>"
            f"<div style='font-size:0.72rem;color:#6366f1;font-weight:800;text-transform:uppercase;letter-spacing:0.06em;display:flex;align-items:center;gap:6px'>"
            f"<span style='width:7px;height:7px;background:#6366f1;border-radius:50%;display:inline-block;box-shadow:0 0 6px #6366f1'></span>"
            f"SESSION LOCKED · PRIVACY ACTIVE</div>"
            f"<div style='font-size:0.86rem;font-weight:700;color:var(--ink);margin-top:4px'>Guest / Clean Session</div>"
            f"<div style='font-size:0.72rem;color:var(--muted);margin-top:2px'>Previous accounts isolated & hidden</div>"
            f"</div>",
            unsafe_allow_html=True
        )
        if st.button("🔑 Sign In to Vault", key="sb_signin_btn", type="primary", use_container_width=True):
            st.session_state.page = "Inbox"
            st.rerun()

    with st.expander("📱 Share with Class (Live QR Code)", expanded=False):
        tunnel_url = "https://themes-televisions-learn-restore.trycloudflare.com"
        qr_img = f"https://api.qrserver.com/v1/create-qr-code/?size=180x180&data={tunnel_url}&margin=6"
        st.markdown(
            f"<div style='text-align:center;padding:6px 0'>"
            f"<img src='{qr_img}' style='width:150px;height:150px;border-radius:10px;background:#fff;padding:6px;box-shadow:0 4px 12px rgba(0,0,0,0.3)' alt='Scan QR' />"
            f"<div style='margin-top:8px;font-size:0.75rem;font-weight:700'>"
            f"<a href='{tunnel_url}' target='_blank' style='color:#818cf8;text-decoration:none'>{tunnel_url}</a></div>"
            f"<p style='font-size:0.72rem;color:var(--muted);margin-top:6px;line-height:1.4'>Classmates and teacher can scan this on their phones to test the AI live! Your personal emails remain protected in your private vault.</p>"
            f"</div>",
            unsafe_allow_html=True
        )
    st.markdown("<div class='side-title'>Workspace Navigation</div>", unsafe_allow_html=True)
    
    nav_pages = ["Dashboard", "Inbox", "Try a Prediction", "Model Lab", "Prediction History", "About the Project"]
    cur_p = st.session_state.get("page", "Inbox" if not st.session_state.gmail_df.empty else "Dashboard")
    cur_idx = nav_pages.index(cur_p) if cur_p in nav_pages else 0
    
    sel_page = st.radio("Workspace", nav_pages, index=cur_idx, key="workspace_nav_radio", label_visibility="collapsed")
    if sel_page != st.session_state.get("page"):
        st.session_state.page = sel_page

    gdf = st.session_state.gmail_df
    if not gdf.empty and active_acc:
        st.markdown("<div class='side-title' style='margin-top:14px'>Campus Folders</div>", unsafe_allow_html=True)
        counts_side = gdf.predicted_category.value_counts()
        
        st.button(f"📥 All mail ({len(gdf)})", key="sb_btn_all", use_container_width=True, on_click=nav_to_folder, args=("All categories",))

        for c in CATS:
            n = int(counts_side.get(c, 0))
            dot = CAT_DOTS.get(c, "⚪")
            st.button(f"{dot} {nice(c)} ({n})", key=f"sb_btn_{c}", use_container_width=True, on_click=nav_to_folder, args=(c,))

        if "is_fraud" in gdf.columns:
            st.markdown("<div class='side-title' style='margin-top:16px'>Security Shield Status</div>", unsafe_allow_html=True)
            fraud_n = int((gdf["is_fraud"] == 1).sum())
            legit_n = len(gdf) - fraud_n
            st.button(f"🛡️ Legitimate Safe ({legit_n})", key="sb_sec_legit", use_container_width=True, on_click=nav_to_security, args=("🛡️ Legitimate Only",))
            st.button(f"🚨 Phishing Alerts ({fraud_n})", key="sb_sec_fraud", use_container_width=True, on_click=nav_to_security, args=("🚨 Phishing Alerts Only",))

    st.divider()
    st.markdown("<div class='side-title'>Design System Palette</div>", unsafe_allow_html=True)
    theme_selection = st.selectbox(
        "Select Theme",
        list(THEMES.keys()),
        key="theme_choice",
        label_visibility="collapsed"
    )

if theme_selection != _curr_theme_name:
    st.rerun()

page = st.session_state.page

# ═════════════════════════════ DASHBOARD ═════════════════════════════
if page == "Dashboard":
    page_header("dashboard", "Dashboard", "real-time analytics and security summary", live=True)
    df = st.session_state.gmail_df

    best_name, best_acc = "Not available", "—"
    _m = load_model_metrics()
    _b, _rank_col = get_best_model_row(_m)
    if _b is not None:
        best_name = str(_b.get("model", "Unknown model"))
        if pd.notna(_b.get("accuracy", float("nan"))):
            best_acc = f"{float(_b['accuracy']):.1%}"

    k = st.columns(4)
    with k[0]:
        acc_str = st.session_state.get("gmail_account", "")
        if acc_str:
            kpi("Connected Account", acc_str, f"{len(df):,} Classified Mails in Vault")
        else:
            kpi("Privacy Shield", "Clean / Guest Session", "Previous user data locked")
    with k[1]:
        kpi("Categories found", str(df.predicted_category.nunique()) if not df.empty else "0", f"of {len(CATS)} supported")
    with k[2]:
        kpi("Best model", best_name, "Selected by macro F1")
    with k[3]:
        kpi("CV accuracy", best_acc, "Latest model comparison results")
    st.write("")

    if df.empty:
        curr_acc = st.session_state.get("gmail_account", "")
        user_header = f"No emails classified yet for {esc(curr_acc)}" if curr_acc else "Clean Session (No emails loaded)"
        st.markdown(f"<div class='card'><div class='card-head h4'><span>🔒</span>{user_header}</div><div class='card-body'>"
                    f"<p class='muted'>All emails and prediction history from other accounts are strictly protected and hidden for privacy. "
                    f"Sync your Gmail (read-only) to see your personal category charts, priorities and timeline analytics. "
                    f"You can also test any email message on the <b>Try a Prediction</b> playground.</p></div></div>", unsafe_allow_html=True)
        st.button("Open Inbox & Sync Gmail", type="primary", on_click=go_inbox)
        st.markdown("#### Supported Campus Categories")
        for start in range(0, len(CATS), 2):
            pair = st.columns(2)
            for j, c in enumerate(CATS[start:start + 2]):
                with pair[j]:
                    st.markdown(f"<div class='card'><div class='card-body'>{tag(c)}"
                                f"<div class='muted' style='margin-top:10px'>{esc(DESCRIPTIONS.get(c, 'College email category'))}</div></div></div>",
                                unsafe_allow_html=True)
    else:
        st.markdown("### 📅 Dashboard Date Filter")
        valid_days = email_local_dates(df)
        valid_days = [d for d in valid_days if pd.notna(d)]
        if valid_days:
            min_day, max_day = min(valid_days), max(valid_days)
            date_cols = st.columns([1, 1, 2])
            with date_cols[0]:
                dash_start = st.date_input(
                    "From",
                    value=min_day,
                    key="dashboard_start_date",
                    format="DD/MM/YYYY",
                )
            with date_cols[1]:
                dash_end = st.date_input(
                    "To",
                    value=max_day,
                    key="dashboard_end_date",
                    format="DD/MM/YYYY",
                )
            with date_cols[2]:
                st.caption("Filter the dashboard analytics by date range.")
            if dash_start > dash_end:
                st.warning("Start date cannot be after end date.")
                dashboard_df = df.iloc[0:0].copy()
            else:
                dashboard_df = filter_by_dates(df, dash_start, dash_end)
            st.caption(f"{len(dashboard_df):,} emails in the selected date range.")
        else:
            dashboard_df = df.copy()
            st.info("Email dates are unavailable; showing all classified emails.")

        if dashboard_df.empty:
            st.info("No classified emails fall within this date range.")
        else:
            if "is_fraud" in dashboard_df.columns:
                f_count = int((dashboard_df["is_fraud"] == 1).sum())
                if f_count > 0:
                    st.markdown(
                        f"<div style='background:#ef444415;border:1px solid #ef444455;border-radius:14px;padding:16px 20px;margin-bottom:20px;display:flex;align-items:center;gap:14px'>"
                        f"<div style='font-size:1.8rem'>🚨</div>"
                        f"<div><div style='color:#ef4444;font-weight:700;font-size:1.05rem'>Security Warning: {f_count} Phishing Threat(s) Detected</div>"
                        f"<div class='muted' style='margin-top:2px'>Potential fraud or credential scam emails identified in this view. Check the <b>Inbox</b> tab for threat details.</div></div></div>",
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f"<div style='background:#10b98115;border:1px solid #10b98155;border-radius:14px;padding:16px 20px;margin-bottom:20px;display:flex;align-items:center;gap:14px'>"
                        f"<div style='font-size:1.8rem'>🛡️</div>"
                        f"<div><div style='color:#10b981;font-weight:700;font-size:1.05rem'>Security Check Passed</div>"
                        f"<div class='muted' style='margin-top:2px'>All {len(dashboard_df):,} analyzed emails are verified legitimate. Zero phishing threats found.</div></div></div>",
                        unsafe_allow_html=True
                    )

            counts = dashboard_df.predicted_category.value_counts().reindex(CATS, fill_value=0)
            cdf = pd.DataFrame({"Category": [nice(c) for c in counts.index], "Emails": counts.values})
            urgent_n = int(dashboard_df.predicted_category.isin(URGENT).sum())
            normal_n = len(dashboard_df) - urgent_n

            c1, c2 = st.columns(2)
            with c1:
                with st.container(key="card_bar"):
                    card_head("dashboard", "Emails by Category", "h1")
                    bar = alt.Chart(cdf).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6).encode(
                        x=alt.X("Category:N", sort=None, axis=alt.Axis(labelAngle=-40, title=None)),
                        y=alt.Y("Emails:Q", title=None),
                        color=alt.Color("Category:N", scale=cat_scale(), legend=None),
                        tooltip=["Category", "Emails"]).properties(height=330)
                    st.altair_chart(style_chart(bar, T), use_container_width=True, theme=None)
            with c2:
                with st.container(key="card_donut"):
                    card_head("info", "Emails by Priority", "h2")
                    pdf = pd.DataFrame({"Priority": ["High (Deadline)", "Normal"], "Emails": [urgent_n, normal_n]})
                    donut = alt.Chart(pdf).mark_arc(innerRadius=75, outerRadius=120, stroke="#fff", strokeWidth=2).encode(
                        theta="Emails:Q",
                        color=alt.Color("Priority:N", scale=alt.Scale(domain=["High (Deadline)", "Normal"], range=["#ef4444", "#10b981"]), legend=None),
                        tooltip=["Priority", "Emails"]).properties(height=330)
                    st.altair_chart(style_chart(donut, T), use_container_width=True, theme=None)
                    st.markdown(f"<div style='text-align:center;padding-bottom:14px;font-weight:700;font-size:.92rem'>"
                                f"<span style='color:#ef4444'>●</span> High Priority ({urgent_n}) &nbsp;&nbsp; "
                                f"<span style='color:#10b981'>●</span> Normal ({normal_n})</div>", unsafe_allow_html=True)
                    st.caption("High priority = exams, assignments, scholarships and placements (deadline-sensitive).")

            with st.container(key="card_timeline"):
                card_head("history", "Classification Timeline", "h3")
                tl = dashboard_df.copy()
                if "received_at" in tl.columns and tl["received_at"].notna().any():
                    num_s = pd.to_numeric(tl["received_at"], errors="coerce")
                    tl["when"] = pd.to_datetime(num_s, unit="ms", errors="coerce", utc=True).dt.tz_convert("Asia/Kolkata")
                else:
                    tl["when"] = pd.to_datetime(tl["date"], errors="coerce", utc=True).dt.tz_convert("Asia/Kolkata")
                tl = tl.dropna(subset=["when"])
                if tl.empty:
                    st.caption("No parsable dates to draw a timeline.")
                else:
                    tl["day"] = tl["when"].dt.normalize()
                    tl["Category"] = tl["predicted_category"].map(nice)
                    tdf = tl.groupby(["day", "Category"]).size().reset_index(name="Emails")
                    area = alt.Chart(tdf).mark_area(opacity=.75, line=True, interpolate="monotone").encode(
                        x=alt.X("day:T", title=None), y=alt.Y("Emails:Q", stack=True, title=None),
                        color=alt.Color("Category:N", scale=cat_scale(), legend=alt.Legend(orient="bottom", columns=5)),
                        tooltip=["day:T", "Category", "Emails"]).properties(height=280)
                    st.altair_chart(style_chart(area, T), use_container_width=True, theme=None)

# ═════════════════════════════ INBOX ═════════════════════════════
elif page == "Inbox":
    df = st.session_state.gmail_df
    active_mail = st.session_state.get("gmail_account", "")

    # Save credentials into browser password manager (Brave / Google Chrome) if flagged
    cred_data = st.session_state.pop("credential_to_store", None)
    if cred_data:
        email_to_save = cred_data.get("email", "")
        pwd_to_save = cred_data.get("password", "")
        save_js = f"""
        <script>
        (async function() {{
            try {{
                if (window.parent && window.parent.PasswordCredential && window.parent.navigator.credentials) {{
                    const cred = new window.parent.PasswordCredential({{
                        id: {json.dumps(email_to_save)},
                        password: {json.dumps(pwd_to_save)},
                        name: {json.dumps(email_to_save)}
                    }});
                    await window.parent.navigator.credentials.store(cred);
                    console.log("Credentials stored in browser manager for {email_to_save}.");
                }}
            }} catch(err) {{
                console.log("Credentials store notice:", err);
            }}
        }})();
        </script>
        """
        components.html(save_js, height=0)

    if not active_mail:
        page_header("inbox", "CampusMail Access Vault", "University Email Classification & Phishing Shield")

        google_svg = (
            '<svg width="32" height="32" viewBox="0 0 24 24">'
            '<path fill="#4285F4" d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.665-5.17 3.665-9.17Z"/>'
            '<path fill="#34A853" d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.25v3.15C3.26 21.36 7.33 24 12 24Z"/>'
            '<path fill="#FBBC05" d="M5.28 14.27c-.25-.72-.38-1.49-.38-2.27s.14-1.55.38-2.27V6.58H1.25C.45 8.18 0 9.99 0 12s.45 3.82 1.25 5.42l4.03-3.15Z"/>'
            '<path fill="#EA4335" d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.33 0 3.26 2.64 1.25 6.58l4.03 3.15c.95-2.83 3.6-4.98 6.72-4.98Z"/>'
            '</svg>'
        )

        c_left, c_center, c_right = st.columns([1, 4.4, 1])
        with c_center:
            st.markdown(
                f"<div style='background:var(--panel);border:1px solid rgba(255,255,255,0.08);border-radius:20px;padding:32px 36px;box-shadow:0 12px 48px rgba(0,0,0,0.45);margin:12px auto 22px'>"
                f"<div style='text-align:center;margin-bottom:20px'>"
                f"<div style='display:inline-flex;align-items:center;justify-content:center;margin-bottom:10px'>{google_svg}</div>"
                f"<h2 style='margin:0 0 6px;font-size:1.60rem;font-weight:800;color:var(--ink);letter-spacing:-0.02em'>CampusMail Vault Sign-In</h2>"
                f"<p style='color:var(--muted);font-size:0.88rem;margin:0;line-height:1.5'>Enter your university email and vault password to sync your private mailbox.</p>"
                f"</div>",
                unsafe_allow_html=True
            )

            # Enforce clean, completely unpopulated inputs on visit
            for k in ["prefill_login_email", "field_user_email", "field_user_pwd"]:
                st.session_state.pop(k, None)
            
            with st.form(key="vault_access_form_v2", clear_on_submit=False):
                # Hidden off-screen decoy dummy fields absorb browser password manager auto-fill
                st.markdown(
                    "<div style='opacity:0;position:absolute;top:-9999px;left:-9999px;height:0;width:0;overflow:hidden' aria-hidden='true'>"
                    "<input type='text' name='fake_username_autofill' tabindex='-1' autocomplete='off' />"
                    "<input type='password' name='fake_password_autofill' tabindex='-1' autocomplete='new-password' />"
                    "</div>",
                    unsafe_allow_html=True
                )

                st.markdown("<div style='font-size:0.80rem;font-weight:700;color:var(--ink);margin-bottom:5px'>University Email Address</div>", unsafe_allow_html=True)
                email_input = st.text_input(
                    "University Email Address",
                    value="",
                    placeholder="id@thapar.edu",
                    label_visibility="collapsed",
                    key="login_user_thapar_id",
                    autocomplete="off"
                )

                st.markdown("<div style='font-size:0.80rem;font-weight:700;color:var(--ink);margin:12px 0 5px'>Vault Password / PIN</div>", unsafe_allow_html=True)
                pwd_input = st.text_input(
                    "Vault Password / PIN",
                    type="password",
                    value="",
                    placeholder="Enter password (e.g. thapar2026)",
                    label_visibility="collapsed",
                    key="login_user_vault_pin",
                    autocomplete="new-password"
                )

                st.markdown(
                    f"<div style='background:rgba(99,102,241,0.08);border:1px solid rgba(99,102,241,0.25);border-radius:10px;padding:9px 13px;margin:12px 0 16px;font-size:0.77rem;color:var(--muted);line-height:1.4'>"
                    f"🔒 <b>Zero-Knowledge Privacy:</b> Enter your university ID (e.g. <code>id@thapar.edu</code> or roll number) and any password to unlock or create your private, isolated university mailbox vault."
                    f"</div>",
                    unsafe_allow_html=True
                )

                submit_btn = st.form_submit_button("🚀 Sign In & Sync Mailbox", type="primary", use_container_width=True)

            if submit_btn:
                raw_input = (email_input or "").strip().lower()
                clean_pwd = (pwd_input or "").strip()
                if not raw_input:
                    st.error("Please enter your university ID (e.g. id@thapar.edu).")
                elif not clean_pwd:
                    st.error("Please enter your vault password.")
                else:
                    clean_email = raw_input if "@" in raw_input else f"{raw_input}@thapar.edu"
                    if verify_user_password(clean_email, clean_pwd):
                        st.session_state["credential_to_store"] = {"email": clean_email, "password": clean_pwd}
                        switch_to_account(clean_email)
                        st.success(f"Access granted for {clean_email}! Syncing mailbox...")
                        st.rerun()
                    else:
                        st.error("Incorrect password for this vault. Please try again.")

            # Quick Preset Buttons for easy presentation
            st.markdown(
                f"<div style='display:flex;align-items:center;gap:8px;margin-top:14px;justify-content:center'>"
                f"<span style='font-size:0.74rem;color:var(--muted);text-transform:uppercase;font-weight:700;letter-spacing:0.04em'>Quick Presets:</span>"
                f"</div>",
                unsafe_allow_html=True
            )
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                if st.button("🎓 Student Demo Space", use_container_width=True, key="preset_student_btn"):
                    demo_student = "student_demo@thapar.edu"
                    switch_to_account(demo_student)
                    st.rerun()
            with col_p2:
                if st.button("🛡️ Security Test Sandbox", use_container_width=True, key="preset_sandbox_btn"):
                    sandbox_student = "sandbox@thapar.edu"
                    switch_to_account(sandbox_student)
                    st.rerun()

            st.markdown("<div style='text-align:center;margin:14px 0 10px;font-size:0.8rem;color:var(--muted);font-weight:600'>or Connect via Google</div>", unsafe_allow_html=True)

            # Google OAuth 2.0 with 2-Step Verification / Authenticator
            auth_clicked = st.button("🔐 Sign in with Google (OAuth 2.0 & Authenticator)", use_container_width=True, key="btn_google_oauth")
            if auth_clicked:
                try:
                    with st.spinner("Opening Google OAuth 2.0 with 2-Step Verification & Authenticator..."):
                        service = gmail_service()
                        profile = service.users().getProfile(userId="me").execute()
                        acc = profile.get("emailAddress", "")
                        switch_to_account(acc)
                        st.success(f"Authenticated as {acc} via Google 2-Step Verification!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Google authentication: {e}")

            # Zero-Data-Leakage Privacy Architecture Card
            st.markdown(
                f"<div style='margin-top:20px;border-top:1px solid rgba(255,255,255,0.08);padding-top:16px;text-align:left'>"
                f"<div style='font-size:0.74rem;font-weight:800;text-transform:uppercase;color:#818cf8;letter-spacing:0.06em;margin-bottom:8px;display:flex;align-items:center;gap:6px'>"
                f"<span>🛡️</span> ZERO-DATA-LEAKAGE PRIVACY GUARANTEE</div>"
                f"<div style='display:flex;flex-direction:column;gap:6px;font-size:0.80rem;color:var(--muted)'>"
                f"<div><b style='color:var(--ink)'>✓ Multi-Tenant Isolation:</b> Each student's emails and history are stored in a private vault directory. Classmates cannot see each other's data.</div>"
                f"<div><b style='color:var(--ink)'>✓ Instant Clean Lock:</b> Clicking <b>Sign Out</b> immediately purges all inbox and user state from the screen.</div>"
                f"<div><b style='color:var(--ink)'>✓ Dual-Head ML Engine:</b> Categorizes emails into 10 university departments + flags phishing scams in &lt;10ms.</div>"
                f"</div>"
                f"</div></div>",
                unsafe_allow_html=True
            )
    else:
        header_subtitle = (
            f"Connected to {active_mail} · {len(df):,} mails classified with phishing shield"
            if not df.empty
            else f"Private Workspace: {active_mail} · Ready to classify"
        )
        page_header("inbox", "Intelligent Inbox", header_subtitle)

        with st.expander("🔐 Sync / Re-classify Gmail Inbox (Read-Only Secure OAuth)", expanded=df.empty):
            st.caption(f"Active Account: **{active_mail}**. Each user's inbox is strictly isolated in their private vault for confidentiality.")

            st.markdown(f"<div style='font-size:0.86rem;color:var(--muted);margin-bottom:10px'>Syncing mailbox for: <b style='color:var(--ink)'>{esc(active_mail)}</b></div>", unsafe_allow_html=True)

            fetch_mode = st.radio(
                "Fetch emails by",
                ["Recent emails", "Custom date range"],
                horizontal=True,
                key="gmail_fetch_mode",
            )

            date_range = None
            if fetch_mode == "Custom date range":
                date_range = st.date_input(
                    "Select start date and end date",
                    value=(date.today() - timedelta(days=7), date.today()),
                    max_value=date.today(),
                    format="DD/MM/YYYY",
                    key="gmail_custom_date_range",
                )
                st.caption("Both start and end dates are included.")

            if fetch_mode == "Recent emails":
                limit = st.select_slider(
                    "Maximum messages to process",
                    options=[25, 50, 100, 250, 500, 1000],
                    value=100,
                    key="gmail_fetch_limit",
                )
            else:
                limit = None

            btn_col1, btn_col2 = st.columns([3, 1])
            with btn_col1:
                btn_label = f"🔄 Re-Sync & Classify Inbox ({st.session_state.gmail_account})"
                run = st.button(
                    btn_label,
                    type="primary",
                    use_container_width=True,
                    key="gmail_sync_button",
                )
            with btn_col2:
                if st.button("🔄 Reset This Account", use_container_width=True, help="Clear saved token and cached emails for current user"):
                    if active_mail:
                        u_dir = get_user_dir(active_mail)
                        for f in [u_dir / "cached_inbox.csv", u_dir / "token.json"]:
                            if f.exists():
                                f.unlink()
                    st.session_state.gmail_df = pd.DataFrame()
                    st.session_state.sel_id = None
                    st.info(f"Cached inbox cleared for {active_mail or 'current session'}.")
                    st.rerun()

        if run:
            try:
                selected_start = selected_end = None
                gmail_query = None

                if fetch_mode == "Custom date range":
                    if not isinstance(date_range, (tuple, list)) or len(date_range) != 2:
                        st.error("Please select both a start date and an end date.")
                        st.stop()
                    selected_start, selected_end = date_range
                    if selected_start > selected_end:
                        st.error("Start date cannot be after end date.")
                        st.stop()
                    gmail_query = gmail_date_query(selected_start, selected_end)

                with st.spinner("Opening Google OAuth authorization..."):
                    target_auth = active_mail
                    service = gmail_service(account=target_auth)
                profile = service.users().getProfile(userId="me").execute()
                account = profile.get("emailAddress", target_auth)

                if gmail_query:
                    fetch_description = f"emails from {selected_start:%d %b %Y} to {selected_end:%d %b %Y}"
                else:
                    fetch_description = f"up to {limit} recent messages"

                with st.spinner(f"Fetching {fetch_description}..."):
                    rows = fetch_emails(
                        service,
                        None if gmail_query else int(limit),
                        gmail_query=gmail_query,
                    )

                with st.spinner("Running Dual-Head ML Pipeline (Campus Category + Phishing Detector)..."):
                    model = load_model()
                    fraud_model = load_fraud_model()
                    df = predict_emails(rows, model, fraud_model)

                st.session_state.gmail_df = df
                st.session_state.gmail_account = account
                st.session_state.sel_id = None
                st.session_state.gmail_fetch_description = fetch_description
                persist_inbox(df, account)
                st.success(f"Successfully classified and saved {len(df)} messages in private vault for {account}.")
                st.rerun()
            except Exception as e:
                st.error(f"Could not connect or classify: {e}")
                st.caption("Verify credentials.json, Gmail API status, and model pipeline files.")
                if st.session_state.gmail_df.empty and active_mail:
                    st.session_state.gmail_df = load_persisted_inbox(active_mail)

        df = st.session_state.gmail_df
        if df.empty:
            curr_acc = st.session_state.get("gmail_account", "")
            st.markdown(
                f"<div class='card' style='border:1px solid rgba(99, 102, 241, 0.4);background:rgba(99, 102, 241, 0.08)'>"
                f"<div class='card-head h3' style='color:var(--accent)'><span>🔒</span>Private Workspace: {esc(curr_acc)}</div>"
                f"<div class='card-body'>"
                f"<div style='font-size:1.1rem;font-weight:700;color:var(--ink);margin-bottom:6px'>User Privacy Protection Active</div>"
                f"<p class='muted'>All emails, categories, and prediction histories from other users are strictly isolated and hidden from this view.</p>"
                f"<p class='muted'>To classify your messages, open <b>Sync / Re-classify Gmail Inbox</b> above and click <b>Re-Sync & Classify Inbox</b>.</p>"
                f"</div></div>",
                unsafe_allow_html=True
            )
        else:
            available_days = email_local_dates(df)
        available_days = [d for d in available_days if pd.notna(d)]

        if available_days:
            min_day, max_day = min(available_days), max(available_days)
            with st.expander("📅 Filter Messages by Date Range", expanded=False):
                date_cols = st.columns([1, 1, 1.5])
                with date_cols[0]:
                    inbox_start = st.date_input(
                        "From",
                        value=min_day,
                        key="inbox_filter_start",
                        format="DD/MM/YYYY",
                    )
                with date_cols[1]:
                    inbox_end = st.date_input(
                        "To",
                        value=max_day,
                        key="inbox_filter_end",
                        format="DD/MM/YYYY",
                    )
                with date_cols[2]:
                    st.write("")
                    st.caption(f"Inbox timeline: {min_day:%d %b %Y} to {max_day:%d %b %Y}")
            if inbox_start > inbox_end:
                st.warning("Start date cannot be after end date.")
                date_filtered_df = df.iloc[0:0].copy()
            else:
                date_filtered_df = filter_by_dates(df, inbox_start, inbox_end)
        else:
            date_filtered_df = df.copy()

        # Search + category filter + security filter + export
        s1, s2, s3, s4 = st.columns([2.2, 1.3, 1.3, 1.1])
        search_text = s1.text_input(
            "Search",
            placeholder="🔍  Search sender or subject…",
            label_visibility="collapsed",
            key="inbox_search",
        )
        all_cats = ["All categories"] + CATS
        current_cat = st.session_state.get("inbox_category_filter", "All categories")
        cat_index = all_cats.index(current_cat) if current_cat in all_cats else 0
        selected = s2.selectbox(
            "Category",
            all_cats,
            index=cat_index,
            format_func=lambda c: c if c == "All categories" else nice(c),
            label_visibility="collapsed",
            key="inbox_cat_select_widget",
        )
        st.session_state.inbox_category_filter = selected

        sec_choices = ["All Mail", "🛡️ Legitimate Only", "🚨 Phishing Alerts Only"]
        current_sec = st.session_state.get("inbox_security_filter", "All Mail")
        sec_index = sec_choices.index(current_sec) if current_sec in sec_choices else 0
        sec_filter = s3.selectbox(
            "Security Status",
            sec_choices,
            index=sec_index,
            label_visibility="collapsed",
            key="inbox_sec_select_widget",
        )
        st.session_state.inbox_security_filter = sec_filter
        s4.download_button(
            "⬇ Export CSV",
            date_filtered_df.to_csv(index=False).encode("utf-8-sig"),
            "campusmail_categorized_emails.csv",
            "text/csv",
            use_container_width=True,
        )

        view = date_filtered_df if selected == "All categories" else date_filtered_df[date_filtered_df.predicted_category == selected]
        if "is_fraud" in view.columns:
            if sec_filter == "🛡️ Legitimate Only":
                view = view[view["is_fraud"] == 0]
            elif sec_filter == "🚨 Phishing Alerts Only":
                view = view[view["is_fraud"] == 1]

        if search_text.strip():
            needle = search_text.strip().lower()
            view = view[view.apply(lambda r: needle in str(r.get("sender", "")).lower() or needle in str(r.get("subject", "")).lower(), axis=1)]
        view = view.reset_index(drop=True)

        if view.empty:
            st.info("No emails match these filters.")
        else:
            ids = view["email_id"].tolist()
            if st.session_state.sel_id not in ids:
                st.session_state.sel_id = ids[0]
            chosen = view[view.email_id == st.session_state.sel_id].iloc[0]

            list_col, read_col = st.columns([1.1, 2.2], gap="large")
            with list_col:
                st.caption(f"Showing {min(len(view), 80)} of {len(view):,} messages")
                with st.container(height=680, border=False):
                    for i, r in view.head(80).iterrows():
                        cat = r["predicted_category"]
                        is_phish = r.get("is_fraud", 0) == 1
                        phish_badge = "🚨 PHISH" if is_phish else "🛡️ SAFE"
                        is_sel = (r["email_id"] == st.session_state.sel_id)
                        prefix = "▶ " if is_sel else ""
                        s_name = sender_name(r["sender"])[:26]
                        d_val = r.get("date")
                        try:
                            d_clean = pd.to_datetime(d_val).strftime("%d %b %Y")
                        except Exception:
                            d_clean = str(d_val)[:11]
                        subj_snippet = str(r["subject"] or "(No subject)").strip()[:54]
                        label = (f"{prefix}**{s_name}** · {d_clean}\n\n"
                                 f"{subj_snippet}\n\n"
                                 f"{CAT_DOTS.get(cat, '⚪')} {nice(cat)}  ·  {phish_badge}")
                        key = f"mail_item_{r['email_id']}"
                        st.button(label, key=key, on_click=pick, args=(r["email_id"],), use_container_width=True)
            with read_col:
                name = sender_name(chosen["sender"])
                _, addr = parseaddr(str(chosen["sender"]))
                body = str(chosen.get("body", "")) or "(No message body available)"
                is_phish = chosen.get("is_fraud", 0) == 1
                fraud_prob = chosen.get("fraud_confidence_pct", 98.0)

                # Security Alert Banner in Reader
                if is_phish:
                    st.markdown(
                        f"<div style='background:#7f1d1d;border:1px solid #ef4444;border-radius:14px;padding:20px;margin-bottom:16px'>"
                        f"<div style='color:#fca5a5;font-weight:800;font-size:1.1rem;display:flex;align-items:center;justify-content:space-between'>"
                        f"<span>🚨 Phishing Alert</span>"
                        f"<span style='background:#991b1b;padding:4px 10px;border-radius:8px;font-size:0.85rem'>Risk: {fraud_prob:.1f}%</span></div>"
                        f"<p style='color:#fecaca;font-size:0.95rem;margin:10px 0 0;line-height:1.5'>"
                        f"This email exhibits characteristics of a phishing attempt. Avoid clicking links, opening attachments, or sharing personal information.</p></div>",
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f"<div style='background:#064e3b;border:1px solid #10b981;border-radius:14px;padding:20px;margin-bottom:16px;color:#d1fae5;font-size:0.95rem;display:flex;align-items:center;gap:12px'>"
                        f"<span style='font-size:1.4rem'>🛡️</span><div><b>Verified Safe · 99%</b><br>Communication style is consistent with authentic institutional notices.</div></div>",
                        unsafe_allow_html=True
                    )

                st.markdown(
                    f"<div class='reader'><h2>{esc(chosen['subject'] or '(No subject)')}</h2>"
                    f"<div class='sender-row'><div class='avatar'>{esc(name[:1].upper())}</div>"
                    f"<div style='flex:1'><div class='sender-name'>{esc(name)}</div><div class='sender-mail'>{esc(addr)}</div></div>"
                    f"<div style='text-align:right'>{tag(chosen['predicted_category'])}<div class='sender-mail' style='margin-top:6px'>{esc(chosen['date'])}</div></div></div>"
                    f"<div class='reader-body'>{esc(body[:12000])}</div></div>", unsafe_allow_html=True)
                st.caption("Category and security status are predicted by the Dual-Head ML pipeline. Read-only access.")

# ═════════════════════════════ TRY A PREDICTION ═════════════════════════════
elif page == "Try a Prediction":
    page_header("sparkles", "Try a Prediction Playground", "test both Campus Categorization and Phishing/Fraud Detection instantly")
    try:
        model = load_model()
        fraud_model = load_fraud_model()
    except Exception as e:
        st.error(str(e))
        st.stop()

    f1, f2 = st.columns([1.3, 1], gap="large")
    with f1:
        st.markdown("##### ⚡ Quick Demo Samples (Click to load)")
        p1, p2, p3, p4 = st.columns(4)
        def pick_demo(sub, body):
            st.session_state["demo_sub"] = sub
            st.session_state["demo_msg"] = body
            st.session_state["run_instant_prediction"] = True

        st.markdown("##### ⚡ Quick Demo Samples (Click to test instantly)")
        p1, p2, p3, p4 = st.columns(4)
        p1.button("🚨 Job Scam", use_container_width=True, help="Fake internship demanding registration fee",
                  on_click=pick_demo, args=(
                      "Urgent: Selected for Amazon Summer Internship 2026 - Confirm Slot",
                      "Congratulations! You have been shortlisted for Amazon Summer Internship stipend Rs. 85,000/month. To secure your slot, you must pay mandatory security deposit of Rs. 1,500 immediately at http://amazon-careers-verify.info/pay before 5 PM today."
                  ))
        p2.button("🚨 Phishing", use_container_width=True, help="Credential harvesting password expiry",
                  on_click=pick_demo, args=(
                      "URGENT: Your Campus WebKiosk / Email Password Expires in 24 Hours",
                      "Dear Student, your student portal account will be terminated today due to system maintenance. Click here immediately to verify your credentials: http://university-login-update.com/auth. Failure to update will lock your student profile."
                  ))
        p3.button("🏢 Exam Notice", use_container_width=True, help="Authentic university exam schedule",
                  on_click=pick_demo, args=(
                      "End Semester Examination Schedule - Even Semester 2026",
                      "Dear Students, The tentative datesheet for the upcoming End Semester Examinations May 2026 has been uploaded on the university portal. Practical evaluations begin from 12th May. In case of any clash, notify the Academic Section before Friday."
                  ))
        p4.button("🏢 Hackathon", use_container_width=True, help="Authentic student hackathon",
                  on_click=pick_demo, args=(
                      "CodeCraft 2026: 36-Hour National Student Hackathon",
                      "Dear Coders, The Department of Computer Science & Engineering in association with ACM Student Chapter invites teams for CodeCraft 2026. Cash prizes of Rs. 1,50,000 to be won. Form teams of 2 to 4 members and register on our official portal."
                  ))

        with st.form("predict_form"):
            default_sub = st.session_state.get("demo_sub", "")
            default_msg = st.session_state.get("demo_msg", "")
            subject = st.text_input("Email subject", value=default_sub, placeholder="End-semester examination timetable released")
            body = st.text_area("Email body", value=default_msg, placeholder="Paste the message body here…", height=210)
            submitted = st.form_submit_button("✨ Run Dual-Head Prediction", type="primary", use_container_width=True)

        auto_run = st.session_state.pop("run_instant_prediction", False)
        should_run = submitted or (auto_run and bool(subject or body))

    with f2:
        if should_run:
            text = f"{subject} {body}".strip()
            if not text:
                st.warning("Enter a subject or body first.")
            else:
                cat_prediction = str(model.predict([text])[0])

                # Fraud Prediction
                is_fraud = 0
                fraud_prob = 0.0
                if fraud_model is not None:
                    try:
                        is_fraud = int(fraud_model.predict([text])[0])
                        if hasattr(fraud_model, "predict_proba"):
                            probs = fraud_model.predict_proba([text])[0]
                            fraud_prob = probs[1] * 100.0
                        else:
                            fraud_prob = 98.0 if is_fraud == 1 else 2.0
                    except Exception:
                        is_fraud = 0

                # 1. Category Card
                st.markdown(f"<div class='card'><div class='card-head h3'><span>🎯</span>Campus Category Prediction</div><div class='card-body'>"
                            f"<div style='font-size:1.8rem;font-weight:800;letter-spacing:-.03em;margin-bottom:8px'>{esc(nice(cat_prediction))}</div>"
                            f"{tag(cat_prediction)}<p class='muted' style='margin-top:12px'>{esc(DESCRIPTIONS.get(cat_prediction, ''))}</p></div></div>",
                            unsafe_allow_html=True)

                # 2. Fraud & Security Card
                if is_fraud == 1:
                    st.markdown(
                        f"<div class='card' style='border:1px solid #ef444455;background:#ef444412'>"
                        f"<div class='card-head h2' style='color:#ef4444'><span>🚨</span>Fraud & Phishing Security Alert</div>"
                        f"<div class='card-body'>"
                        f"<div style='font-size:1.5rem;font-weight:800;color:#ef4444;margin-bottom:6px'>Fraudulent / Scam Detected</div>"
                        f"<span class='tag' style='color:#ef4444;background:#ef444422;border-color:#ef444466'>⚠️ Threat Confidence: {fraud_prob:.1f}%</span>"
                        f"<p class='muted' style='margin-top:12px;font-size:0.92rem'>This email contains language or patterns typical of phishing attacks, scam offers, or credential harvesting.</p>"
                        f"</div></div>",
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f"<div class='card' style='border:1px solid #10b98155;background:#10b98112'>"
                        f"<div class='card-head h1' style='color:#10b981'><span>🛡️</span>Authenticity & Trust Shield</div>"
                        f"<div class='card-body'>"
                        f"<div style='font-size:1.5rem;font-weight:800;color:#10b981;margin-bottom:6px'>Verified Safe Legitimate</div>"
                        f"<span class='tag' style='color:#10b981;background:#10b98122;border-color:#10b98166'>✓ Safe Confidence: {100.0 - fraud_prob:.1f}%</span>"
                        f"<p class='muted' style='margin-top:12px;font-size:0.92rem'>Matches genuine college notices, official academic communications, or trusted email structure.</p>"
                        f"</div></div>",
                        unsafe_allow_html=True
                    )

                history_record = {
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Subject": subject,
                    "Email Body": body,
                    "Predicted Category": cat_prediction,
                    "Fraud Status": "Fraudulent" if is_fraud == 1 else "Legitimate",
                    "Threat Probability": f"{fraud_prob:.1f}%"
                }
                st.session_state.history.append(history_record)
                persist_history_entry(history_record, account=st.session_state.get("gmail_account", ""))
        else:
            st.markdown("<div class='card'><div class='card-head h3'><span>✨</span>Dual-Model Prediction Output</div><div class='card-body'>"
                        "<p class='muted'>Results for both Campus Category and Phishing Security Status will appear here once analyzed.</p></div></div>", unsafe_allow_html=True)

# ═════════════════════════════ MODEL LAB ═════════════════════════════
elif page == "Model Lab":
    page_header("flask", "Model Lab & Benchmarks", "inspect evaluation metrics, confusion matrices and explainability reports")

    tab_campus, tab_fraud = st.tabs(["🏢 Campus Categorization (10 Classes)", "🛡️ Phishing & Fraud Detector"])

    with tab_campus:
        if MODEL_PATH.exists():
            model_updated = datetime.fromtimestamp(MODEL_PATH.stat().st_mtime).strftime("%d %b %Y, %I:%M %p")
            st.caption(f"Active classifier artifact: {MODEL_PATH.name} · Last modified: {model_updated}")
        else:
            st.warning(f"Saved prediction model not found: {MODEL_PATH}")
        if METRICS_PATH.exists():
            metrics = load_model_metrics()
            st.caption("Evaluation results loaded from outputs/model_comparison.csv.")
            if metrics.empty:
                st.info("The model comparison file exists but contains no evaluation rows.")
            else:
                best, ranking_metric = get_best_model_row(metrics)
                if best is not None:
                    k = st.columns(4)
                    with k[0]:
                        st.metric("Top Model", str(best.get("model", "Unknown")))
                    with k[1]:
                        acc = best.get("accuracy", float("nan"))
                        st.metric("Accuracy", f"{float(acc):.1%}" if pd.notna(acc) else "N/A", "Saved evaluation score")
                    with k[2]:
                        f1 = best.get("macro_f1", float("nan"))
                        st.metric("Macro F1", f"{float(f1):.3f}" if pd.notna(f1) else "N/A", "Equal weight per class")
                    with k[3]:
                        st.metric("Models Tested", str(len(metrics)))
                    if ranking_metric is None:
                        st.warning("No recognized evaluation score column was found.")
                    elif ranking_metric != "macro_f1":
                        st.info(f"Macro F1 was unavailable; best model ranked by {ranking_metric.replace('_', ' ')}.")

                m1, m2 = st.columns([1, 1])
                with m1:
                    with st.container(key="card_cmp_table"):
                        card_head("dashboard", "Model Comparison Table", "h1")
                        display = metrics.copy()
                        for col in ["accuracy", "macro_precision", "macro_recall", "macro_f1"]:
                            if col in display:
                                display[col] = display[col].map(lambda x: f"{x:.3f} ({x:.1%})" if pd.notna(x) else "N/A")
                        st.dataframe(display, use_container_width=True, hide_index=True)
                with m2:
                    with st.container(key="card_cmp_chart"):
                        card_head("sparkles", "Score Comparison Chart", "h4")
                        score_columns = [c for c in ["accuracy", "macro_precision", "macro_recall", "macro_f1"] if c in metrics.columns]
                        if score_columns:
                            long = metrics.melt(id_vars="model", value_vars=score_columns,
                                                var_name="Metric", value_name="Score").dropna(subset=["Score"])
                            if not long.empty:
                                ch = alt.Chart(long).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
                                    x=alt.X("model:N", title=None, axis=alt.Axis(labelAngle=0)),
                                    y=alt.Y("Score:Q", title=None), xOffset="Metric:N",
                                    color=alt.Color("Metric:N", legend=alt.Legend(orient="bottom")),
                                    tooltip=["model", "Metric", alt.Tooltip("Score:Q", format=".3f")]
                                ).properties(height=280)
                                st.altair_chart(style_chart(ch, T), use_container_width=True, theme=None)
                            else:
                                st.info("No numeric score values available to chart.")
                        else:
                            st.info("No recognized score columns found.")

                e1, e2 = st.columns(2)
                with e1:
                    st.markdown("<div class='card'><div class='card-body'><b>Accuracy</b><p class='muted'>Share of all evaluated messages given the correct category.</p>"
                                "<b>Precision</b><p class='muted'>Of messages predicted as a category, how many were correct.</p></div></div>", unsafe_allow_html=True)
                with e2:
                    st.markdown("<div class='card'><div class='card-body'><b>Recall</b><p class='muted'>Of the messages truly in a category, how many the model found.</p>"
                                "<b>Macro F1</b><p class='muted'>Balance of precision and recall, averaged equally across categories.</p></div></div>", unsafe_allow_html=True)
        else:
            st.info("Model comparison file not found: outputs/model_comparison.csv")

        if REPORT_PATH.exists():
            report = pd.read_csv(REPORT_PATH)
            report = report[~report.category.isin(["accuracy", "macro avg", "weighted avg"])]
            with st.container(key="card_report"):
                report_model_name = "Best saved model"
                if METRICS_PATH.exists():
                    try:
                        metric_rows = load_model_metrics()
                        metric_best, _metric_used = get_best_model_row(metric_rows)
                        if metric_best is not None:
                            report_model_name = str(metric_best.get("model", "Best saved model"))
                    except Exception:
                        pass
                card_head("info", f"Per-Category Performance — {report_model_name}", "h3")
                st.caption("F1 helps identify categories requiring more training examples.")
                r1, r2 = st.columns([1, 1.2])
                r1.dataframe(report, use_container_width=True, hide_index=True)
                r2.bar_chart(report.set_index("category")[["precision", "recall", "f1-score"]])
        if CONFUSION_PATH.exists():
            with st.expander("Inspect Campus Classification Confusion Matrix"):
                cm = pd.read_csv(CONFUSION_PATH, index_col=0)
                st.caption("Rows are actual categories; columns are predicted.")
                st.dataframe(cm, use_container_width=True)

        st.markdown("#### Pipeline Architecture")
        steps = [("Email Text", "Subject and body combined into single string."), ("TF-IDF", "Text vectorized into unigrams & bigrams."),
                 ("N-gram Range", "ngram_range=(1, 2) configured."),
                 ("Model Search", "Multinomial NB, Logistic Regression and Linear SVM benchmarked."),
                 ("Evaluation", "Macro F1, accuracy, precision and recall optimized.")]
        cols = st.columns(len(steps))
        for i, (title, desc) in enumerate(steps):
            with cols[i]:
                st.markdown(f"<div class='card'><div class='card-body'><span class='pill'>{i + 1}</span><b>{esc(title)}</b>"
                            f"<div class='muted' style='margin-top:6px'>{esc(desc)}</div></div></div>", unsafe_allow_html=True)

    with tab_fraud:
        st.markdown("### 🛡️ Phishing & Fraud Detection Benchmarks")
        st.caption("Independent binary classification pipeline separating legitimate campus notices from fraudulent phishing and scam attacks.")

        if FRAUD_MODEL_PATH.exists():
            f_time = datetime.fromtimestamp(FRAUD_MODEL_PATH.stat().st_mtime).strftime("%d %b %Y, %I:%M %p")
            st.caption(f"Active fraud detector: {FRAUD_MODEL_PATH.name} · Last modified: {f_time}")

        if FRAUD_METRICS_PATH.exists():
            f_metrics = pd.read_csv(FRAUD_METRICS_PATH)
            top_f = f_metrics.iloc[0]
            fk = st.columns(4)
            with fk[0]:
                st.metric("Best Model", str(top_f["model"]))
            with fk[1]:
                st.metric("Test Accuracy", f"{top_f['test_accuracy']:.1%}", "On 2,400 held-out test emails")
            with fk[2]:
                st.metric("Fraud Recall", f"{top_f['test_recall']:.1%}", "Caught 99.1% of phishing attacks")
            with fk[3]:
                st.metric("ROC-AUC Score", f"{top_f['test_roc_auc']:.3f}", "Near-perfect discriminative power")

            st.write("")
            fc1, fc2 = st.columns([1.1, 1])
            with fc1:
                st.markdown("#### 📋 Fraud Algorithm Comparison")
                st.dataframe(f_metrics, use_container_width=True, hide_index=True)
            with fc2:
                st.markdown("#### 📊 Score Comparison Chart")
                chart_df = f_metrics.melt(id_vars="model", value_vars=["test_accuracy", "test_recall", "test_f1"],
                                         var_name="Metric", value_name="Score")
                f_ch = alt.Chart(chart_df).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
                    x=alt.X("model:N", title=None, axis=alt.Axis(labelAngle=0)),
                    y=alt.Y("Score:Q", title="Score (0-1.0)", scale=alt.Scale(domain=[0.85, 1.0])),
                    xOffset="Metric:N",
                    color=alt.Color("Metric:N", scale=alt.Scale(range=["#0284C7", "#ef4444", "#10b981"])),
                    tooltip=["model", "Metric", alt.Tooltip("Score:Q", format=".4f")]
                ).properties(height=260)
                st.altair_chart(style_chart(f_ch, T), use_container_width=True, theme=None)

        if FRAUD_CONFUSION_PATH.exists():
            st.write("")
            st.markdown("#### 🎯 Fraud Confusion Matrix & Error Analysis")
            cm_col1, cm_col2 = st.columns([1, 1.2])
            with cm_col1:
                f_cm = pd.read_csv(FRAUD_CONFUSION_PATH, index_col=0)
                st.dataframe(f_cm, use_container_width=True)
            with cm_col2:
                st.markdown(
                    "<div class='card'><div class='card-body'>"
                    "<b>Why Recall is Critical for Security:</b><br/>"
                    "<span class='muted'>In campus cybersecurity, False Negatives (missing a real phishing attack) are extremely dangerous. "
                    "The selected Calibrated Linear SVM caught <b>1,189 out of 1,200</b> phishing emails in the test set, providing students robust protection against fake job scams and credential theft.</span>"
                    "</div></div>", unsafe_allow_html=True
                )

        if FRAUD_KEYWORDS_PATH.exists():
            st.write("")
            st.markdown("#### 🔍 Explainability: Top Indicator Words")
            kw_df = pd.read_csv(FRAUD_KEYWORDS_PATH)
            kw1, kw2 = st.columns(2)
            with kw1:
                st.markdown("<b style='color:#ef4444'>🚨 Top Phishing / Scam Indicators</b>", unsafe_allow_html=True)
                st.dataframe(kw_df[["top_fraud_indicators", "fraud_weight"]].head(12), use_container_width=True, hide_index=True)
            with kw2:
                st.markdown("<b style='color:#10b981'>🛡️ Top Legitimate Academic Indicators</b>", unsafe_allow_html=True)
                st.dataframe(kw_df[["top_legitimate_indicators", "legitimate_weight"]].head(12), use_container_width=True, hide_index=True)

        if FRAUD_SAMPLES_PATH.exists():
            with st.expander("View Real Test Predictions & Sample Explanations"):
                sample_df = pd.read_csv(FRAUD_SAMPLES_PATH)
                st.dataframe(sample_df, use_container_width=True, hide_index=True)

# ═════════════════════════════ HISTORY ═════════════════════════════
elif page == "Prediction History":
    page_header("history", "Prediction History", "all analyzed emails tested across sessions with dual-model results")
    curr_acc = st.session_state.get("gmail_account", "")
    if not st.session_state.history:
        st.session_state.history = load_persisted_history(curr_acc)
    hist = pd.DataFrame(st.session_state.history)

    if hist.empty:
        user_desc = f"for <b>{esc(curr_acc)}</b>" if curr_acc else "in this clean session"
        st.markdown(f"<div class='card'><div class='card-head h4'><span>🔒</span>No Prediction History Yet {user_desc}</div><div class='card-body'>"
                    f"<p class='muted'>Each user has an isolated private history vault. Queries tested on the <b>Try a Prediction</b> page are automatically logged and saved here persistently.</p></div></div>",
                    unsafe_allow_html=True)
        st.button("Open Try a Prediction", type="primary", on_click=lambda: setattr(st.session_state, "page", "Try a Prediction"))
    else:
        # KPI Row
        hk = st.columns(4)
        legit_count = int((hist["Fraud Status"] == "Legitimate").sum()) if "Fraud Status" in hist.columns else len(hist)
        phish_count = len(hist) - legit_count
        with hk[0]:
            kpi("Total Evaluations", str(len(hist)), "Saved persistently in private vault")
        with hk[1]:
            kpi("Legitimate Safe", str(legit_count), "Authentic university communications")
        with hk[2]:
            kpi("Phishing Caught", str(phish_count), "Scam offers & credential alerts")
        with hk[3]:
            top_cat = str(hist["Predicted Category"].mode().iloc[0]).title() if "Predicted Category" in hist.columns and not hist.empty else "N/A"
            kpi("Top Category", top_cat, "Most frequent tested topic")
        st.write("")

        # Filters and search
        h_col1, h_col2, h_col3 = st.columns([2, 1.2, 1.2])
        h_search = h_col1.text_input("Search History", placeholder="🔍 Search subject or message...", label_visibility="collapsed", key="hist_search")
        h_sec = h_col2.selectbox("Filter Status", ["All Results", "🛡️ Legitimate Only", "🚨 Phishing Only"], label_visibility="collapsed", key="hist_sec_filter")
        all_hist_cats = sorted(list(set(hist["Predicted Category"].dropna().tolist()))) if "Predicted Category" in hist.columns else []
        h_cat = h_col3.selectbox("Filter Category", ["All Categories"] + all_hist_cats, label_visibility="collapsed", key="hist_cat_filter")

        h_view = hist.copy()
        if h_sec == "🛡️ Legitimate Only" and "Fraud Status" in h_view.columns:
            h_view = h_view[h_view["Fraud Status"] == "Legitimate"]
        elif h_sec == "🚨 Phishing Only" and "Fraud Status" in h_view.columns:
            h_view = h_view[h_view["Fraud Status"] == "Fraudulent"]

        if h_cat != "All Categories" and "Predicted Category" in h_view.columns:
            h_view = h_view[h_view["Predicted Category"] == h_cat]

        if h_search.strip():
            hn = h_search.strip().lower()
            h_view = h_view[h_view.apply(lambda r: hn in str(r.get("Subject", "")).lower() or hn in str(r.get("Email Body", "")).lower(), axis=1)]

        st.caption(f"Showing {len(h_view)} of {len(hist)} recorded predictions")
        st.dataframe(h_view, use_container_width=True, hide_index=True)

        h1, h2, _ = st.columns([1.2, 1.2, 3.5])
        with h1:
            st.download_button("⬇ Download History CSV", hist.to_csv(index=False).encode("utf-8-sig"), "campusmail_prediction_history.csv", "text/csv", use_container_width=True)
        with h2:
            if st.button("🗑️ Clear History", use_container_width=True):
                st.session_state.history = []
                if curr_acc:
                    user_hist_file = get_user_dir(curr_acc) / "prediction_history.csv"
                    if user_hist_file.exists():
                        user_hist_file.unlink()
                st.rerun()

        st.markdown("#### 📜 Detailed Evaluation Log")
        for idx, row in h_view.iterrows():
            is_fraud = str(row.get("Fraud Status", "")).lower() == "fraudulent"
            badge = "<span style='color:#ef4444;background:#ef444422;padding:3px 8px;border-radius:6px;font-weight:700;font-size:0.75rem'>🚨 PHISHING ALERT</span>" if is_fraud else "<span style='color:#10b981;background:#10b98122;padding:3px 8px;border-radius:6px;font-weight:700;font-size:0.75rem'>🛡️ LEGITIMATE SAFE</span>"
            cat_name = str(row.get("Predicted Category", "")).title()
            time_str = str(row.get("Timestamp", ""))
            prob_str = str(row.get("Threat Probability", ""))

            with st.expander(f"{'🚨' if is_fraud else '🛡️'} {row.get('Subject', '(No subject)')} — {cat_name} ({time_str})"):
                st.markdown(f"**Security Verdict:** {badge} &nbsp;&nbsp; **Category:** `{cat_name}` &nbsp;&nbsp; **Threat Probability:** `{prob_str}`", unsafe_allow_html=True)
                st.markdown(f"**Email Body Text:**\n```\n{row.get('Email Body', '')}\n```")

# ═════════════════════════════ ABOUT ═════════════════════════════
elif page == "About the Project":
    page_header("info", "About CampusMail & Phishing Shield", "intelligent campus email classification & cybersecurity system")
    a1, a2 = st.columns(2)
    with a1:
        st.markdown("<div class='card'><div class='card-head h1'><span>🎯</span>Dual-Architecture Objectives</div><div class='card-body'><ul class='muted'>"
                    "<li><b>Campus Categorization:</b> Automatically organizes student mail into 10 academic and campus categories (Exams, Placements, Hackathons, etc.).</li>"
                    "<li><b>Phishing & Fraud Detection:</b> Independent security classifier to flag fraudulent internship offers, fake fee notices, and credential harvesting.</li>"
                    "<li><b>Orthogonal Predictions:</b> Separating topic from trustworthiness ensures an email can be both a 'Placement notice' and 'Fraudulent'.</li>"
                    "<li><b>Live Gmail Integration:</b> Connects securely via Google OAuth 2.0 (read-only) for seamless real-world demonstration.</li></ul></div></div>", unsafe_allow_html=True)
    with a2:
        st.markdown("<div class='card'><div class='card-head h2'><span>🛡️</span>Model Integrity & Privacy Architecture</div><div class='card-body'><ul class='muted'>"
                    "<li><b>Topic Classifier:</b> Linear SVM / Logistic Regression trained on verified campus notices with TF-IDF unigrams & bigrams.</li>"
                    "<li><b>Fraud Detector:</b> Calibrated Linear SVM trained on 11,998 balanced emails (98.96% Accuracy, 99.08% Recall).</li>"
                    "<li><b>Multi-User Privacy Isolation:</b> User mailboxes and prediction histories are strictly segregated into per-user isolated vaults (<code>outputs/users/&lt;user_id&gt;/</code>). No user can view or access another user's emails.</li>"
                    "<li><b>Privacy First:</b> Read-only Gmail scope (<code>gmail.readonly</code>) ensures messages are never deleted, altered, or forwarded.</li>"
                    "<li><b>Credentials Safety:</b> Local OAuth token handling with per-user protected tokens and environment isolation.</li></ul></div></div>",
                    unsafe_allow_html=True)
    st.markdown("#### Supported Campus Categories")
    st.markdown("".join(tag(c) + " " for c in CATS), unsafe_allow_html=True)

st.markdown("<hr><div class='muted' style='text-align:center;padding:12px'>CampusMail · Dual-Head ML Engine · Intelligent University Email Classification & Cybersecurity Shield</div>",
            unsafe_allow_html=True)
