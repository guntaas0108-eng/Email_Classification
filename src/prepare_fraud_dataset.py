"""
Prepare balanced, high-quality fraud & phishing detection dataset.
Combines:
1. Real campus emails from data/college_emails.csv (verified Legitimate)
2. University phishing advisories from curated university corpus (Fraudulent)
3. Large-scale benchmark phishing & safe emails from Hugging Face corpus
"""

from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
OUTPUT_FILE = DATA_DIR / "fraud_detection_dataset.csv"

HF_URL = "https://huggingface.co/datasets/sahith002/phishing-email-dataset/resolve/main/Phishing_Email.csv"
UNIV_URL = "https://raw.githubusercontent.com/sadat1971/Phishing_Email/master/Data/curated_set.csv"
COLLEGE_CSV = DATA_DIR / "college_emails.csv"


def clean_text(s):
    if not isinstance(s, str):
        return ""
    text = s.strip()
    # Normalize whitespace
    return " ".join(text.split())


def build_dataset():
    print("=" * 60)
    print("BUILDING FRAUD & PHISHING DETECTION DATASET")
    print("=" * 60)

    records = []

    # 1. Load College Emails (Legitimate)
    if COLLEGE_CSV.exists():
        print(f"Loading genuine college emails from {COLLEGE_CSV.name}...")
        college_df = pd.read_csv(COLLEGE_CSV)
        subjects = college_df["subject"].fillna("").astype(str)
        bodies = college_df["body"].fillna("").astype(str)
        full_text = (subjects + " " + bodies).apply(clean_text)
        valid_mask = full_text.str.len() >= 30
        valid_texts = full_text[valid_mask].drop_duplicates().tolist()
        print(f"  Found {len(valid_texts)} valid unique college emails.")

        # Take up to 4,500 real college emails as Legitimate
        for t in valid_texts[:4500]:
            records.append({
                "text": t,
                "label": 0,
                "label_name": "Legitimate",
                "source": "college_emails"
            })

    # 2. Load University Phishing Corpus
    print("Fetching university-specific phishing dataset...")
    try:
        univ_df = pd.read_csv(UNIV_URL)
        for _, row in univ_df.iterrows():
            txt = clean_text(str(row.get("text", "")))
            if len(txt) >= 20:
                is_p = int(row.get("is_phishing", 0))
                records.append({
                    "text": txt,
                    "label": is_p,
                    "label_name": "Fraudulent" if is_p == 1 else "Legitimate",
                    "source": "university_phishing_corpus"
                })
        print(f"  Loaded {len(univ_df)} rows from university corpus.")
    except Exception as exc:
        print(f"  Warning: could not fetch university corpus: {exc}")

    # 3. Load Hugging Face Phishing Dataset
    print("Fetching large-scale benchmark phishing dataset...")
    try:
        hf_df = pd.read_csv(HF_URL)
        hf_df = hf_df.dropna(subset=["Email Text", "Email Type"])
        hf_phishing = hf_df[hf_df["Email Type"].str.lower().str.contains("phish")]["Email Text"].apply(clean_text)
        hf_safe = hf_df[hf_df["Email Type"].str.lower().str.contains("safe")]["Email Text"].apply(clean_text)

        hf_phishing = hf_phishing[hf_phishing.str.len() >= 30].drop_duplicates()
        hf_safe = hf_safe[hf_safe.str.len() >= 30].drop_duplicates()

        print(f"  Benchmark contains {len(hf_phishing)} phishing and {len(hf_safe)} safe emails.")

        # Target: roughly 6,000 Fraudulent and 6,000 Legitimate
        current_fraud = sum(1 for r in records if r["label"] == 1)
        needed_fraud = max(0, 6000 - current_fraud)
        for t in hf_phishing.sample(min(needed_fraud, len(hf_phishing)), random_state=42):
            records.append({
                "text": t,
                "label": 1,
                "label_name": "Fraudulent",
                "source": "phishing_benchmark"
            })

        current_legit = sum(1 for r in records if r["label"] == 0)
        needed_legit = max(0, 6000 - current_legit)
        for t in hf_safe.sample(min(needed_legit, len(hf_safe)), random_state=42):
            records.append({
                "text": t,
                "label": 0,
                "label_name": "Legitimate",
                "source": "safe_benchmark"
            })
    except Exception as exc:
        print(f"  Warning: could not fetch benchmark: {exc}")

    df = pd.DataFrame(records)
    df = df.drop_duplicates(subset=["text"]).reset_index(drop=True)

    # Balance classes evenly
    fraud_df = df[df["label"] == 1]
    legit_df = df[df["label"] == 0]
    min_count = min(len(fraud_df), len(legit_df))
    balanced_df = pd.concat([
        fraud_df.sample(min_count, random_state=42),
        legit_df.sample(min_count, random_state=42)
    ]).sample(frac=1.0, random_state=42).reset_index(drop=True)

    balanced_df.to_csv(OUTPUT_FILE, index=False)
    print("\nDataset generation complete!")
    print(f"Saved to: {OUTPUT_FILE}")
    print(f"Total samples: {len(balanced_df)}")
    print(balanced_df["label_name"].value_counts().to_string())
    print("\nBreakdown by source:")
    print(balanced_df.groupby(["source", "label_name"]).size().to_string())


if __name__ == "__main__":
    build_dataset()
