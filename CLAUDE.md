# CLAUDE.md — UniMail / CampusMail Project Guide

## 📌 Project Overview
**UniMail (CampusMail)** is an intelligent email classification and security analysis dashboard designed for university students. It runs on a **Dual-Head Supervised Machine Learning Architecture**:
1. **Campus Categorization Module (10 Classes):** Classifies emails into `Exams`, `Placements`, `Scholarships`, `Hackathons`, `Assignments`, `Hostel Notices`, `Seminars`, `Sports`, `Events`, and `General Announcements`.
2. **Fraud & Phishing Detection Engine (Binary):** Flags scam emails, fake placement offers, fee fraud, and credential harvesting (`Legitimate` vs `Fraudulent`).

The application features an interactive **Streamlit** frontend and connects with **Gmail API** via read-only Google OAuth 2.0.

---

## 🚀 Environment & Running Commands

Always use the local Python 3.13 virtual environment:
```powershell
# Navigate to project
cd "c:\Users\gunta\Desktop\Email_Classification"

# Activate virtual environment
.\.venv\Scripts\activate

# Run the Streamlit web application
streamlit run app.py

# Retrain the Fraud & Phishing Detection model
python train_fraud_detector.py

# Retrain the Campus Category models
python train_campusmail_models.py
```

---

## 📁 Repository Structure
```text
Email_Classification/
├── .venv/                      # Python 3.13 virtual environment
├── data/
│   ├── college_emails.csv      # 5,200+ authentic university notices
│   └── fraud_detection_dataset.csv # 12,000 balanced emails (Legit vs Phish)
├── models/
│   ├── best_email_classifier.joblib   # 10-class campus pipeline
│   ├── best_fraud_detector.joblib     # Calibrated Linear SVM fraud pipeline
│   └── email_categories.txt           # List of 10 campus categories
├── outputs/
│   ├── fraud_model_comparison.csv     # Benchmarks across SVM, LR, NB, RF
│   ├── fraud_best_model_confusion_matrix.csv
│   └── fraud_top_keywords.csv         # Feature importances
├── app.py                      # Main Streamlit web application
├── credentials.json            # Google OAuth client secrets (DO NOT COMMIT)
├── token.json                  # Cached Google OAuth token (DO NOT COMMIT)
└── requirements.txt            # Python dependencies
```

---

## 🎨 UI/UX Redesign Goals & Guidelines

When redesigning the user interface in `app.py`:
1. **Design Aesthetic:**
   - Modern, premium, clean SaaS interface (inspired by Linear, Vercel, and Claude).
   - Polished typography using Inter / SF Pro fonts with high contrast ratios.
   - Elegant dark/light mode with CSS variables (`--bg`, `--panel`, `--line`, `--ink`, `--accent`).
   - Smooth card elevations, soft borders (`1px solid rgba(...)`), and rounded corners (`border-radius: 12px`).
2. **Dual-Model Representation:**
   - Keep Topic and Security status visually distinct:
     - Topic: Category pill tags (`#a78bfa` Hackathons, `#f87171` Exams, `#22d3ee` Placements, etc.).
     - Security: Trust badges (`🛡️ Legitimate` in emerald green vs `🚨 Phishing Alert` in bright crimson).
3. **Key Pages:**
   - **Dashboard:** Modern KPI cards, category distribution chart, priority breakdown, and security alert banner.
   - **Inbox:** Split-pane email client (collapsible email list on left, rich reading pane on right with security headers).
   - **Try a Prediction:** Interactive demo playground with 1-click test buttons (`Job Scam`, `Phishing`, `Exam Notice`, `Hackathon`).
   - **Model Lab:** Interactive tabbed benchmark viewer showing evaluation tables, confusion matrices, and explainability keywords.
   - **Prediction History & About:** Session logging and transparent project documentation.

---

## ⚠️ Critical Development Rules
- **Do Not Break Saved Models:** Both `best_email_classifier.joblib` and `best_fraud_detector.joblib` are pre-trained scikit-learn `Pipeline` objects. Load them via `joblib.load()`.
- **Preserve OAuth Scope:** The Gmail integration requires read-only permissions (`https://www.googleapis.com/auth/gmail.readonly`). Never modify or request write scopes.
- **Always Keep Decoupled Inference:** Predictions must remain independent:
  `predict_emails(rows, model, fraud_model)` outputs both `predicted_category` and `fraud_status`.
