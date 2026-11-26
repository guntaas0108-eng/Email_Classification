import re
import warnings
import pandas as pd
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import VotingClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.metrics import accuracy_score, f1_score, classification_report
warnings.filterwarnings('ignore')

from test_expanded_real import df_all, y, cv

text = (df_all['subject'] + ' ' + df_all['subject'] + ' ' + df_all['subject'] + ' ' + df_all['body']).str.strip().tolist()

union = FeatureUnion([
    ('word', TfidfVectorizer(ngram_range=(1, 2), max_features=35000, sublinear_tf=True, strip_accents='unicode')),
    ('char', TfidfVectorizer(analyzer='char_wb', ngram_range=(3, 5), max_features=25000, sublinear_tf=True))
])

pipe = Pipeline([
    ('feats', union),
    ('clf', LinearSVC(C=1.2, class_weight='balanced', random_state=42))
])

preds = cross_val_predict(pipe, text, y, cv=cv)
acc = accuracy_score(y, preds)
f1 = f1_score(y, preds, average='macro')

print("\n=======================================================")
print(f"FeatureUnion + Expanded Real Emails CV Accuracy: {acc * 100:.2f}% | Macro F1: {f1:.4f}")
print("=======================================================")
print(classification_report(y, preds, digits=3))
