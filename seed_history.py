import joblib
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parent
m_cat = joblib.load(BASE / "models" / "best_email_classifier.joblib")
m_fraud = joblib.load(BASE / "models" / "best_fraud_detector.joblib")

samples = [
    {
        "time": (datetime.now() - timedelta(minutes=45)).strftime("%Y-%m-%d %H:%M:%S"),
        "subject": "Urgent: Selected for Amazon Summer Internship 2026 - Confirm Slot",
        "body": "Congratulations! You have been shortlisted for Amazon Summer Internship stipend Rs. 85,000/month. To secure your slot, you must pay mandatory security deposit of Rs. 1,500 immediately at http://amazon-careers-verify.info/pay before 5 PM today."
    },
    {
        "time": (datetime.now() - timedelta(minutes=38)).strftime("%Y-%m-%d %H:%M:%S"),
        "subject": "URGENT: Your Campus WebKiosk / Email Password Expires in 24 Hours",
        "body": "Dear Student, your student portal account will be terminated today due to system maintenance. Click here immediately to verify your credentials: http://university-login-update.com/auth. Failure to update will lock your student profile."
    },
    {
        "time": (datetime.now() - timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S"),
        "subject": "End Semester Examination Schedule - Even Semester 2026",
        "body": "Dear Students, The tentative datesheet for the upcoming End Semester Examinations May 2026 has been uploaded on the university portal. Practical evaluations begin from 12th May. In case of any clash, notify the Academic Section before Friday."
    },
    {
        "time": (datetime.now() - timedelta(minutes=22)).strftime("%Y-%m-%d %H:%M:%S"),
        "subject": "CodeCraft 2026: 36-Hour National Student Hackathon",
        "body": "Dear Coders, The Department of Computer Science & Engineering in association with ACM Student Chapter invites teams for CodeCraft 2026. Cash prizes of Rs. 1,50,000 to be won. Form teams of 2 to 4 members and register on our official portal."
    },
    {
        "time": (datetime.now() - timedelta(minutes=16)).strftime("%Y-%m-%d %H:%M:%S"),
        "subject": "Hostel H-Wing Hot Water Geyser Maintenance Notice",
        "body": "Dear Residents of Hostel H, Please note that solar and electrical geysers will undergo routine safety inspection and maintenance on Thursday from 9 AM to 1 PM. Hot water supply will remain suspended during these hours. Inconvenience is regretted."
    },
    {
        "time": (datetime.now() - timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S"),
        "subject": "Distinguished Lecture on Generative Foundation Models by Dr. Rajesh Sharma",
        "body": "You are cordially invited to attend a guest lecture on Generative Foundation Models and Agentic AI by Dr. Rajesh Sharma, Lead Research Scientist, on Friday at 3:00 PM in the Main Auditorium. Tea and high snacks will follow."
    },
    {
        "time": (datetime.now() - timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S"),
        "subject": "Campus Placement Drive: Microsoft Software Engineer FTE 2026",
        "body": "Centre for Industrial Liaison & Placement is pleased to announce that Microsoft is conducting an on-campus placement drive for final year B.Tech/M.Tech students. Eligible branches: CSE/ECE/COE. CTC offered: 44.5 LPA. Apply via placement portal by Sunday."
    },
    {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "subject": "URGENT: Win Rs. 50,000 Cash - Student Survey Reward Claim",
        "body": "You have won our annual student lucky draw! Claim your Rs. 50,000 direct bank transfer immediately. Enter your bank account details and debit card PIN on our prize portal http://student-cash-claim.com to receive the funds."
    }
]

records = []
for s in samples:
    text = f"{s['subject']} {s['body']}"
    cat = str(m_cat.predict([text])[0])
    is_f = int(m_fraud.predict([text])[0])
    prob = m_fraud.predict_proba([text])[0][1] * 100.0
    records.append({
        "Timestamp": s["time"],
        "Subject": s["subject"],
        "Email Body": s["body"],
        "Predicted Category": cat,
        "Fraud Status": "Fraudulent" if is_f == 1 else "Legitimate",
        "Threat Probability": f"{prob:.1f}%"
    })

hist_df = pd.DataFrame(records)
out_path = BASE / "outputs" / "prediction_history.csv"
hist_df.to_csv(out_path, index=False)
print(f"Successfully saved {len(hist_df)} records to {out_path}")
