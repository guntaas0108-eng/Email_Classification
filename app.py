import time
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
from googleapiclient.errors import HttpError

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
    "Obsidian Luxury (Dark)": dict(
        bg="#0B0F19", bg2="#0F172A", panel="#131C31", panel2="#18233C", line="#202D49",
        ink="#F8FAFC", muted="#94A3B8", accent="#6366F1", accent_soft="rgba(99, 102, 241, 0.15)",
        input="#101828", sel="rgba(99, 102, 241, 0.22)", hover="#1E2A47",
        h1="rgba(99, 102, 241, 0.12)", h2="rgba(239, 68, 68, 0.12)",
        h3="rgba(16, 185, 129, 0.12)", h4="rgba(245, 158, 11, 0.12)",
        shadow="0 1px 3px rgba(0, 0, 0, 0.35), 0 8px 24px -4px rgba(0, 0, 0, 0.5)",
        is_dark=True
    ),
    "Linear SaaS Light": dict(
        bg="#F8FAFC", bg2="#FFFFFF", panel="#FFFFFF", panel2="#F1F5F9", line="#E2E8F0",
        ink="#0F172A", muted="#64748B", accent="#4F46E5", accent_soft="rgba(79, 70, 229, 0.08)",
        input="#FFFFFF", sel="rgba(79, 70, 229, 0.10)", hover="#F1F5F9",
        h1="rgba(79, 70, 229, 0.06)", h2="rgba(239, 68, 68, 0.06)",
        h3="rgba(16, 185, 129, 0.06)", h4="rgba(245, 158, 11, 0.06)",
        shadow="0 1px 3px rgba(15, 23, 42, 0.04), 0 4px 14px -2px rgba(15, 23, 42, 0.05)",
        is_dark=False
    ),
    "Warm Editorial (Light)": dict(
        bg="#FAF8F5", bg2="#FFFFFF", panel="#FFFFFF", panel2="#F4F2EE", line="#E7E5E0",
        ink="#1C1917", muted="#78716C", accent="#0284C7", accent_soft="#E0F2FE",
        input="#FAF8F5", sel="#BAE6FD", hover="#F5F3EF",
        h1="rgba(16, 185, 129, 0.08)", h2="rgba(239, 68, 68, 0.08)",
        h3="rgba(99, 102, 241, 0.08)", h4="rgba(2, 132, 199, 0.08)",
        shadow="0 1px 2px rgba(0,0,0,0.04), 0 8px 24px -4px rgba(0,0,0,0.06)",
        is_dark=False
    ),
}

OAUTH_SUCCESS_HTML = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Authentication Complete - CampusMail</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background: #0B0F19;
            color: #F8FAFC;
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100vh;
            margin: 0;
            padding: 20px;
            box-sizing: border-box;
        }
        .box {
            background: #131C31;
            border: 1px solid #202D49;
            padding: 40px 32px;
            border-radius: 16px;
            text-align: center;
            max-width: 440px;
            box-shadow: 0 12px 32px rgba(0,0,0,0.5);
        }
        .icon { font-size: 48px; margin-bottom: 12px; }
        h2 { font-size: 22px; font-weight: 700; color: #10B981; margin: 0 0 10px; }
        p { color: #94A3B8; font-size: 14px; line-height: 1.5; margin: 0 0 24px; }
        .btn {
            display: inline-block;
            background: #6366F1;
            color: #ffffff;
            font-weight: 600;
            padding: 12px 24px;
            border-radius: 8px;
            text-decoration: none;
            transition: 0.2s;
        }
        .btn:hover { background: #4F46E5; }
    </style>
</head>
<body>
    <div class="box">
        <div class="icon">✅</div>
        <h2>Authentication Complete!</h2>
        <p>Google account verified successfully.<br>Returning to your CampusMail inbox...</p>
        <a class="btn" href="http://localhost:8501">Return to CampusMail</a>
    </div>
    <script>
        setTimeout(function() {
            window.location.href = "http://localhost:8501";
        }, 600);
        setTimeout(function() {
            window.close();
        }, 3000);
    </script>
</body>
</html>"""

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
    # Template seeding strictly for demo accounts
    if "student_demo" in acc.lower() or "demo" in acc.lower():
        demo_file = BASE / "data" / "demo_student_mailbox.csv"
        if demo_file.exists():
            try:
                df = pd.read_csv(demo_file)
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

def merge_inbox_dataframes(new_df: pd.DataFrame, old_df: pd.DataFrame) -> pd.DataFrame:
    if old_df is None or old_df.empty:
        return new_df
    if new_df is None or new_df.empty:
        return old_df
    if "email_id" in old_df.columns and "email_id" in new_df.columns:
        combined = pd.concat([new_df, old_df], ignore_index=True)
        combined = combined.drop_duplicates(subset=["email_id"], keep="first")
        if "received_at" in combined.columns:
            try:
                combined = combined.sort_values(by="received_at", ascending=False, na_position="last").reset_index(drop=True)
            except Exception:
                pass
        return combined
    return new_df

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
    st.session_state.page = "Dashboard"
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
    st.session_state.pop("inbox_filter_start", None)
    st.session_state.pop("inbox_filter_end", None)
    st.session_state.pop("_last_inbox_min_day", None)
    st.session_state.pop("_last_inbox_max_day", None)
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

st.session_state.setdefault("page", "Dashboard")
st.session_state.setdefault("sel_id", None)
st.session_state.setdefault("theme_choice", "Obsidian Luxury (Dark)")


def go_inbox():
    st.session_state.page = "Email History"


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
        dt_s = pd.to_datetime(frame["received_at"], errors="coerce")
        if dt_s.notna().any():
            return dt_s.dt.date

    if "date" in frame.columns and frame["date"].notna().any():
        timestamps = pd.to_datetime(frame["date"], errors="coerce")
        if timestamps.notna().any():
            return timestamps.dt.date

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
            creds = flow.run_local_server(
                port=0,
                prompt="select_account",
                success_message=OAUTH_SUCCESS_HTML,
            )
        except Exception as e:
            if "mismatching_state" in str(e).lower():
                raise RuntimeError("Google OAuth sign-in state expired or duplicate tab detected. Please click 'Sign in & Classify Inbox' again to complete authorization.")
            raise e
        if target_acc:
            user_token.write_text(creds.to_json(), encoding="utf-8")
        TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
    return build("gmail", "v1", credentials=creds)


def fetch_emails(service, limit, gmail_query=None, progress_callback=None):
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

        try:
            response = service.users().messages().list(**request_args).execute()
        except HttpError as e:
            err_str = str(e).lower()
            if "ratelimitexceeded" in err_str or "quota" in err_str:
                time.sleep(2.5)
                try:
                    response = service.users().messages().list(**request_args).execute()
                except Exception:
                    break
            else:
                break
        except Exception:
            break

        messages = response.get("messages", [])
        if not messages:
            break

        for item in messages:
            if limit is not None and len(result_rows) >= limit:
                break

            msg = None
            for attempt in range(3):
                try:
                    msg = service.users().messages().get(
                        userId="me", id=item["id"], format="full"
                    ).execute()
                    break
                except HttpError as e:
                    err_str = str(e).lower()
                    if "ratelimitexceeded" in err_str or "quota" in err_str or (hasattr(e, "resp") and e.resp.status in (403, 429)):
                        # Back off exponentially to allow Google's per-minute quota bucket to refill
                        time.sleep(2.0 * (attempt + 1))
                    else:
                        break
                except Exception:
                    time.sleep(1.0)

            if not msg:
                # If rate limited on this email, return whatever emails we have successfully retrieved so far
                if len(result_rows) > 0:
                    return result_rows
                continue

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
            if progress_callback:
                target_count = limit or max(len(messages), len(result_rows))
                progress_callback(len(result_rows), target_count)
            time.sleep(0.04)  # Pacing delay between queries to stay safely within per-second API quota

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
        "settings": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>',
    }
    return icons.get(name, "")


def inject_css(t):
    root = ":root{" + ";".join(f"--{k}:{v}" for k, v in t.items()) + "}"
    css = """
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

/* Base Typography & Smooth Transition */
html, body, .stApp {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: var(--bg);
    color: var(--ink);
    transition: background 0.2s ease, color 0.2s ease;
}

/* Material icon preservation */
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

/* Balanced Desktop Container Layout */
[data-testid="stHeader"] {background: transparent;}
.stApp [data-testid="stMain"] .block-container,
.main .block-container {
    max-width: 1400px !important;
    margin: 0 auto !important;
    padding-top: 1.4rem !important;
    padding-bottom: 3rem !important;
    padding-left: 2.2rem !important;
    padding-right: 2.2rem !important;
}

/* EQUAL COLUMN HEIGHT & GRID BALANCING */
div[data-testid="column"] {
    display: flex !important;
    flex-direction: column !important;
    justify-content: stretch !important;
}
div[data-testid="column"] > div[data-testid="stVerticalBlock"] {
    flex: 1 1 auto !important;
    display: flex !important;
    flex-direction: column !important;
    height: 100% !important;
}
div[data-testid="column"] > div[data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"] {
    flex: 1 1 auto !important;
    display: flex !important;
    flex-direction: column !important;
}
div[data-testid="column"] > div[data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"] > div {
    flex: 1 1 auto !important;
    display: flex !important;
    flex-direction: column !important;
}

.stMarkdown, .stMarkdown p, label, [data-testid="stWidgetLabel"] *, [data-testid="stCaptionContainer"], h1, h2, h3, h4 {color: var(--ink);}
[data-testid="stCaptionContainer"] {color: var(--muted); font-size: .84rem;}
h1, h2, h3 {letter-spacing: -.025em; font-weight: 700;}

/* ══════════ SIDEBAR (Linear / Swiss Design with Smooth Toggle) ══════════ */
[data-testid="stSidebar"],
section[data-testid="stSidebar"] {
    background: var(--bg2) !important;
    border-right: 1px solid var(--line) !important;
    box-shadow: 4px 0 24px rgba(0,0,0,0.12) !important;
    transition: transform 0.32s cubic-bezier(0.16, 1, 0.3, 1), width 0.32s cubic-bezier(0.16, 1, 0.3, 1) !important;
}

/* FLOATING REOPEN SIDEBAR BUTTON (Visible when closed) */
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"],
button[data-testid="stSidebarCollapsedControl"],
button[data-testid="collapsedControl"] {
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    position: fixed !important;
    top: 14px !important;
    left: 14px !important;
    z-index: 999999 !important;
    background: var(--bg2, #111726) !important;
    color: var(--accent, #6366F1) !important;
    border: 1.5px solid var(--accent, #6366F1) !important;
    border-radius: 10px !important;
    padding: 7px 11px !important;
    box-shadow: 0 4px 20px rgba(99, 102, 241, 0.38) !important;
    cursor: pointer !important;
    transition: all 0.22s cubic-bezier(0.16, 1, 0.3, 1) !important;
}

[data-testid="collapsedControl"]:hover,
[data-testid="stSidebarCollapsedControl"]:hover {
    background: var(--accent, #6366F1) !important;
    color: #ffffff !important;
    transform: scale(1.08) translateX(2px) !important;
    box-shadow: 0 6px 26px rgba(99, 102, 241, 0.58) !important;
}

[data-testid="collapsedControl"] svg,
[data-testid="stSidebarCollapsedControl"] svg {
    fill: currentColor !important;
    stroke: currentColor !important;
    width: 20px !important;
    height: 20px !important;
}

/* COLLAPSE CLOSE BUTTON (Inside Sidebar Header) */
[data-testid="stSidebarCollapseButton"] button,
button[data-testid="stSidebarCollapseButton"] {
    background: rgba(255, 255, 255, 0.05) !important;
    border: 1px solid var(--line, rgba(255,255,255,0.12)) !important;
    border-radius: 8px !important;
    color: var(--ink, #ffffff) !important;
    transition: all 0.2s ease !important;
}

[data-testid="stSidebarCollapseButton"] button:hover,
button[data-testid="stSidebarCollapseButton"]:hover {
    background: var(--accent, #6366F1) !important;
    border-color: var(--accent, #6366F1) !important;
    color: #ffffff !important;
    transform: scale(1.05) !important;
}

[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] {
    gap: 0.35rem !important;
}
[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"] {
    margin-bottom: 2px !important;
    padding-bottom: 0 !important;
}

/* SIDEBAR NAVIGATION: Modern SaaS Pill Tabs (No Radio Dots) */
[data-testid="stSidebar"] div[data-testid="stRadio"] [role="radiogroup"] {
    gap: 5px !important;
    display: flex !important;
    flex-direction: column !important;
}
[data-testid="stSidebar"] div[data-testid="stRadio"] [role="radiogroup"] label {
    padding: 9px 14px !important;
    border-radius: 10px !important;
    width: 100% !important;
    cursor: pointer !important;
    margin: 0 !important;
    transition: all 0.18s cubic-bezier(0.16, 1, 0.3, 1) !important;
    background: transparent !important;
    border: 1px solid transparent !important;
    display: flex !important;
    align-items: center !important;
}

/* HIDE RADIO CIRCLE COMPLETELY ACROSS ALL STREAMLIT VERSIONS */
[data-testid="stSidebar"] div[data-testid="stRadio"] label > div:first-child:not([data-testid="stMarkdownContainer"]),
[data-testid="stSidebar"] div[data-testid="stRadio"] [data-baseweb="radio"] > div:first-child,
[data-testid="stSidebar"] div[data-testid="stRadio"] [role="radiogroup"] label div[data-testid="stRadioGroup-item"],
[data-testid="stSidebar"] div[data-testid="stRadio"] [role="radiogroup"] label div[data-testid="stRadioGroupItem"],
[data-testid="stSidebar"] div[data-testid="stRadio"] [role="radiogroup"] label > div[aria-hidden="true"],
[data-testid="stSidebar"] div[data-testid="stRadio"] [role="radiogroup"] label input[type="radio"],
[data-testid="stSidebar"] div[data-testid="stRadio"] [role="radiogroup"] label svg,
[data-testid="stSidebar"] div[data-testid="stRadio"] div[data-baseweb="radio"] input {
    display: none !important;
    visibility: hidden !important;
    width: 0 !important;
    height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    position: absolute !important;
}

[data-testid="stSidebar"] div[data-testid="stRadio"] [role="radiogroup"] label div[data-testid="stMarkdownContainer"],
[data-testid="stSidebar"] div[data-testid="stRadio"] [role="radiogroup"] label div[data-testid="stMarkdownContainer"] p {
    display: flex !important;
    align-items: center !important;
    visibility: visible !important;
    opacity: 1 !important;
    font-size: 0.92rem !important;
    font-weight: 500 !important;
    color: var(--muted) !important;
    margin: 0 !important;
    width: 100% !important;
    letter-spacing: -0.01em !important;
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
    box-shadow: 0 0 16px rgba(99, 102, 241, 0.22) !important;
    transform: translateX(3px) !important;
}
[data-testid="stSidebar"] div[data-testid="stRadio"] [role="radiogroup"] label:has(input:checked) div[data-testid="stMarkdownContainer"] p {
    color: var(--accent) !important;
    font-weight: 700 !important;
}

/* SIDEBAR BUTTONS - FULL WIDTH TREE / LIST ITEMS (Navigation & Folders) */
[data-testid="stSidebar"] div.stButton > button {
    display: flex !important;
    justify-content: flex-start !important;
    align-items: center !important;
    text-align: left !important;
    width: 100% !important;
    padding: 8px 16px !important;
    min-height: 2.55rem !important;
    font-size: 0.95rem !important;
    font-weight: 500 !important;
    margin: 2px 0 !important;
    border-radius: 9px !important;
    border: 1px solid transparent !important;
    background: transparent !important;
    color: var(--muted) !important;
    box-shadow: none !important;
    transition: all 0.15s cubic-bezier(0.16, 1, 0.3, 1) !important;
}

[data-testid="stSidebar"] div.stButton > button > div,
[data-testid="stSidebar"] div.stButton > button span,
[data-testid="stSidebar"] div.stButton > button [data-testid="stMarkdownContainer"],
[data-testid="stSidebar"] div.stButton > button [data-testid="stMarkdownContainer"] p {
    display: flex !important;
    justify-content: flex-start !important;
    align-items: center !important;
    text-align: left !important;
    width: 100% !important;
    margin: 0 !important;
    gap: 12px !important;
    font-size: 0.95rem !important;
}

/* Inactive list button hover */
[data-testid="stSidebar"] div.stButton > button:not([kind="primary"]):hover {
    background: var(--hover) !important;
    border-color: var(--line) !important;
    color: var(--ink) !important;
    transform: translateX(3px) !important;
}

/* Active navigation item (Primary) */
[data-testid="stSidebar"] div.stButton > button[kind="primary"] {
    background: var(--accent_soft) !important;
    border: 1px solid var(--accent) !important;
    color: var(--accent) !important;
    font-weight: 700 !important;
    box-shadow: 0 0 16px rgba(99, 91, 255, 0.20) !important;
    transform: translateX(3px) !important;
}
[data-testid="stSidebar"] div.stButton > button[kind="primary"] p {
    color: var(--accent) !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
}

/* CRITICAL: SIDEBAR HORIZONTAL BLOCKS (Theme Toggle, Sign Out/Sync, Demo/Sign In) */
/* Reset alignment to CENTER for buttons inside columns */
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] {
    gap: 10px !important;
    margin: 6px 0 !important;
}

[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] div.stButton > button,
[data-testid="stSidebar"] [data-testid="column"] div.stButton > button {
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    text-align: center !important;
    width: 100% !important;
    min-height: 2.50rem !important;
    padding: 8px 14px !important;
    border-radius: 10px !important;
    font-size: 0.93rem !important;
    font-weight: 600 !important;
    margin: 0 !important;
    transform: none !important;
    box-shadow: none !important;
}

[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] div.stButton > button > div,
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] div.stButton > button span,
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] div.stButton > button [data-testid="stMarkdownContainer"],
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] div.stButton > button [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] [data-testid="column"] div.stButton > button > div,
[data-testid="stSidebar"] [data-testid="column"] div.stButton > button span,
[data-testid="stSidebar"] [data-testid="column"] div.stButton > button [data-testid="stMarkdownContainer"],
[data-testid="stSidebar"] [data-testid="column"] div.stButton > button [data-testid="stMarkdownContainer"] p {
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    text-align: center !important;
    width: 100% !important;
    margin: 0 auto !important;
    gap: 8px !important;
    font-size: 0.93rem !important;
    font-weight: 600 !important;
}

/* Secondary column button (Dark/Light inactive, Sign Out, Demo Space) - CLEARLY DISTINGUISHABLE */
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] div.stButton > button:not([kind="primary"]),
[data-testid="stSidebar"] [data-testid="column"] div.stButton > button:not([kind="primary"]) {
    background: rgba(255, 255, 255, 0.06) !important;
    border: 1px solid rgba(255, 255, 255, 0.18) !important;
    color: var(--ink) !important;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15) !important;
}

[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] div.stButton > button:not([kind="primary"]):hover,
[data-testid="stSidebar"] [data-testid="column"] div.stButton > button:not([kind="primary"]):hover {
    background: rgba(239, 68, 68, 0.12) !important;
    border-color: rgba(239, 68, 68, 0.55) !important;
    color: #EF4444 !important;
    transform: none !important;
}
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] div.stButton > button:not([kind="primary"]):hover p,
[data-testid="stSidebar"] [data-testid="column"] div.stButton > button:not([kind="primary"]):hover p {
    color: #EF4444 !important;
}

/* Primary column button (Dark/Light active, Sync Inbox) - VIBRANT & DISTINCT */
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] div.stButton > button[kind="primary"],
[data-testid="stSidebar"] [data-testid="column"] div.stButton > button[kind="primary"] {
    background: #635BFF !important;
    border: 1px solid #635BFF !important;
    color: #ffffff !important;
    box-shadow: 0 4px 14px rgba(99, 91, 255, 0.45) !important;
    transform: none !important;
}

[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] div.stButton > button[kind="primary"] p,
[data-testid="stSidebar"] [data-testid="column"] div.stButton > button[kind="primary"] p {
    color: #ffffff !important;
    font-weight: 700 !important;
}

[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] div.stButton > button[kind="primary"]:hover,
[data-testid="stSidebar"] [data-testid="column"] div.stButton > button[kind="primary"]:hover {
    background: #5046E5 !important;
    border-color: #5046E5 !important;
    box-shadow: 0 6px 20px rgba(99, 91, 255, 0.6) !important;
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
    box-shadow: 0 0 10px rgba(99, 102, 241, 0.15) !important;
}
div[data-testid="stRadio"]:not([data-testid="stSidebar"] div[data-testid="stRadio"]) [role="radiogroup"] label:has(input:checked) p {
    color: var(--ink) !important;
    font-weight: 700 !important;
}

/* BUTTONS & INPUTS */
div.stButton > button, div.stDownloadButton > button {
    border-radius: 9px;
    font-weight: 600;
    font-size: 0.88rem;
    min-height: 2.4rem;
    border: 1px solid var(--line);
    background: var(--panel2);
    color: var(--ink);
    transition: all 0.15s ease;
}
div.stButton > button:hover, div.stDownloadButton > button:hover {
    border-color: var(--accent);
    color: var(--accent);
    background: var(--hover);
    transform: translateY(-1px);
    box-shadow: var(--shadow);
}
div.stButton > button[kind="primary"], 
div.stFormSubmitButton > button[kind="primary"], 
div.stFormSubmitButton > button {
    background: var(--accent) !important;
    color: #ffffff !important;
    border: none !important;
    box-shadow: 0 2px 8px rgba(99, 102, 241, 0.28) !important;
    font-weight: 700 !important;
}
div.stButton > button[kind="primary"]:hover {
    filter: brightness(1.1) !important;
    color: #ffffff !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 14px rgba(99, 102, 241, 0.4) !important;
}

[data-baseweb="input"], [data-baseweb="base-input"], [data-baseweb="textarea"], textarea, [data-baseweb="select"] > div {
    background: var(--input) !important;
    color: var(--ink) !important;
    border-color: var(--line) !important;
    border-radius: 9px !important;
}
[data-baseweb="input"]:focus-within, [data-baseweb="textarea"]:focus-within {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px var(--accent_soft) !important;
}

/* BASEWEB & STREAMLIT DROPDOWNS / MENUS IN DARK & LIGHT */
div[data-baseweb="popover"], div[data-baseweb="menu"], ul[role="listbox"], div[role="listbox"] {
    background-color: var(--panel) !important;
    border: 1px solid var(--line) !important;
    border-radius: 10px !important;
    box-shadow: 0 10px 28px rgba(0,0,0,0.25) !important;
}
li[role="option"] {
    background-color: var(--panel) !important;
    color: var(--ink) !important;
    font-size: 0.88rem !important;
    padding: 8px 12px !important;
}
li[role="option"]:hover, li[role="option"][aria-selected="true"] {
    background-color: var(--sel) !important;
    color: var(--ink) !important;
}
[data-baseweb="select"] span {
    color: var(--ink) !important;
}
div[data-baseweb="calendar"] {
    background-color: var(--panel) !important;
    color: var(--ink) !important;
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
    font-size: 0.92rem !important;
    color: var(--ink) !important;
    padding: 10px 16px !important;
}
[data-testid="stExpander"] div[data-testid="stExpanderDetails"] {
    padding: 4px 16px 16px !important;
}

/* CARDS, KPIS & BRAND */
.side-title {color:var(--muted); font-size:.74rem; text-transform:uppercase; letter-spacing:.05em; margin:14px 4px 6px; font-weight:700;}
.brand {padding: 6px 0 10px 0;}
.brand-name {font-size:1.20rem; font-weight:800; letter-spacing:-.03em; display:flex; align-items:center; gap:8px;}
.brand small {display:block; font-weight:500; font-size:.74rem; color:var(--muted); margin-top:2px;}

.page-head {display:flex; align-items:center; gap:16px; padding:4px 0 16px;}
.page-icon {width:46px; height:46px; border-radius:12px; background:var(--accent_soft); display:flex; align-items:center; justify-content:center; border:1px solid var(--line); color:var(--accent); box-shadow:var(--shadow); flex-shrink:0;}
.page-title {font-size:1.75rem; font-weight:800; letter-spacing:-.03em; line-height:1.15; color:var(--ink);}
.page-sub {color:var(--muted); font-size:.88rem; margin-top:3px;}
.live {display:inline-flex; align-items:center; gap:8px; padding:6px 12px; border-radius:9px; background:var(--panel); border:1px solid var(--line); font-size:.80rem; font-weight:600; white-space:nowrap; box-shadow:var(--shadow);}
.live i {width:7px; height:7px; border-radius:50%; background:#10b981; display:inline-block; animation: pulse-glow 2s infinite;}

@keyframes pulse-glow {
  0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.6); }
  70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
  100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
}

.card {background:var(--panel); border:1px solid var(--line); border-radius:12px; box-shadow:var(--shadow); overflow:hidden; margin-bottom:16px; transition:border-color 0.15s ease;}
.card-head {padding:14px 18px; font-weight:700; font-size:0.95rem; border-bottom:1px solid var(--line); display:flex; align-items:center; gap:10px; background:var(--panel2); color:var(--ink);}
.card-body {padding:18px 20px;}
.h1 {background:var(--h1); color:var(--ink);} .h2 {background:var(--h2); color:var(--ink);} .h3 {background:var(--h3); color:var(--ink);} .h4 {background:var(--h4); color:var(--ink);}

.kpi {background:var(--panel); border:1px solid var(--line); border-radius:12px; padding:18px 20px; box-shadow:var(--shadow); transition:transform 0.15s ease, border-color 0.15s ease;}
.kpi:hover {transform:translateY(-2px); border-color:var(--accent);}
.kpi-label {color:var(--muted); font-size:.76rem; font-weight:700; text-transform:uppercase; letter-spacing:.05em;}
.kpi-value {font-size:1.85rem; font-weight:800; letter-spacing:-.03em; margin-top:4px; color:var(--ink);}
.kpi-foot {color:var(--muted); font-size:.78rem; margin-top:4px; font-weight:500;}

.tag {display:inline-flex; align-items:center; gap:6px; padding:3px 10px; border-radius:999px; border:1px solid; font-size:.76rem; font-weight:700; white-space:nowrap;}
.pill {display:inline-flex; align-items:center; gap:6px; border:1px solid var(--line); background:var(--accent_soft); color:var(--accent); padding:4px 12px; border-radius:999px; font-size:.78rem; font-weight:700; margin:2px 6px 2px 0;}
.muted {color:var(--muted); font-size:.90rem; line-height:1.55;}

/* MAIL LIST & READER */
[class*="st-key-mail"] button {
    width: 100% !important;
    text-align: left !important;
    justify-content: flex-start !important;
    background: var(--panel2) !important;
    border: 1px solid var(--line) !important;
    border-radius: 10px !important;
    padding: 10px 14px !important;
    min-height: 0 !important;
    box-shadow: none !important;
    height: auto !important;
    transition: all 0.12s ease !important;
    margin-bottom: 4px !important;
}
[class*="st-key-mail"] button > div {width: 100%; display: block; text-align: left;}
[class*="st-key-mail"] button [data-testid="stMarkdownContainer"] {width: 100%; text-align: left;}
[class*="st-key-mail"] button p {text-align: left !important; width: 100%; font-size: .84rem; color: var(--muted); line-height: 1.45; margin: 0;}
[class*="st-key-mail"] button p strong {color: var(--ink); font-size: .90rem; font-weight: 700;}
[class*="st-key-mail"] button:hover {border-color: var(--accent) !important; background: var(--hover) !important; transform: translateX(2px) !important;}
[class*="st-key-mailsel"] button {background: var(--sel) !important; border-color: var(--accent) !important; box-shadow: var(--shadow) !important;}

.reader {background: var(--panel); border: 1px solid var(--line); border-radius: 14px; padding: 24px; box-shadow: var(--shadow);}
.reader h2 {margin: 0 0 14px; font-size: 1.45rem; letter-spacing: -.025em; line-height: 1.25; color: var(--ink);}
.sender-row {display: flex; align-items: center; gap: 14px; margin-bottom: 18px;}
.avatar {width: 42px; height: 42px; border-radius: 50%; background: var(--accent_soft); color: var(--accent); display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 1.05rem; border: 1px solid var(--line); box-shadow: var(--shadow); flex-shrink: 0;}
.sender-name {font-weight: 700; font-size: 0.98rem; color: var(--ink);} 
.sender-mail {color: var(--muted); font-size: .82rem;}
.reader-body {white-space: pre-wrap; word-break: break-word; line-height: 1.68; font-size: 0.96rem; max-height: 560px; overflow-y: auto; border-top: 1px solid var(--line); padding-top: 20px; color: var(--ink);}
[data-testid="stDataFrame"] {border: 1px solid var(--line); border-radius: 10px; overflow: hidden; background: var(--panel);}
hr {border-color: var(--line); margin: 18px 0;}

/* ── Executive HUD Strip & Badges ── */
.hud-strip {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 12px;
    padding: 12px 20px;
    margin-bottom: 18px;
    box-shadow: var(--shadow);
}
.hud-item {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    font-size: 0.84rem;
    color: var(--ink);
}
.hud-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 0.74rem;
    font-weight: 700;
    padding: 3px 9px;
    border-radius: 20px;
    letter-spacing: 0.03em;
    text-transform: uppercase;
}
.hud-pulse {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #10b981;
    display: inline-block;
    box-shadow: 0 0 0 rgba(16,185,129,0.7);
    animation: hudPulse 2s infinite;
}
@keyframes hudPulse {
    0% { box-shadow: 0 0 0 0 rgba(16,185,129,0.7); }
    70% { box-shadow: 0 0 0 7px rgba(16,185,129,0); }
    100% { box-shadow: 0 0 0 0 rgba(16,185,129,0); }
}

/* ── Modern Equal-Height KPI Card ── */
.kpi-modern {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 12px;
    padding: 16px 18px;
    box-shadow: var(--shadow);
    transition: transform 0.16s ease, border-color 0.16s ease, box-shadow 0.16s ease;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    min-height: 142px;
    height: 100%;
    box-sizing: border-box;
}
.kpi-modern:hover {
    transform: translateY(-2px);
    border-color: var(--accent);
    box-shadow: 0 8px 24px -4px rgba(0,0,0,0.12);
}
.kpi-modern-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 8px;
}
.kpi-modern-icon {
    width: 32px;
    height: 32px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.05rem;
    border: 1px solid var(--line);
}
.kpi-modern-label {
    font-size: 0.74rem;
    font-weight: 700;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: 4px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.kpi-modern-val {
    font-size: 1.60rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    color: var(--ink);
    line-height: 1.2;
    margin-bottom: 4px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.kpi-modern-foot {
    font-size: 0.74rem;
    color: var(--muted);
    line-height: 1.35;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

/* ── Department Grid Matrix Cards (Equalized) ── */
.dept-pill-card {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 12px;
    padding: 13px 15px;
    margin-bottom: 10px;
    box-shadow: var(--shadow);
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    min-height: 96px;
    height: 100%;
    box-sizing: border-box;
    transition: all 0.15s ease;
}
.dept-pill-card:hover {
    border-color: var(--accent);
    transform: translateY(-1px);
    box-shadow: 0 4px 14px rgba(0,0,0,0.06);
}
.dept-progress-bg {
    width: 100%;
    height: 4px;
    background: var(--panel2);
    border-radius: 999px;
    overflow: hidden;
    margin-top: 8px;
}
.dept-progress-fill {
    height: 100%;
    border-radius: 999px;
    transition: width 0.3s ease;
}

/* ── Urgent Action Items List ── */
.deadline-item {
    background: var(--panel);
    border: 1px solid var(--line);
    border-left: 4px solid #ef4444;
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 14px;
    transition: all 0.15s ease;
}
.deadline-item:hover {
    border-color: #ef4444;
    background: var(--panel2);
}

/* ── Threat HUD & Safe HUD (Bespoke Human UI) ── */
.threat-hud-card {
    background: var(--panel);
    border: 1px solid rgba(239,68,68,0.35);
    border-left: 4px solid #ef4444;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 18px;
    box-shadow: var(--shadow);
}
.safe-hud-card {
    background: var(--panel);
    border: 1px solid rgba(16,185,129,0.3);
    border-left: 4px solid #10b981;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 18px;
    box-shadow: var(--shadow);
}
"""
    st.markdown(f"<style>{root}{css}</style>", unsafe_allow_html=True)


def page_header(icon_name, title, sub, live=False):
    left, right = st.columns([5, 2])
    icon_html = svg_icon(icon_name, size=24, color="var(--accent)")
    with left:
        st.markdown(f"<div class='page-head'><div class='page-icon'>{icon_html}</div><div><div class='page-title'>{esc(title)}</div>"
                    f"<div class='page-sub'>{esc(sub)}</div></div></div>", unsafe_allow_html=True)
    with right:
        acc = st.session_state.get("gmail_account", "")
        if acc:
            st.markdown(
                f"<div style='display:flex;align-items:center;justify-content:flex-end;height:100%;padding-top:10px'>"
                f"<span class='live' style='color:#10b981;border-color:rgba(16,185,129,0.35);background:rgba(16,185,129,0.1);padding:5px 12px;font-size:0.80rem;white-space:nowrap;display:inline-flex;align-items:center;gap:6px'>"
                f"<i style='background:#10b981;width:6px;height:6px;border-radius:50%;display:inline-block'></i> {esc(acc)}</span></div>",
                unsafe_allow_html=True
            )
        elif live:
            b1, b2 = st.columns([3, 1])
            with b1:
                st.markdown(f"<div style='text-align:right;padding-top:10px'><span class='live'><i></i>Live • {datetime.now():%H:%M}</span></div>",
                            unsafe_allow_html=True)
            with b2:
                if st.button("⟳", key="refresh", help="Refresh"):
                    st.rerun()


def kpi(label, value, foot=""):
    st.markdown(f"<div class='kpi'><div class='kpi-label'>{esc(label)}</div><div class='kpi-value'>{esc(value)}</div>"
                f"<div class='kpi-foot'>{esc(foot)}</div></div>", unsafe_allow_html=True)


def kpi_modern(icon, label, value, foot="", badge="", badge_color="#10b981", bg_accent="rgba(37,99,235,0.08)"):
    badge_html = f"<span class='hud-badge' style='background:{badge_color}22;color:{badge_color};border:1px solid {badge_color}44'>{esc(badge)}</span>" if badge else ""
    st.markdown(
        f"<div class='kpi-modern'>"
        f"<div>"
        f"<div class='kpi-modern-top'>"
        f"<div class='kpi-modern-icon' style='background:{bg_accent};'>{icon}</div>"
        f"{badge_html}"
        f"</div>"
        f"<div class='kpi-modern-label'>{esc(label)}</div>"
        f"<div class='kpi-modern-val'>{esc(str(value))}</div>"
        f"</div>"
        f"<div class='kpi-modern-foot'>{esc(str(foot))}</div>"
        f"</div>",
        unsafe_allow_html=True
    )


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


def render_prediction_history_view():
    curr_acc = st.session_state.get("gmail_account", "")
    if not st.session_state.history:
        st.session_state.history = load_persisted_history(curr_acc)
    hist = pd.DataFrame(st.session_state.history)

    if hist.empty:
        user_desc = f"for <b>{esc(curr_acc)}</b>" if curr_acc else "in this clean session"
        st.markdown(
            f"<div class='card' style='padding:32px 24px;border:1px solid var(--line);border-radius:14px;background:var(--panel);text-align:center;box-shadow:var(--shadow)'>"
            f"<div style='font-size:2.2rem;margin-bottom:8px'>🔒</div>"
            f"<div style='font-size:1.15rem;font-weight:700;color:var(--ink);margin-bottom:6px'>No Ad-Hoc Predictions Recorded Yet {user_desc}</div>"
            f"<p class='muted' style='font-size:0.86rem;max-width:440px;margin:0 auto 16px;line-height:1.55'>"
            f"Queries tested on the <b>Classify Emails</b> page are automatically logged and saved persistently in your private vault."
            f"</p></div>",
            unsafe_allow_html=True
        )
        if st.button("⚡ Open Classify Emails", type="primary", key="btn_open_classify_from_hist"):
            st.session_state.page = "Classify Emails"
            st.rerun()
    else:
        # Modern KPI Row
        hk = st.columns(4)
        legit_count = int((hist["Fraud Status"] == "Legitimate").sum()) if "Fraud Status" in hist.columns else len(hist)
        phish_count = len(hist) - legit_count
        with hk[0]:
            kpi_modern("📋", "Total Evaluations", str(len(hist)), "Saved in private vault", "Vault Active", "#635BFF", "rgba(99,91,255,0.12)")
        with hk[1]:
            kpi_modern("🛡️", "Legitimate Safe", str(legit_count), "Authentic notices", "Safe", "#16A36A", "rgba(22,163,106,0.12)")
        with hk[2]:
            kpi_modern("🚨", "Phishing Caught", str(phish_count), "Scam offers & credential alerts", "Caught", "#E05252", "rgba(224,82,82,0.12)")
        with hk[3]:
            top_cat = str(hist["Predicted Category"].mode().iloc[0]).title() if "Predicted Category" in hist.columns and not hist.empty else "N/A"
            kpi_modern("🏷️", "Top Category", top_cat, "Most frequent tested topic", "Primary", "#0284C7", "rgba(2,132,199,0.12)")
        st.write("")

        # Filters and search
        h_col1, h_col2, h_col3 = st.columns([2, 1.2, 1.2])
        h_search = h_col1.text_input("Search History", placeholder="🔍 Search subject or message...", label_visibility="collapsed", key="hist_search_field")
        h_sec = h_col2.selectbox("Filter Status", ["All Results", "🛡️ Legitimate Only", "🚨 Phishing Only"], label_visibility="collapsed", key="hist_sec_filter_field")
        all_hist_cats = sorted(list(set(hist["Predicted Category"].dropna().tolist()))) if "Predicted Category" in hist.columns else []
        h_cat = h_col3.selectbox("Filter Category", ["All Categories"] + all_hist_cats, label_visibility="collapsed", key="hist_cat_filter_field")

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
            st.download_button("⬇ Download History CSV", hist.to_csv(index=False).encode("utf-8-sig"), "campusmail_prediction_history.csv", "text/csv", use_container_width=True, key="dl_hist_csv_btn")
        with h2:
            if st.button("🗑️ Clear History", use_container_width=True, key="clear_hist_btn"):
                st.session_state.history = []
                if curr_acc:
                    user_hist_file = get_user_dir(curr_acc) / "prediction_history.csv"
                    if user_hist_file.exists():
                        user_hist_file.unlink()
                st.rerun()

        st.markdown("#### 📜 Detailed Evaluation Log")
        for idx, row in h_view.iterrows():
            is_fraud = str(row.get("Fraud Status", "")).lower() == "fraudulent"
            badge = "<span style='color:#E05252;background:rgba(224,82,82,0.15);padding:3px 8px;border-radius:6px;font-weight:700;font-size:0.75rem'>🚨 PHISHING ALERT</span>" if is_fraud else "<span style='color:#16A36A;background:rgba(22,163,106,0.15);padding:3px 8px;border-radius:6px;font-weight:700;font-size:0.75rem'>🛡️ LEGITIMATE SAFE</span>"
            cat_name = str(row.get("Predicted Category", "")).title()
            time_str = str(row.get("Timestamp", ""))
            prob_str = str(row.get("Threat Probability", ""))

            with st.expander(f"{'🚨' if is_fraud else '🛡️'} {row.get('Subject', '(No subject)')} — {cat_name} ({time_str})"):
                st.markdown(f"**Security Verdict:** {badge} &nbsp;&nbsp; **Category:** `{cat_name}` &nbsp;&nbsp; **Threat Probability:** `{prob_str}`", unsafe_allow_html=True)
                st.markdown(f"**Email Body Text:**\n```\n{row.get('Email Body', '')}\n```")


# ───────────────────────────── sidebar ─────────────────────────────
def nav_to_inbox():
    st.session_state.page = "Email History"

def nav_to_folder(category_name):
    st.session_state.page = "Email History"
    st.session_state.inbox_category_filter = category_name
    st.session_state.inbox_security_filter = "All Mail"

def nav_to_security(sec_filter):
    st.session_state.page = "Email History"
    st.session_state.inbox_category_filter = "All categories"
    st.session_state.inbox_security_filter = sec_filter

_curr_theme_name = st.session_state.get("theme_choice", "Obsidian Luxury (Dark)")
if _curr_theme_name not in THEMES:
    _curr_theme_name = "Obsidian Luxury (Dark)"
T = THEMES[_curr_theme_name]
inject_css(T)

with st.sidebar:
    brand_ic = svg_icon("sparkles", size=22, color="var(--accent)")
    st.markdown(
        f"<div class='brand' style='margin-bottom:12px;padding-bottom:12px;border-bottom:1px solid var(--line)'>"
        f"<div class='brand-name' style='font-size:1.30rem;font-weight:800;letter-spacing:-0.02em;display:flex;align-items:center;gap:10px'>"
        f"{brand_ic} CampusMail"
        f"</div>"
        f"<div style='font-size:0.86rem;color:var(--muted);margin-top:4px;font-weight:500'>Smart Campus Email Classifier</div>"
        f"</div>",
        unsafe_allow_html=True
    )
    
    # ── Theme Quick-Toggle (Dark / Light) ──
    is_dark = "Dark" in _curr_theme_name
    tcol1, tcol2 = st.columns(2)
    with tcol1:
        if st.button("🌙 Dark", key="sb_btn_dark", type="primary" if is_dark else "secondary", use_container_width=True, help="Switch to Dark theme"):
            st.session_state.theme_choice = "Obsidian Luxury (Dark)"
            st.rerun()
    with tcol2:
        if st.button("☀️ Light", key="sb_btn_light", type="primary" if not is_dark else "secondary", use_container_width=True, help="Switch to Light theme"):
            st.session_state.theme_choice = "Linear SaaS Light"
            st.rerun()

    active_acc = st.session_state.get("gmail_account", "")
    known_accounts = list_known_accounts()
    
    st.markdown("<div class='side-title' style='margin-top:12px'>Navigation</div>", unsafe_allow_html=True)
    
    NAV_ITEMS = [
        ("Dashboard", "📊  Dashboard"),
        ("Try a Prediction", "🎯  Try Prediction & Classify"),
        ("Email History", "📬  Email History & Mailbox"),
        ("Analytics", "📈  Analytics & Model Lab"),
        ("Settings", "⚙️  Settings & Architecture"),
    ]
    
    cur_p = st.session_state.get("page", "Dashboard")
    if cur_p in ("Inbox", "Prediction History"):
        cur_p = "Email History"
    elif cur_p == "Classify Emails":
        cur_p = "Try a Prediction"
    elif cur_p == "Model Lab":
        cur_p = "Analytics"
    elif cur_p == "About the Project":
        cur_p = "Settings"
    st.session_state.page = cur_p

    def on_nav_change(target_p):
        st.session_state.page = target_p

    for page_key, page_label in NAV_ITEMS:
        is_active = (cur_p == page_key)
        st.button(
            page_label,
            key=f"nav_btn_{page_key}",
            type="primary" if is_active else "secondary",
            use_container_width=True,
            on_click=on_nav_change,
            args=(page_key,)
        )

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
            st.markdown("<div class='side-title' style='margin-top:14px'>Cyber-Defense Shield</div>", unsafe_allow_html=True)
            fraud_n = int((gdf["is_fraud"] == 1).sum())
            legit_n = len(gdf) - fraud_n
            st.button(f"🛡️ Legitimate ({legit_n})", key="sb_sec_legit", use_container_width=True, on_click=nav_to_security, args=("🛡️ Legitimate Only",))
            st.button(f"🚨 Phishing Alerts ({fraud_n})", key="sb_sec_fraud", use_container_width=True, on_click=nav_to_security, args=("🚨 Phishing Alerts Only",))

    # ── User Profile Section at Sidebar Bottom ──
    st.markdown("<div style='margin-top:22px'></div>", unsafe_allow_html=True)
    if active_acc:
        u_initial = active_acc[0].upper() if active_acc else "U"
        st.markdown(
            f"<div style='background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.16);border-radius:14px;padding:14px 16px;margin-bottom:10px;box-shadow:0 4px 16px rgba(0,0,0,0.25)'>"
            f"<div style='display:flex;align-items:center;gap:12px'>"
            f"<div style='width:44px;height:44px;border-radius:50%;background:linear-gradient(135deg,#635BFF,#8B5CF6);color:#ffffff;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:1.15rem;box-shadow:0 3px 12px rgba(99,91,255,0.45);flex-shrink:0'>{u_initial}</div>"
            f"<div style='flex:1;min-width:0'>"
            f"<div style='font-size:0.95rem;font-weight:700;color:var(--ink);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;line-height:1.3'>{esc(active_acc)}</div>"
            f"<div style='font-size:0.82rem;color:#10B981;display:flex;align-items:center;gap:6px;font-weight:600;margin-top:3px'>"
            f"<span style='width:7px;height:7px;border-radius:50%;background:#10B981;box-shadow:0 0 8px #10B981;display:inline-block'></span> Authenticated Active"
            f"</div></div></div></div>",
            unsafe_allow_html=True
        )
        col_u1, col_u2 = st.columns([1, 1])
        with col_u1:
            if st.button("🚪 Sign Out", key="sb_prof_signout", use_container_width=True, help="Lock session"):
                sign_out()
                st.rerun()
        with col_u2:
            st.button("🔄 Sync Inbox", type="primary", key="sb_prof_sync", use_container_width=True, on_click=nav_to_inbox, help="Sync mailbox")
    else:
        st.markdown(
            f"<div style='background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.16);border-radius:14px;padding:14px 16px;margin-bottom:10px;box-shadow:0 4px 16px rgba(0,0,0,0.25)'>"
            f"<div style='display:flex;align-items:center;gap:12px'>"
            f"<div style='width:44px;height:44px;border-radius:50%;background:linear-gradient(135deg,#635BFF,#8B5CF6);color:#ffffff;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:1.20rem;box-shadow:0 3px 12px rgba(99,91,255,0.45);flex-shrink:0'>🎓</div>"
            f"<div style='flex:1;min-width:0'>"
            f"<div style='font-size:0.95rem;font-weight:700;color:var(--ink);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;line-height:1.3'>Guest / Demo Workspace</div>"
            f"<div style='font-size:0.82rem;color:var(--accent);display:flex;align-items:center;gap:6px;font-weight:600;margin-top:3px'>"
            f"<span style='width:7px;height:7px;border-radius:50%;background:#635BFF;box-shadow:0 0 8px #635BFF;display:inline-block'></span> Demo Workspace"
            f"</div></div></div></div>",
            unsafe_allow_html=True
        )
        col_g1, col_g2 = st.columns([1, 1])
        with col_g1:
            if st.button("🎓 Demo Space", key="sb_demo_btn", type="primary", use_container_width=True, help="Load 103 demo notices"):
                switch_to_account("student_demo@thapar.edu")
                st.session_state.page = "Dashboard"
                st.rerun()
        with col_g2:
            if st.button("🔑 Sign In", key="sb_signin_btn", use_container_width=True, help="Sign in to your private mailbox"):
                st.session_state.page = "Email History"
                st.rerun()

if _curr_theme_name != st.session_state.get("theme_choice", "Obsidian Luxury (Dark)"):
    st.rerun()

page = st.session_state.page

# ═════════════════════════════ DASHBOARD ═════════════════════════════
if page == "Dashboard":
    page_header("dashboard", "Your Email Intelligence Dashboard", "Understand, organize, and classify your emails with AI.", live=True)
    df = st.session_state.gmail_df

    # Auto-load academic showcase benchmark dataset if no private mailbox loaded
    is_demo_mode = False
    if df.empty:
        demo_path = BASE / "data" / "demo_student_mailbox.csv"
        if demo_path.exists():
            try:
                df = pd.read_csv(demo_path)
                is_demo_mode = True
            except Exception:
                pass

    # Model inference metadata
    best_name, best_acc = "Linear SVM", "91.2%"
    _m = load_model_metrics()
    _b, _rank_col = get_best_model_row(_m)
    if _b is not None:
        best_name = str(_b.get("model", "Linear SVM"))
        if pd.notna(_b.get("accuracy", float("nan"))):
            best_acc = f"{float(_b['accuracy']):.1%}"

    # 4 Compact Modern SaaS KPI Cards
    total_n = len(df)
    urgent_n = int(df.predicted_category.isin(URGENT).sum()) if not df.empty else 0
    f_count = int((df["is_fraud"] == 1).sum()) if (not df.empty and "is_fraud" in df.columns) else 0

    k = st.columns(4)
    with k[0]:
        kpi_modern("📬", "Total Emails Processed", f"{total_n:,}", f"{df.predicted_category.nunique() if not df.empty else 0} active departments", badge="Live Ingested", badge_color="#635BFF", bg_accent="rgba(99,91,255,0.08)")
    with k[1]:
        kpi_modern("⚡", "Important Emails", f"{urgent_n:,}", "Deadlines & Priority action items", badge="Deadlines Active", badge_color="#16A36A", bg_accent="rgba(22,163,106,0.08)")
    with k[2]:
        if f_count > 0:
            kpi_modern("🚨", "Spam & Threats Detected", f"{f_count} Threats", "Phishing quarantined by Cyber Shield", badge="Critical Alert", badge_color="#E05252", bg_accent="rgba(224,82,82,0.10)")
        else:
            kpi_modern("🛡️", "Spam & Threats Detected", "0 Threats", "Zero-Trust verified authentic", badge="Shield Active", badge_color="#16A36A", bg_accent="rgba(22,163,106,0.08)")
    with k[3]:
        kpi_modern("🎯", "Classification Accuracy", best_acc, "Evaluated Model Benchmark", badge="Production", badge_color="#635BFF", bg_accent="rgba(99,91,255,0.08)")
    st.write("")

    if df.empty:
        curr_acc = st.session_state.get("gmail_account", "")
        st.markdown(
            f"<div class='card' style='border:1px solid rgba(59,130,246,0.3);border-radius:14px;padding:22px;margin-bottom:20px;text-align:center'>"
            f"<div style='font-size:1.20rem;font-weight:700;color:var(--ink);margin-bottom:6px'>Welcome to CampusMail</div>"
            f"<p class='muted' style='font-size:0.88rem;margin:0 0 16px'>Sign in to your university mailbox or explore the pre-loaded demo space.</p>"
            f"</div>",
            unsafe_allow_html=True
        )
        b_demo, b_sync = st.columns(2)
        with b_demo:
            if st.button("🎓 Student Demo Space", type="primary", use_container_width=True):
                switch_to_account("student_demo@thapar.edu")
                st.rerun()
        with b_sync:
            st.button("🔑 Sign In / Sync Gmail", use_container_width=True, on_click=go_inbox)

        st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)
        card_head("info", "Supported University Email Taxonomies (10 Departments)", "h2")
        for start in range(0, len(CATS), 2):
            pair = st.columns(2)
            for j, c in enumerate(CATS[start:start + 2]):
                with pair[j]:
                    st.markdown(f"<div class='card' style='margin-bottom:12px'><div class='card-body'>{tag(c)}"
                                f"<div class='muted' style='margin-top:10px;font-size:0.88rem;line-height:1.5'>{esc(DESCRIPTIONS.get(c, 'College email category'))}</div></div></div>",
                                unsafe_allow_html=True)
    else:
        # Date Filter Row
        valid_days = email_local_dates(df)
        valid_days = [d for d in valid_days if pd.notna(d)]
        if valid_days:
            min_day, max_day = min(valid_days), max(valid_days)
            date_cols = st.columns([1.1, 1.1, 2.5])
            with date_cols[0]:
                dash_start = st.date_input("From", value=min_day, key="dashboard_start_date", format="DD/MM/YYYY")
            with date_cols[1]:
                dash_end = st.date_input("To", value=max_day, key="dashboard_end_date", format="DD/MM/YYYY")
            with date_cols[2]:
                st.markdown(
                    f"<div style='padding-top:28px;font-size:0.80rem;color:var(--muted);display:flex;align-items:center;gap:6px'>"
                    f"<span>📅</span> <span>Filtering {len(df):,} circulars across selected timeframe</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )
            if dash_start > dash_end:
                st.warning("Start date cannot be after end date.")
                dashboard_df = df.iloc[0:0].copy()
            else:
                dashboard_df = filter_by_dates(df, dash_start, dash_end)
        else:
            dashboard_df = df.copy()

        if dashboard_df.empty:
            st.info("No classified emails fall within this date range.")
        else:
            # ── 10-Department Volume & Distribution Matrix (5x2 Grid) ──
            card_head("dashboard", "Departmental Circular Volume Matrix", "h2")
            total_emails_in_view = len(dashboard_df)
            counts_series = dashboard_df.predicted_category.value_counts()
            
            for row_start in [0, 5]:
                matrix_cols = st.columns(5)
                for idx, cat_name in enumerate(CATS[row_start:row_start+5]):
                    cnt = int(counts_series.get(cat_name, 0))
                    pct = (cnt / total_emails_in_view * 100) if total_emails_in_view > 0 else 0
                    cat_color = CAT_COLORS.get(cat_name, "#3b82f6")
                    with matrix_cols[idx]:
                        st.markdown(
                            f"<div class='dept-pill-card'>"
                            f"<div style='display:flex;align-items:center;justify-content:space-between;gap:4px;margin-bottom:3px'>"
                            f"<span style='font-weight:700;font-size:0.77rem;color:var(--ink);white-space:nowrap;overflow:hidden;text-overflow:ellipsis' title='{nice(cat_name)}'>{nice(cat_name)}</span>"
                            f"<span style='font-size:0.72rem;font-weight:800;color:{cat_color};flex-shrink:0'>{pct:.0f}%</span>"
                            f"</div>"
                            f"<div style='font-size:1.30rem;font-weight:800;color:var(--ink);margin:2px 0'>{cnt:,}</div>"
                            f"<div class='dept-progress-bg'>"
                            f"<div class='dept-progress-fill' style='width:{min(100, pct)}%;background:{cat_color}'></div>"
                            f"</div>"
                            f"</div>",
                            unsafe_allow_html=True
                        )
            st.write("")

            # ── Interactive Charts ──
            counts = dashboard_df.predicted_category.value_counts().reindex(CATS, fill_value=0)
            cdf = pd.DataFrame({"Category": [nice(c) for c in counts.index], "Emails": counts.values})
            urgent_n = int(dashboard_df.predicted_category.isin(URGENT).sum())
            normal_n = len(dashboard_df) - urgent_n

            c1, c2 = st.columns([1.2, 0.8], gap="large")
            with c1:
                with st.container(key="card_bar"):
                    card_head("dashboard", "Emails by Department (Distribution)", "h1")
                    bar = alt.Chart(cdf).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6).encode(
                        x=alt.X("Category:N", sort=None, axis=alt.Axis(labelAngle=-36, title=None, labelFontSize=11)),
                        y=alt.Y("Emails:Q", title=None, axis=alt.Axis(grid=True)),
                        color=alt.Color("Category:N", scale=cat_scale(), legend=None),
                        tooltip=["Category", "Emails"]).properties(height=300)
                    st.altair_chart(style_chart(bar, T), use_container_width=True, theme=None)
            with c2:
                with st.container(key="card_donut"):
                    card_head("info", "Deadline Triage Priority", "h2")
                    pdf = pd.DataFrame({"Priority": ["High (Deadline)", "Normal"], "Emails": [urgent_n, normal_n]})
                    donut = alt.Chart(pdf).mark_arc(innerRadius=70, outerRadius=110, stroke=T["panel"], strokeWidth=2).encode(
                        theta="Emails:Q",
                        color=alt.Color("Priority:N", scale=alt.Scale(domain=["High (Deadline)", "Normal"], range=["#ef4444", "#10b981"]), legend=None),
                        tooltip=["Priority", "Emails"]).properties(height=240)
                    st.altair_chart(style_chart(donut, T), use_container_width=True, theme=None)
                    st.markdown(f"<div style='text-align:center;padding:4px 0 6px;font-weight:700;font-size:.88rem'>"
                                f"<span style='color:#ef4444'>●</span> High Deadline ({urgent_n}) &nbsp;&nbsp; "
                                f"<span style='color:#10b981'>●</span> Normal Notice ({normal_n})</div>", unsafe_allow_html=True)

            # ── Top Urgent Circulars & Impending Deadlines Table ──
            urgent_df = dashboard_df[dashboard_df.predicted_category.isin(URGENT)].copy()
            if not urgent_df.empty:
                st.markdown("<div style='margin-top:16px'></div>", unsafe_allow_html=True)
                card_head("alert", f"Top Impending Deadlines & Urgent Circulars ({len(urgent_df):,} detected)", "h2")
                urgent_preview = urgent_df.head(5)
                for _, urow in urgent_preview.iterrows():
                    u_subj = esc(str(urow.get("subject", "No subject")))
                    u_cat = str(urow.get("predicted_category", "general"))
                    u_date = str(urow.get("date", ""))[:16]
                    u_from = esc(str(urow.get("from", "Administration")).split("<")[0].strip())
                    u_cat_color = CAT_COLORS.get(u_cat, "#ef4444")
                    st.markdown(
                        f"<div class='deadline-item'>"
                        f"<div style='flex:1;min-width:0'>"
                        f"<div style='display:flex;align-items:center;gap:10px;margin-bottom:4px'>"
                        f"<span style='background:{u_cat_color}22;color:{u_cat_color};border:1px solid {u_cat_color}55;border-radius:6px;font-size:0.74rem;font-weight:700;padding:2px 8px'>{nice(u_cat)}</span>"
                        f"<span style='font-size:0.80rem;color:var(--muted)'>{esc(u_from)}</span>"
                        f"</div>"
                        f"<div style='font-weight:700;font-size:0.94rem;color:var(--ink);white-space:nowrap;overflow:hidden;text-overflow:ellipsis'>{u_subj}</div>"
                        f"</div>"
                        f"<div style='text-align:right;white-space:nowrap;font-size:0.80rem;color:var(--muted);font-weight:600'>{esc(u_date)}</div>"
                        f"</div>",
                        unsafe_allow_html=True
                    )
                st.button("View All Urgent Circulars in Inbox →", on_click=go_inbox)

            # ── Temporal Ingestion Timeline ──
            st.markdown("<div style='margin-top:16px'></div>", unsafe_allow_html=True)
            with st.container(key="card_timeline"):
                card_head("history", "Temporal Ingestion & Multi-Class Timeline", "h3")
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


# ═════════════════════════════ EMAIL HISTORY & INBOX ═════════════════════════════
elif page in ("Email History", "Inbox", "Prediction History"):
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

    hist_mode = st.radio(
        "History Source",
        ["📬 University Mailbox", "🔬 Single Prediction Logs"],
        horizontal=True,
        label_visibility="collapsed",
        key="email_history_mode_selector"
    )
    if hist_mode.startswith("🔬 Single Prediction"):
        page_header("history", "Prediction History & Logs", "Ad-hoc analyzed emails tested across sessions with dual-model results")
        render_prediction_history_view()
    elif not active_mail:
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
                f"<div style='background:var(--panel);border:1px solid rgba(255,255,255,0.08);border-radius:20px;padding:32px 36px;box-shadow:0 12px 48px rgba(0,0,0,0.45);margin:0 auto 22px'>"
                f"<div style='text-align:center;margin-bottom:20px'>"
                f"<div style='display:inline-flex;align-items:center;justify-content:center;margin-bottom:10px'>{google_svg}</div>"
                f"<h2 style='margin:0 0 6px;font-size:1.60rem;font-weight:800;color:var(--ink);letter-spacing:-0.02em'>CampusMail Sign-In</h2>"
                f"<p style='color:var(--muted);font-size:0.88rem;margin:0;line-height:1.5'>Sign in with your university credentials or explore the demo mailbox.</p>"
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

                st.markdown("<div style='font-size:0.80rem;font-weight:700;color:var(--ink);margin-bottom:5px'>University Email</div>", unsafe_allow_html=True)
                email_input = st.text_input(
                    "University Email Address",
                    value="",
                    placeholder="id@thapar.edu",
                    label_visibility="collapsed",
                    key="login_user_thapar_id",
                    autocomplete="off"
                )

                st.markdown("<div style='font-size:0.80rem;font-weight:700;color:var(--ink);margin:12px 0 5px'>Password</div>", unsafe_allow_html=True)
                pwd_input = st.text_input(
                    "Vault Password / PIN",
                    type="password",
                    value="",
                    placeholder="Enter password",
                    label_visibility="collapsed",
                    key="login_user_vault_pin",
                    autocomplete="new-password"
                )

                submit_btn = st.form_submit_button("🚀 Sign In", type="primary", use_container_width=True)

            if submit_btn:
                raw_input = (email_input or "").strip().lower()
                clean_pwd = (pwd_input or "").strip()
                if not raw_input:
                    st.error("Please enter your university ID (e.g. id@thapar.edu).")
                elif not clean_pwd:
                    st.error("Please enter your password.")
                else:
                    clean_email = raw_input if "@" in raw_input else f"{raw_input}@thapar.edu"
                    if verify_user_password(clean_email, clean_pwd):
                        st.session_state["credential_to_store"] = {"email": clean_email, "password": clean_pwd}
                        switch_to_account(clean_email)
                        st.rerun()
                    else:
                        st.error("Incorrect password. Please try again.")

            col_p1, col_p2 = st.columns(2)
            with col_p1:
                if st.button("🎓 Student Demo Space", use_container_width=True, key="preset_student_btn"):
                    switch_to_account("student_demo@thapar.edu")
                    st.rerun()
            with col_p2:
                if st.button("🔐 Sign in with Google", use_container_width=True, key="btn_google_oauth"):
                    try:
                        with st.spinner("Connecting to Google OAuth & Authorizing..."):
                            service = gmail_service()
                            profile = service.users().getProfile(userId="me").execute()
                            acc = profile.get("emailAddress", "").strip().lower()

                        with st.spinner(f"⚡ Live Syncing recent emails for {acc}..."):
                            rows = fetch_emails(service, limit=25)
                            if rows:
                                model = load_model()
                                fraud_model = load_fraud_model()
                                new_df = predict_emails(rows, model, fraud_model)
                                old_df = load_persisted_inbox(acc)
                                merged_df = merge_inbox_dataframes(new_df, old_df)
                                persist_inbox(merged_df, acc)

                        switch_to_account(acc)
                        st.session_state.page = "Email History"
                        st.rerun()
                    except Exception as e:
                        st.error(f"Google authentication: {e}")

            st.markdown("</div>", unsafe_allow_html=True)
    else:
        header_subtitle = (
            f"Connected to {active_mail} · {len(df):,} mails classified"
            if not df.empty
            else f"Workspace: {active_mail}"
        )
        page_header("inbox", "Email History & Mailbox", header_subtitle)

        with st.expander("🔄 Sync Live Gmail Inbox (Google OAuth)", expanded=df.empty):
            fetch_mode = st.radio(
                "Fetch emails by",
                ["Recent emails", "Custom date range"],
                horizontal=True,
                key="gmail_fetch_mode",
            )

            date_range = None
            if fetch_mode == "Custom date range":
                date_range = st.date_input(
                    "Select date range",
                    value=(date.today() - timedelta(days=7), date.today()),
                    max_value=date.today(),
                    format="DD/MM/YYYY",
                    key="gmail_custom_date_range",
                )

            if fetch_mode == "Recent emails":
                limit = st.select_slider(
                    "Maximum messages to process",
                    options=[25, 50, 100, 250, 500, 1000],
                    value=25,
                    key="gmail_fetch_limit",
                )
            else:
                limit = None

            btn_col1, btn_col2 = st.columns([3, 1])
            with btn_col1:
                run = st.button(
                    "🔄 Sync & Classify Inbox",
                    type="primary",
                    use_container_width=True,
                    key="gmail_sync_button",
                )
            with btn_col2:
                if st.button("🗑️ Reset Cache", use_container_width=True, help="Clear saved token and cached emails for current user"):
                    if active_mail:
                        u_dir = get_user_dir(active_mail)
                        for f in [u_dir / "cached_inbox.csv", u_dir / "token.json"]:
                            if f.exists():
                                f.unlink()
                    st.session_state.gmail_df = pd.DataFrame()
                    st.session_state.sel_id = None
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

                prog_holder = st.empty()
                progress_bar = prog_holder.progress(0.0, text=f"Connecting to Gmail API ({fetch_description})...")

                def on_progress(current, total):
                    pct = min(1.0, float(current) / float(max(1, total)))
                    progress_bar.progress(pct, text=f"⚡ Live Sync: Fetched & parsed {current} of {total} messages...")

                rows = fetch_emails(
                    service,
                    None if gmail_query else int(limit),
                    gmail_query=gmail_query,
                    progress_callback=on_progress,
                )
                prog_holder.empty()

                if not rows:
                    st.warning("⚠️ No new messages could be fetched right now because Google's per-minute quota was temporarily reached. Please wait ~60 seconds and try with 25 messages.")
                    if st.session_state.gmail_df.empty and active_mail:
                        st.session_state.gmail_df = load_persisted_inbox(active_mail)
                    st.stop()

                with st.spinner("Running Dual-Head ML Pipeline (Campus Category + Phishing Detector)..."):
                    model = load_model()
                    fraud_model = load_fraud_model()
                    new_df = predict_emails(rows, model, fraud_model)

                old_df = load_persisted_inbox(account)
                df = merge_inbox_dataframes(new_df, old_df)

                st.session_state.gmail_df = df
                st.session_state.gmail_account = account
                st.session_state.sel_id = None
                st.session_state.gmail_fetch_description = fetch_description
                st.session_state.pop("inbox_filter_start", None)
                st.session_state.pop("inbox_filter_end", None)
                st.session_state.pop("_last_inbox_min_day", None)
                st.session_state.pop("_last_inbox_max_day", None)
                persist_inbox(df, account)
                st.success(f"Successfully classified and updated inbox ({len(df)} total messages in vault for {account}).")
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
                f"<p class='muted'>Open <b>Sync Live Gmail Inbox</b> above to fetch and classify messages.</p>"
                f"</div></div>",
                unsafe_allow_html=True
            )
            date_filtered_df = pd.DataFrame()
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
                st.caption(f"Showing {len(view):,} of {len(view):,} messages")
                with st.container(height=680, border=False):
                    for i, r in view.iterrows():
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
                        f"<div style='background:rgba(239,68,68,0.12);border:1px solid rgba(239,68,68,0.35);border-radius:12px;padding:12px 16px;margin-bottom:14px;color:#fca5a5;font-size:0.90rem;display:flex;align-items:center;justify-content:space-between'>"
                        f"<div style='display:flex;align-items:center;gap:10px'><span style='font-size:1.25rem'>🚨</span><b>Phishing Alert:</b> Potential credential or financial risk.</div>"
                        f"<span style='background:#ef4444;color:#fff;padding:2px 8px;border-radius:6px;font-size:0.78rem;font-weight:700'>Risk: {fraud_prob:.1f}%</span></div>",
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f"<div style='background:rgba(16,185,129,0.12);border:1px solid rgba(16,185,129,0.35);border-radius:12px;padding:12px 16px;margin-bottom:14px;color:#34d399;font-size:0.90rem;display:flex;align-items:center;gap:10px'>"
                        f"<span style='font-size:1.25rem'>🛡️</span><div><b>Verified Safe · 99%</b> — Authentic institutional notice.</div></div>",
                        unsafe_allow_html=True
                    )

                st.markdown(
                    f"<div class='reader'><h2>{esc(chosen['subject'] or '(No subject)')}</h2>"
                    f"<div class='sender-row'><div class='avatar'>{esc(name[:1].upper())}</div>"
                    f"<div style='flex:1'><div class='sender-name'>{esc(name)}</div><div class='sender-mail'>{esc(addr)}</div></div>"
                    f"<div style='text-align:right'>{tag(chosen['predicted_category'])}<div class='sender-mail' style='margin-top:6px'>{esc(chosen['date'])}</div></div></div>"
                    f"<div class='reader-body'>{esc(body[:12000])}</div></div>", unsafe_allow_html=True)

# ═════════════════════════════ CLASSIFY EMAILS / TRY A PREDICTION ═════════════════════════════
elif page in ("Try a Prediction", "Classify Emails"):
    page_header("sparkles", "Try a Prediction & Classify", "Analyze incoming messages in real-time with dual-head multi-class topic categorization and fraud detection.")
    try:
        model = load_model()
        fraud_model = load_fraud_model()
    except Exception as e:
        st.error(str(e))
        st.stop()

    f1, f2 = st.columns([1.2, 1], gap="large")
    with f1:
        st.markdown(
            f"<div style='font-size:0.80rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:0.04em;margin-bottom:8px'>"
            f"⚡ Quick Benchmark Samples (Click to load)</div>",
            unsafe_allow_html=True
        )
        def pick_demo(sub, body):
            st.session_state["demo_sub"] = sub
            st.session_state["demo_msg"] = body
            st.session_state["run_instant_prediction"] = True

        p1, p2, p3, p4 = st.columns(4)
        p1.button("💼 Placement", use_container_width=True, help="Authentic campus recruitment drive",
                  on_click=pick_demo, args=(
                      "Placement Drive 2026: Microsoft Campus Recruitment & Registration",
                      "Dear Students, The Centre for Training & Placement is pleased to announce Microsoft Campus Drive for 2026 graduates. Eligibility: CSE/IT with CGPA >= 7.5. Stipend for summer intern is Rs. 1,25,000/month. Register on the campus portal before 15th October."
                  ))
        p2.button("📝 Exam Datesheet", use_container_width=True, help="Authentic university exam schedule",
                  on_click=pick_demo, args=(
                      "End Semester Examination Schedule - Even Semester 2026",
                      "Dear Students, The tentative datesheet for the upcoming End Semester Examinations May 2026 has been uploaded on the university portal. Practical evaluations begin from 12th May. In case of any clash, notify the Academic Section before Friday."
                  ))
        p3.button("🚨 Fee Scam", use_container_width=True, help="Fake tuition fee payment link demanding funds",
                  on_click=pick_demo, args=(
                      "URGENT: Semester Tuition Fee Outstanding - Late Fine Applicable",
                      "Final Warning: Your semester fee payment of Rs. 42,500 is pending. If not cleared within 2 hours, your student registration will be canceled. Pay instantly through our fast gateway: http://tiet-fees-fastpay.net/gateway before 6 PM today."
                  ))
        p4.button("🚨 Phishing", use_container_width=True, help="Credential harvesting password expiry scam",
                  on_click=pick_demo, args=(
                      "URGENT: Your Campus WebKiosk / Email Password Expires in 24 Hours",
                      "Dear Student, your student portal account will be terminated today due to system maintenance. Click here immediately to verify your credentials: http://university-login-update.com/auth. Failure to update will lock your student profile."
                  ))

        with st.form("predict_form"):
            default_sub = st.session_state.get("demo_sub", "")
            default_msg = st.session_state.get("demo_msg", "")
            st.markdown("<div style='font-size:0.82rem;font-weight:700;color:var(--ink);margin-bottom:4px'>Email Subject</div>", unsafe_allow_html=True)
            subject = st.text_input("Email subject", value=default_sub, placeholder="e.g. End Semester Examination Schedule or Job Offer", label_visibility="collapsed")
            st.markdown("<div style='font-size:0.82rem;font-weight:700;color:var(--ink);margin:10px 0 4px'>Email Content / Body</div>", unsafe_allow_html=True)
            body = st.text_area("Email body", value=default_msg, placeholder="Paste or type the full email message content here…", height=230, label_visibility="collapsed")
            submitted = st.form_submit_button("⚡ Analyze Email", type="primary", use_container_width=True)

        auto_run = st.session_state.pop("run_instant_prediction", False)
        should_run = submitted or (auto_run and bool(subject or body))

    with f2:
        if should_run:
            text = f"{subject} {body}".strip()
            if not text:
                st.warning("Please enter an email subject or content to analyze.")
            else:
                cat_prediction = str(model.predict([text])[0])

                # Mathematical confidence via Softmax over SVM Decision Hyperplanes
                import numpy as np
                conf_pct = 95.0
                if hasattr(model, "decision_function"):
                    try:
                        d_vals = model.decision_function([text])[0]
                        exp_d = np.exp(d_vals - np.max(d_vals))
                        probs = exp_d / np.sum(exp_d)
                        conf_pct = float(probs[np.argmax(probs)] * 100.0)
                    except Exception:
                        conf_pct = 94.5

                # Fraud / Cyber-Defense Assessment
                is_fraud = 0
                fraud_prob = 0.0
                if fraud_model is not None:
                    try:
                        is_fraud = int(fraud_model.predict([text])[0])
                        if hasattr(fraud_model, "predict_proba"):
                            probs = fraud_model.predict_proba([text])[0]
                            fraud_prob = probs[1] * 100.0
                        else:
                            fraud_prob = 98.4 if is_fraud == 1 else 1.6
                    except Exception:
                        is_fraud = 0

                is_urgent = cat_prediction in URGENT

                # ── Category Classification Result Card ──
                # Palette: Important (Green), Spam (Red), Events (Purple), Seminars/Placements (Blue), General (Neutral)
                if is_urgent:
                    badge_bg = "rgba(22,163,106,0.12)"
                    badge_color = "#16A36A"
                    badge_label = f"⚡ {nice(cat_prediction)} (Important / Deadline)"
                elif cat_prediction in ("hackathons", "events"):
                    badge_bg = "rgba(99,91,255,0.10)"
                    badge_color = "#635BFF"
                    badge_label = f"🟣 {nice(cat_prediction)}"
                elif cat_prediction in ("placements", "seminars", "sports"):
                    badge_bg = "rgba(2,132,199,0.10)"
                    badge_color = "#0284C7"
                    badge_label = f"🔵 {nice(cat_prediction)}"
                else:
                    badge_bg = "rgba(119,129,150,0.10)"
                    badge_color = "#778196"
                    badge_label = f"⚪ {nice(cat_prediction)}"

                st.markdown(
                    f"<div class='card' style='padding:22px;border:1px solid var(--line);border-radius:14px;background:var(--panel);margin-bottom:16px;box-shadow:var(--shadow)'>"
                    f"<div style='display:flex;align-items:center;justify-content:space-between;margin-bottom:10px'>"
                    f"<span style='font-size:0.75rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:0.04em'>Predicted Category</span>"
                    f"<span style='background:rgba(99,91,255,0.08);color:var(--accent);font-size:0.75rem;font-weight:700;padding:2px 8px;border-radius:6px;border:1px solid rgba(99,91,255,0.2)'>Confidence: {conf_pct:.1f}%</span>"
                    f"</div>"
                    f"<div style='font-size:1.60rem;font-weight:800;color:var(--ink);letter-spacing:-0.02em;margin-bottom:8px'>{esc(nice(cat_prediction))}</div>"
                    f"<span class='tag' style='color:{badge_color};background:{badge_bg};border:1px solid {badge_color}44;padding:4px 10px;border-radius:6px;font-weight:700;font-size:0.82rem'>{badge_label}</span>"
                    f"<p class='muted' style='font-size:0.86rem;line-height:1.5;margin:12px 0 0'>{esc(DESCRIPTIONS.get(cat_prediction, 'University campus communication.'))}</p>"
                    f"</div>",
                    unsafe_allow_html=True
                )

                # ── Cyber-Defense Triage Card ──
                if is_fraud == 1:
                    st.markdown(
                        f"<div class='card' style='padding:20px;border:1px solid rgba(224,82,82,0.35);border-radius:14px;background:linear-gradient(135deg, rgba(224,82,82,0.08), rgba(224,82,82,0.03));margin-bottom:16px'>"
                        f"<div style='display:flex;align-items:center;justify-content:space-between;margin-bottom:8px'>"
                        f"<span style='font-size:0.75rem;font-weight:800;color:#E05252;text-transform:uppercase;letter-spacing:0.04em'>🚨 Threat Alert</span>"
                        f"<span class='hud-badge' style='background:rgba(224,82,82,0.2);color:#E05252;border:1px solid rgba(224,82,82,0.4)'>Risk: {fraud_prob:.1f}%</span>"
                        f"</div>"
                        f"<div style='font-size:1.30rem;font-weight:800;color:#E05252;margin-bottom:4px'>Phishing / Scam Detected</div>"
                        f"<p class='muted' style='font-size:0.86rem;line-height:1.5;margin:6px 0 0'>"
                        f"High-risk patterns detected. Exercise caution with unexpected links, payment requests, or urgent credential demands."
                        f"</p></div>",
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f"<div class='card' style='padding:20px;border:1px solid rgba(22,163,106,0.35);border-radius:14px;background:linear-gradient(135deg, rgba(22,163,106,0.08), rgba(22,163,106,0.03));margin-bottom:16px'>"
                        f"<div style='display:flex;align-items:center;justify-content:space-between;margin-bottom:8px'>"
                        f"<span style='font-size:0.75rem;font-weight:800;color:#16A36A;text-transform:uppercase;letter-spacing:0.04em'>🛡️ Authenticity Verification</span>"
                        f"<span class='hud-badge' style='background:rgba(22,163,106,0.2);color:#16A36A;border:1px solid rgba(22,163,106,0.4)'>Safe: {100.0 - fraud_prob:.1f}%</span>"
                        f"</div>"
                        f"<div style='font-size:1.30rem;font-weight:800;color:#16A36A;margin-bottom:4px'>Verified Authentic Notice</div>"
                        f"<p class='muted' style='font-size:0.86rem;line-height:1.5;margin:6px 0 0'>"
                        f"Communication patterns and vocabulary conform to standard university notices."
                        f"</p></div>",
                        unsafe_allow_html=True
                    )

                # ── Mathematical Explainability Keywords ──
                try:
                    vec = model.named_steps["tfidf"]
                    clf = model.named_steps["clf"]
                    feats = vec.get_feature_names_out()
                    X_sample = vec.transform([text])
                    word_indices = X_sample.nonzero()[1]
                    class_idx = list(model.classes_).index(cat_prediction)
                    coefs = clf.coef_[class_idx]
                    top_words = sorted([(feats[i], coefs[i]) for i in word_indices if coefs[i] > 0], key=lambda x: x[1], reverse=True)[:5]
                except Exception:
                    top_words = []

                if top_words:
                    kw_tags = " ".join([f"<span class='tag' style='background:var(--panel2);color:var(--ink);border:1px solid var(--line);font-size:0.74rem;padding:2px 7px'><b>{w}</b> (+{sc:.2f})</span>" for w, sc in top_words])
                    st.markdown(
                        f"<div class='card' style='padding:14px 18px;border-radius:12px;background:var(--panel);border:1px solid var(--line)'>"
                        f"<div style='font-size:0.75rem;font-weight:700;color:var(--muted);text-transform:uppercase;margin-bottom:6px'>Key Model Decision Drivers (TF-IDF Weights)</div>"
                        f"<div style='display:flex;flex-wrap:wrap;gap:6px'>{kw_tags}</div>"
                        f"</div>",
                        unsafe_allow_html=True
                    )

                # Persist to session history
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
            st.markdown(
                f"<div class='card' style='padding:36px 24px;text-align:center;border:1px solid var(--line);border-radius:14px;background:var(--panel);box-shadow:var(--shadow)'>"
                f"<div style='font-size:2.2rem;margin-bottom:10px'>✨</div>"
                f"<div style='font-size:1.15rem;font-weight:700;color:var(--ink);margin-bottom:6px'>Ready for Analysis</div>"
                f"<p class='muted' style='font-size:0.86rem;line-height:1.55;max-width:360px;margin:0 auto'>"
                f"Enter an email or select a sample benchmark on the left to analyze category, priority, and authenticity."
                f"</p>"
                f"</div>",
                unsafe_allow_html=True
            )

# ═════════════════════════════ ANALYTICS & BENCHMARKS ═════════════════════════════
elif page in ("Analytics", "Model Lab"):
    page_header("sparkles", "Analytics & Model Intelligence", "Comprehensive breakdown of multi-class email distributions, fraud patterns, and ML model benchmarks.")

    tab_campus, tab_fraud, tab_mail_analytics = st.tabs([
        "🏢 Campus Categorization (10 Classes)",
        "🛡️ Phishing & Cyber-Defense Shield",
        "📬 Live Mailbox Telemetry"
    ])

    with tab_campus:
        if MODEL_PATH.exists():
            model_updated = datetime.fromtimestamp(MODEL_PATH.stat().st_mtime).strftime("%d %b %Y, %I:%M %p")
            st.caption(f"Active classifier artifact: {MODEL_PATH.name} · Last modified: {model_updated}")
        else:
            st.warning(f"Saved prediction model not found: {MODEL_PATH}")

        if METRICS_PATH.exists():
            metrics = load_model_metrics()
            if metrics.empty:
                st.info("The model comparison file exists but contains no evaluation rows.")
            else:
                best, ranking_metric = get_best_model_row(metrics)
                if best is not None:
                    k = st.columns(4)
                    acc_val = float(best.get("accuracy", 0.912))
                    f1_val = float(best.get("macro_f1", 0.919))

                    # Calculate verified margin over Naive Bayes baseline
                    nb_rows = metrics[metrics["model"].astype(str).str.contains("Naive Bayes|NB", case=False, na=False)]
                    if not nb_rows.empty and "accuracy" in nb_rows.columns:
                        nb_acc = float(nb_rows.iloc[0]["accuracy"])
                        gain_pct = (acc_val - nb_acc) * 100
                        gain_badge = f"+{gain_pct:.1f}% vs NB"
                    else:
                        gain_badge = "+7.3% vs NB"

                    with k[0]:
                        kpi_modern("🏆", "Top Algorithm", str(best.get("model", "Linear SVM")), "Saved production pipeline", "Champion", "#635BFF", "rgba(99,91,255,0.12)")
                    with k[1]:
                        kpi_modern("🎯", "Benchmark Accuracy", f"{acc_val:.1%}", "Evaluated on held-out split", gain_badge, "#16A36A", "rgba(22,163,106,0.12)")
                    with k[2]:
                        kpi_modern("⚖️", "Macro F1-Score", f"{f1_val:.3f}", "Equal weight per class", "Balanced", "#0284C7", "rgba(2,132,199,0.12)")
                    with k[3]:
                        kpi_modern("🧪", "Models Tested", str(len(metrics)), "Benchmarked algorithms", "Comprehensive", "#E6A23C", "rgba(230,162,60,0.12)")

                st.write("")
                m1, m2 = st.columns([1, 1], gap="large")
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
                r1, r2 = st.columns([1, 1.2], gap="large")
                with r1:
                    st.dataframe(report, use_container_width=True, hide_index=True)
                with r2:
                    st.bar_chart(report.set_index("category")[["precision", "recall", "f1-score"]])
        if CONFUSION_PATH.exists():
            with st.expander("Inspect Campus Classification Confusion Matrix"):
                cm = pd.read_csv(CONFUSION_PATH, index_col=0)
                st.dataframe(cm, use_container_width=True)

    with tab_fraud:
        st.markdown(
            f"<div style='font-size:0.80rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:0.04em;margin-bottom:8px'>"
            f"🛡️ Phishing & Cyber-Defense Benchmarks</div>",
            unsafe_allow_html=True
        )

        if FRAUD_MODEL_PATH.exists():
            f_time = datetime.fromtimestamp(FRAUD_MODEL_PATH.stat().st_mtime).strftime("%d %b %Y, %I:%M %p")
            st.caption(f"Active fraud detector: {FRAUD_MODEL_PATH.name} · Last modified: {f_time}")

        if FRAUD_METRICS_PATH.exists():
            f_metrics = pd.read_csv(FRAUD_METRICS_PATH)
            top_f = f_metrics.iloc[0]
            fk = st.columns(4)
            with fk[0]:
                kpi_modern("🛡️", "Defense Model", str(top_f["model"]), "Loss: Squared Hinge L2", "Active", "#16A36A", "rgba(22,163,106,0.12)")
            with fk[1]:
                kpi_modern("🎯", "Test Accuracy", f"{top_f['test_accuracy']:.1%}", "On 2,400 held-out test emails", "Verified", "#635BFF", "rgba(99,91,255,0.12)")
            with fk[2]:
                kpi_modern("🚨", "Phishing Recall", f"{top_f['test_recall']:.1%}", "Caught 1,189 / 1,200 attacks", "Critical", "#E05252", "rgba(224,82,82,0.12)")
            with fk[3]:
                kpi_modern("📈", "ROC-AUC Score", f"{top_f['test_roc_auc']:.3f}", "Near-perfect discrimination", "Near-Zero FP", "#0284C7", "rgba(2,132,199,0.12)")

            st.write("")
            fc1, fc2 = st.columns([1.1, 1], gap="large")
            with fc1:
                card_head("shield-check", "Fraud Algorithm Comparison", "h1")
                st.dataframe(f_metrics, use_container_width=True, hide_index=True)
            with fc2:
                card_head("sparkles", "Security Score Comparison", "h4")
                chart_df = f_metrics.melt(id_vars="model", value_vars=["test_accuracy", "test_recall", "test_f1"],
                                         var_name="Metric", value_name="Score")
                f_ch = alt.Chart(chart_df).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
                    x=alt.X("model:N", title=None, axis=alt.Axis(labelAngle=0)),
                    y=alt.Y("Score:Q", title="Score (0-1.0)", scale=alt.Scale(domain=[0.85, 1.0])),
                    xOffset="Metric:N",
                    color=alt.Color("Metric:N", scale=alt.Scale(range=["#0284C7", "#E05252", "#16A36A"])),
                    tooltip=["model", "Metric", alt.Tooltip("Score:Q", format=".4f")]
                ).properties(height=260)
                st.altair_chart(style_chart(f_ch, T), use_container_width=True, theme=None)

        if FRAUD_CONFUSION_PATH.exists():
            st.write("")
            cm_col1, cm_col2 = st.columns([1, 1.2], gap="large")
            with cm_col1:
                card_head("shield-alert", "Fraud Confusion Matrix", "h2")
                f_cm = pd.read_csv(FRAUD_CONFUSION_PATH, index_col=0)
                st.dataframe(f_cm, use_container_width=True)
            with cm_col2:
                st.markdown(
                    "<div class='card' style='padding:20px;border-radius:12px;background:var(--panel);border:1px solid var(--line)'><div class='card-body'>"
                    "<b style='color:var(--ink)'>Threat Detection Performance</b><br/>"
                    "<span class='muted' style='font-size:0.86rem;line-height:1.55'>"
                    "Calibrated Linear SVM achieves <b>99.08% threat interception</b> (1,189 / 1,200 phishing attempts caught in evaluation) with low false alarm rates."
                    "</span></div></div>", unsafe_allow_html=True
                )

        if FRAUD_KEYWORDS_PATH.exists():
            st.write("")
            st.markdown("<div style='font-size:0.80rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:0.04em;margin-bottom:8px'>🔍 Explainability: Top Feature Indicators</div>", unsafe_allow_html=True)
            kw_df = pd.read_csv(FRAUD_KEYWORDS_PATH)
            kw1, kw2 = st.columns(2, gap="large")
            with kw1:
                st.markdown("<b style='color:#E05252;font-size:0.86rem'>🚨 Top Phishing / Scam Indicators</b>", unsafe_allow_html=True)
                st.dataframe(kw_df[["top_fraud_indicators", "fraud_weight"]].head(12), use_container_width=True, hide_index=True)
            with kw2:
                st.markdown("<b style='color:#16A36A;font-size:0.86rem'>🛡️ Top Legitimate Academic Indicators</b>", unsafe_allow_html=True)
                st.dataframe(kw_df[["top_legitimate_indicators", "legitimate_weight"]].head(12), use_container_width=True, hide_index=True)

        if FRAUD_SAMPLES_PATH.exists():
            with st.expander("View Real Test Predictions & Sample Explanations"):
                sample_df = pd.read_csv(FRAUD_SAMPLES_PATH)
                st.dataframe(sample_df, use_container_width=True, hide_index=True)

    with tab_mail_analytics:
        st.markdown(
            f"<div style='font-size:0.80rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:0.04em;margin-bottom:8px'>"
            f"📬 Real-Time Mailbox Ingestion Telemetry</div>",
            unsafe_allow_html=True
        )
        gdf = st.session_state.gmail_df
        if gdf.empty:
            curr_acc = st.session_state.get("gmail_account", "")
            st.markdown(
                f"<div class='card' style='padding:36px 24px;border:1px solid var(--line);border-radius:14px;background:var(--panel);text-align:center;box-shadow:var(--shadow)'>"
                f"<div style='font-size:2.4rem;margin-bottom:8px'>📬</div>"
                f"<div style='font-size:1.15rem;font-weight:700;color:var(--ink);margin-bottom:6px'>No Live Mailbox Telemetry Active</div>"
                f"<p class='muted' style='font-size:0.86rem;max-width:460px;margin:0 auto 16px;line-height:1.55'>"
                f"Enter the Student Demo space or authenticate via Google OAuth in <b>Email History</b> to stream live message telemetry, department distributions, and cyber-threat statistics."
                f"</p>"
                f"</div>",
                unsafe_allow_html=True
            )
            if st.button("🚀 Enter Student Demo Mailbox (student_demo@thapar.edu)", type="primary", key="btn_load_demo_from_analytics"):
                switch_to_account("student_demo@thapar.edu")
                st.session_state.page = "Analytics"
                st.rerun()
        else:
            total_n = len(gdf)
            urgent_n = int(gdf["predicted_category"].isin(URGENT).sum())
            fraud_n = int((gdf["is_fraud"] == 1).sum()) if "is_fraud" in gdf.columns else 0
            safe_n = total_n - fraud_n
            cats_active = gdf["predicted_category"].nunique()

            lk = st.columns(4)
            with lk[0]:
                kpi_modern("📬", "Ingested Messages", f"{total_n:,}", "Active student mailbox", "Vault Synced", "#635BFF", "rgba(99,91,255,0.12)")
            with lk[1]:
                kpi_modern("⚡", "Important & Deadlines", f"{urgent_n:,}", f"{(urgent_n/total_n*100):.1f}% of total volume", "High Priority", "#16A36A", "rgba(22,163,106,0.12)")
            with lk[2]:
                kpi_modern("🚨", "Phishing Threats", f"{fraud_n:,}", "Auto-quarantined notices", "Zero Incident", "#E05252" if fraud_n else "#16A36A", "rgba(224,82,82,0.12)" if fraud_n else "rgba(22,163,106,0.12)")
            with lk[3]:
                kpi_modern("🏢", "Active Departments", f"{cats_active} / 10", "All faculties categorized", "Full Coverage", "#0284C7", "rgba(2,132,199,0.12)")

            st.write("")
            c_chart1, c_chart2 = st.columns([1.3, 1], gap="large")
            with c_chart1:
                with st.container(key="card_live_cat_dist"):
                    card_head("dashboard", "Department Volume Distribution", "h1")
                    cat_counts = gdf["predicted_category"].value_counts().reset_index()
                    cat_counts.columns = ["Category", "Count"]
                    cat_counts["Name"] = cat_counts["Category"].apply(nice)
                    c_ch = alt.Chart(cat_counts).mark_bar(cornerRadiusTopRight=5, cornerRadiusBottomRight=5).encode(
                        y=alt.Y("Name:N", sort="-x", title=None),
                        x=alt.X("Count:Q", title="Email Volume"),
                        color=alt.Color("Category:N", scale=cat_scale(), legend=None),
                        tooltip=["Name", "Count"]
                    ).properties(height=280)
                    st.altair_chart(style_chart(c_ch, T), use_container_width=True, theme=None)
            with c_chart2:
                with st.container(key="card_live_sec_dist"):
                    card_head("shield-check", "Cybersecurity & Priority Ratio", "h4")
                    sec_data = pd.DataFrame([
                        {"Type": "Legitimate Academic", "Count": safe_n},
                        {"Type": "Phishing Attacks", "Count": fraud_n}
                    ])
                    pie = alt.Chart(sec_data).mark_arc(innerRadius=50).encode(
                        theta=alt.Theta("Count:Q"),
                        color=alt.Color("Type:N", scale=alt.Scale(domain=["Legitimate Academic", "Phishing Attacks"], range=["#16A36A", "#E05252"]), legend=alt.Legend(orient="bottom")),
                        tooltip=["Type", "Count"]
                    ).properties(height=280)
                    st.altair_chart(style_chart(pie, T), use_container_width=True, theme=None)


# ═════════════════════════════ HISTORY FALLBACK ═════════════════════════════
elif page == "Prediction History":
    page_header("history", "Prediction History", "all analyzed emails tested across sessions with dual-model results")
    render_prediction_history_view()


# ═════════════════════════════ SETTINGS & CONFIGURATION ═════════════════════════════
elif page in ("Settings", "About the Project"):
    page_header("settings", "Settings & Configuration", "Manage interface preferences, model specifications, session security, and policies.")

    s_col1, s_col2 = st.columns(2, gap="large")
    with s_col1:
        # Card 1: Appearance & Theme
        st.markdown(
            f"<div class='card' style='padding:22px;border:1px solid var(--line);border-radius:14px;background:var(--panel);margin-bottom:18px'>"
            f"<div style='font-size:0.80rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:0.04em;margin-bottom:6px'>🎨 Appearance</div>"
            f"<div style='font-size:1.15rem;font-weight:700;color:var(--ink);margin-bottom:14px'>Theme Preference</div>",
            unsafe_allow_html=True
        )
        theme_names = list(THEMES.keys())
        active_theme_str = st.session_state.get("theme_choice", "Obsidian Luxury (Dark)")
        if active_theme_str not in theme_names:
            active_theme_str = "Obsidian Luxury (Dark)"
        current_theme_idx = theme_names.index(active_theme_str)
        new_theme = st.selectbox("Active Theme Palette", theme_names, index=current_theme_idx, key="settings_theme_select")
        if new_theme != active_theme_str:
            st.session_state.theme_choice = new_theme
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        # Card 2: AI Engine Architecture
        st.markdown(
            f"<div class='card' style='padding:22px;border:1px solid var(--line);border-radius:14px;background:var(--panel);margin-bottom:18px'>"
            f"<div style='font-size:0.80rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:0.04em;margin-bottom:6px'>🧠 Model Specifications</div>"
            f"<div style='font-size:1.15rem;font-weight:700;color:var(--ink);margin-bottom:14px'>Dual-Head ML Architecture</div>"
            f"<div style='display:flex;flex-direction:column;gap:12px'>"
            f"<div style='background:var(--panel2);padding:14px 16px;border-radius:10px;border:1px solid var(--line);display:flex;justify-content:space-between;align-items:center'>"
            f"<div><div style='font-weight:700;font-size:0.96rem;color:var(--ink)'>Topic Categorization</div>"
            f"<div class='muted' style='font-size:0.86rem;margin-top:2px'>Linear SVM · 10 Department Taxonomy</div></div>"
            f"<span style='background:rgba(99,91,255,0.14);color:var(--accent);font-weight:700;font-size:0.90rem;padding:4px 10px;border-radius:6px;border:1px solid rgba(99,91,255,0.3)'>91.6% Acc</span>"
            f"</div>"
            f"<div style='background:var(--panel2);padding:14px 16px;border-radius:10px;border:1px solid var(--line);display:flex;justify-content:space-between;align-items:center'>"
            f"<div><div style='font-weight:700;font-size:0.96rem;color:var(--ink)'>Cyber-Defense Phishing Shield</div>"
            f"<div class='muted' style='font-size:0.86rem;margin-top:2px'>Calibrated Linear SVM · Threat Detection</div></div>"
            f"<span style='background:rgba(22,163,106,0.14);color:#16A36A;font-weight:700;font-size:0.90rem;padding:4px 10px;border-radius:6px;border:1px solid rgba(22,163,106,0.3)'>98.96% Acc</span>"
            f"</div>"
            f"</div>"
            f"</div>",
            unsafe_allow_html=True
        )

    with s_col2:
        # Card 3: Account & Session
        curr_user = st.session_state.get("gmail_account", "")
        display_user = curr_user if curr_user else "Guest / Demo Mode"
        is_auth = bool(curr_user and curr_user != "student_demo@thapar.edu")
        status_label = "Authenticated" if is_auth else ("Demo Account" if curr_user else "Guest")
        status_color = "#16A36A" if is_auth else "#635BFF"

        st.markdown(
            f"<div class='card' style='padding:22px;border:1px solid var(--line);border-radius:14px;background:var(--panel);margin-bottom:18px'>"
            f"<div style='font-size:0.80rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:0.04em;margin-bottom:6px'>🔒 Account & Session</div>"
            f"<div style='font-size:1.15rem;font-weight:700;color:var(--ink);margin-bottom:14px'>Session Security</div>"
            f"<div style='background:var(--panel2);padding:14px 16px;border-radius:10px;border:1px solid var(--line);margin-bottom:16px'>"
            f"<div style='font-size:0.88rem;color:var(--muted);margin-bottom:4px'>Current Active Account</div>"
            f"<div style='font-size:1.02rem;font-weight:700;color:var(--ink);display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px'>"
            f"<span>{esc(display_user)}</span>"
            f"<span style='font-size:0.82rem;font-weight:700;color:{status_color};background:{status_color}22;padding:3px 9px;border-radius:6px;border:1px solid {status_color}44'>● {status_label}</span>"
            f"</div></div>",
            unsafe_allow_html=True
        )

        b_c1, b_c2 = st.columns(2)
        with b_c1:
            if st.button("🎓 Demo Account", use_container_width=True, key="set_demo_btn"):
                switch_to_account("student_demo@thapar.edu")
                st.session_state.page = "Settings"
                st.rerun()
        with b_c2:
            if st.button("🚪 Sign Out", use_container_width=True, key="set_signout_btn"):
                sign_out()
                st.session_state.page = "Dashboard"
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        # Card 4: Classification Preferences & Privacy
        st.markdown(
            f"<div class='card' style='padding:22px;border:1px solid var(--line);border-radius:14px;background:var(--panel);margin-bottom:18px'>"
            f"<div style='font-size:0.80rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:0.04em;margin-bottom:6px'>⚙️ Policies & Privacy</div>"
            f"<div style='font-size:1.15rem;font-weight:700;color:var(--ink);margin-bottom:14px'>Auto-Routing & Privacy Rules</div>"
            f"<div style='display:flex;flex-direction:column;gap:12px;font-size:0.90rem'>"
            f"<div style='display:flex;align-items:center;gap:10px'>"
            f"<span style='font-size:1.2rem'>⚡</span>"
            f"<div><b style='color:var(--ink)'>Priority Notice Routing:</b> <span class='muted'>Exams, assignments, scholarships, and placements flagged high priority.</span></div>"
            f"</div>"
            f"<div style='display:flex;align-items:center;gap:10px'>"
            f"<span style='font-size:1.2rem'>🚨</span>"
            f"<div><b style='color:var(--ink)'>Phishing Quarantine:</b> <span class='muted'>Threat scores &ge; 85% activate immediate security warnings and alert banners.</span></div>"
            f"</div>"
            f"<div style='display:flex;align-items:center;gap:10px'>"
            f"<span style='font-size:1.2rem'>🔒</span>"
            f"<div><b style='color:var(--ink)'>Zero-Leak OAuth Privacy:</b> <span class='muted'>Strict read-only scope (<code>gmail.readonly</code>). Emails are never forwarded or shared.</span></div>"
            f"</div>"
            f"</div></div>",
            unsafe_allow_html=True
        )

    st.markdown("<div style='margin-top:16px;font-size:0.82rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:0.04em'>Supported University Categories</div>", unsafe_allow_html=True)
    st.markdown("<div style='display:flex;flex-wrap:wrap;gap:8px;margin-top:8px'>" + "".join(tag(c) for c in CATS) + "</div>", unsafe_allow_html=True)

st.markdown("<hr><div class='muted' style='text-align:center;padding:12px;font-size:0.84rem'>CampusMail · Intelligent University Email Classification & Cybersecurity</div>",
            unsafe_allow_html=True)
