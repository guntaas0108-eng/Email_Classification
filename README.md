# 🎓 CampusMail — Intelligent University Email Classification & Dual-Head Cybersecurity Phishing Shield

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://clouds-measurement-advantage-sight.trycloudflare.com)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Scikit-Learn](https://img.shields.io/badge/scikit--learn-1.3+-orange.svg)](https://scikit-learn.org/)
[![Cloudflare Tunnel](https://img.shields.io/badge/cloudflare-tunnel--live-F38020.svg?logo=cloudflare)](https://clouds-measurement-advantage-sight.trycloudflare.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🌐 Live Web Application & Classroom Demo

> **Live Public URL:** **[https://clouds-measurement-advantage-sight.trycloudflare.com](https://clouds-measurement-advantage-sight.trycloudflare.com)**  
> **Local Presenter URL:** `http://localhost:8501`  
> **Status:** 🟢 **Active & Serving Online**

### 📱 How Anyone in Class / Teacher Can Test Live:
1. Open the public link: **[https://clouds-measurement-advantage-sight.trycloudflare.com](https://clouds-measurement-advantage-sight.trycloudflare.com)** on any phone, tablet, or laptop.
2. The portal loads in **Guest Mode** with zero data leakage.
3. Sign in using either:
   - **`🎓 Student Demo Space`** (Instant 1-click demo with 103 emails across all 10 departments + 3 phishing alerts)
   - **`⚡ Presenter (gsingh15)`** (1-click presenter account with real verified campus notices)
   - **Any Student Email** (e.g. `rollnumber@thapar.edu` + any password — creates an encrypted private vault)
4. Experience all features: browse 10 campus folders, inspect phishing alerts, view timeline charts, test custom emails in **Try a Prediction**, and inspect **Model Lab** metrics.
5. Click **`🚪 Sign Out`**: all personal emails, folder counts, and history are **immediately wiped with zero data remaining on screen**.

---

## ⚡ Always-On Architecture & Real-Time Live Sync

```
  ┌────────────────────────────────────────────────────────────────────────┐
  │                           DEVELOPER LAPTOP                             │
  │                                                                        │
  │   Code Updates (app.py) ──► Streamlit Engine (--server.runOnSave true)  │
  │                                        │                               │
  │                                        ▼                               │
  │                           Local Port: localhost:8501                   │
  └────────────────────────────────────────┬───────────────────────────────┘
                                           │
                                           ▼ (Encrypted QUIC / HTTP/2)
  ┌────────────────────────────────────────────────────────────────────────┐
  │                 CLOUDFLARED TUNNEL (Global Edge Daemons)               │
  │                                        │                               │
  │                                        ▼                               │
  │     https://clouds-measurement-advantage-sight.trycloudflare.com               │
  └────────────────────────────────────────┬───────────────────────────────┘
                                           │
                    ┌──────────────────────┴──────────────────────┐
                    ▼                                             ▼
          👨‍🏫 Professor / Teacher                          📱 Classmates / Students
        (Evaluates Live ML Metrics)                   (Tests Phishing & Campus Folders)
```

### How Real-Time Changes Work:
* **Instant Hot-Reload:** The server runs with Streamlit's live file watcher. Any edits made to `app.py`, design CSS, or ML pipeline parameters are **instantly updated on the live URL in real-time** without restarting or disconnecting users.
* **1-Click Presentation Launcher:** Included [`run_presentation_demo.bat`](run_presentation_demo.bat) launches both the background Streamlit AI server and Cloudflare Edge Tunnel in a single click.
* **Streamlit Community Cloud 24/7 Option:** This repository is pre-configured with `requirements.txt` and `.streamlit/config.toml` so it can also be linked to [Streamlit Community Cloud](https://share.streamlit.io/) for 24/7 cloud hosting directly from this GitHub repository.

---

## 🧠 Dual-Head Machine Learning Architecture

Unlike naive classification systems that force security and campus topics into a single list, **CampusMail utilizes a decoupled dual-head supervised ML architecture**:

```
                                  Incoming Email Notice
                               (Subject, Body, Sender)
                                          │
                                          ▼
                         [ Text Cleaning & Normalization ]
                                          │
                    ┌─────────────────────┴─────────────────────┐
                    ▼                                           ▼
          TF-IDF Sublinear N-Grams                    TF-IDF Sublinear N-Grams
            (Campus Vocabulary)                         (Cybersecurity Tokens)
                    │                                           │
                    ▼                                           ▼
             [ Head 1: Campus ]                         [ Head 2: Security ]
            Linear SVM Pipeline                       Calibrated Linear SVM
                    │                                           │
                    ▼                                           ▼
           10 University Folders                       Phishing Threat Verdict
      (Exams, Placements, Hackathons,             (Legitimate vs. Phishing Scam)
       Seminars, Sports, Hostel, etc.)             98.96% Accuracy · 99.08% Recall
                    │                                           │
                    └─────────────────────┬─────────────────────┘
                                          ▼
                       [ Unified Intelligent Inbox View ]
```

### Why Decoupled Dual-Head?
> **Mathematical Justification:** Topic and Trustworthiness are mathematically orthogonal dimensions. A single multi-class model forces mutual exclusivity ($P(\text{Placements}) + P(\text{Fraud}) \le 1$), meaning an email can only be classified as a Placement notice OR Fraud. In reality, modern phishing relies on spear-phishing that impersonates placement drives or fee payments. An email can be simultaneously about placements and malicious.

---

## 📂 10 Campus Categories Supported

| Dot | Category | Description |
| :---: | :--- | :--- |
| 🟣 | **Hackathons** | Buildathons, coding contests, and technical innovation challenges |
| 🔴 | **Exams** | Examination datesheets, seating arrangements, and hall ticket notices |
| 🟤 | **Hostel Notices** | Hostel mess schedules, room allotments, and maintenance circulars |
| 🔵 | **Seminars** | Guest lectures, research workshops, and academic keynote sessions |
| 🟢 | **Sports** | Inter-college tournaments, sports trials, and athletics announcements |
| 🟡 | **Scholarships** | Merit aid, tuition waivers, government grants, and fellowship deadlines |
| 🟠 | **Assignments** | Coursework submissions, lab evaluations, and project deadlines |
| 💗 | **Events** | Cultural fests, student club activities, and campus orientation |
| ⚪ | **General Announcements** | Broad administrative circulars and institute-wide updates |
| 🩵 | **Placements** | Corporate recruitment drives, internship openings, and interviews |

---

## 🛡️ Zero-Data-Leakage Privacy & Multi-Tenant Isolation

1. **Multi-Tenant User Isolation:** Each visitor's classified emails and prediction histories are strictly sequestered in `outputs/users/<clean_email>/`. Classmates on their phones cannot see the presenter's or other students' data.
2. **PBKDF2-SHA256 Vault Encryption:** Vault passwords are salted and hashed with 100,000 rounds. No plaintext credentials are ever stored.
3. **Brave & Google Chrome Password Manager Ready:** Integrates with browser password management APIs so students can save their password for seamless 1-click unlock.
4. **Clean Sign-Out Purge:** Clicking `🚪 Sign Out` purges all session state, resets the folder view, and locks the screen with **zero data remaining**.
5. **Read-Only Gmail API Scope:** Strictly restricted to `https://www.googleapis.com/auth/gmail.readonly`. The system never alters, deletes, or forwards emails.

---

## 📊 Model Evaluation & Benchmarks

### 1. Campus Topic Classifier (10 Classes)
Evaluated using Stratified 5-Fold Cross-Validation on verified university notices:

| Model | Accuracy | Macro Precision | Macro Recall | Macro F1 |
| :--- | :---: | :---: | :---: | :---: |
| **Linear SVM (Selected)** | **91.8%** | **92.4%** | **91.6%** | **91.9%** |
| Logistic Regression | 89.2% | 89.8% | 88.7% | 89.1% |
| Multinomial Naive Bayes | 84.5% | 85.1% | 83.9% | 84.3% |
| XGBoost | 88.1% | 88.5% | 87.6% | 88.0% |
| Random Forest | 86.4% | 87.0% | 85.8% | 86.2% |

### 2. Fraud & Phishing Detection Engine (Binary)
Trained and evaluated on **11,998 balanced emails** (authentic campus notices vs. real-world phishing corpus):

| Metric | Calibrated Linear SVM | Logistic Regression | Multinomial NB |
| :--- | :---: | :---: | :---: |
| **Accuracy** | **98.96%** | 98.42% | 96.15% |
| **Recall (Phishing Caught)** | **99.08%** (1,189 / 1,200) | 98.25% | 95.83% |
| **Precision** | **98.83%** | 98.58% | 96.47% |
| **F1-Score** | **0.9896** | 0.9841 | 0.9615 |
| **ROC-AUC** | **0.9984** | 0.9972 | 0.9910 |

---

## 📑 Full Academic Project Report

For the in-depth theoretical framework, mathematical formulation, error analysis, and defense Q&A guide prepared for professors, see:  
👉 **[Read the Full Project Report (PROJECT_REPORT.md)](PROJECT_REPORT.md)**

---

## 🛠️ Project Structure

```text
Email_Classification/
├── app.py                             # Main Streamlit Application (Obsidian Luxury UI)
├── PROJECT_REPORT.md                  # Comprehensive Academic Project Report & Defense Guide
├── README.md                          # Project Documentation & Live Demo Guide
├── requirements.txt                   # Production Dependencies
├── run_presentation_demo.bat          # 1-Click Server & Cloudflare Tunnel Launcher
│
├── data/
│   └── demo_student_mailbox.csv       # Pre-classified 103 emails (10 categories + 3 phishing alerts)
│
├── models/
│   ├── best_email_classifier.joblib   # Serialized Linear SVM Campus Classifier Pipeline
│   ├── best_fraud_detector.joblib     # Serialized Calibrated Linear SVM Phishing Pipeline
│   └── email_categories.txt           # 10 Supported Department Categories
│
├── outputs/
│   ├── model_comparison.csv           # Multi-Model Benchmark Metrics
│   ├── best_model_classification_report.csv
│   ├── best_model_confusion_matrix.csv
│   ├── fraud_model_comparison.csv
│   ├── fraud_best_model_classification_report.csv
│   ├── fraud_best_model_confusion_matrix.csv
│   ├── fraud_top_keywords.csv
│   └── fraud_sample_predictions.csv
│
├── src/
│   ├── prepare_data.py                # Dataset Cleaning & Verification
│   ├── prepare_fraud_dataset.py       # Balanced 11,998 Email Corpus Preparation
│   └── auto_categorize.py
│
├── train_campusmail_models.py         # Multi-Class Classifier Training Pipeline
└── train_fraud_detector.py            # Binary Phishing Detector Training Pipeline
```

---

## ⚙️ Installation & Local Setup

### 1. Clone the Repository
```bash
git clone https://github.com/guntaas0108-eng/Email_Classification.git
cd Email_Classification
```

### 2. Set Up Virtual Environment
```bash
python -m venv .venv
# On Windows:
.\.venv\Scripts\activate
# On Linux / macOS:
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Application
```bash
streamlit run app.py
```
Open `http://localhost:8501` in your browser.

---

## 👨‍💻 Author & Academic Credits
* **Student Name:** Guntaas Singh
* **Institute:** Thapar Institute of Engineering & Technology (TIET), Patiala
* **Repository:** [https://github.com/guntaas0108-eng/Email_Classification](https://github.com/guntaas0108-eng/Email_Classification)
* **Live System:** [https://clouds-measurement-advantage-sight.trycloudflare.com](https://clouds-measurement-advantage-sight.trycloudflare.com)
