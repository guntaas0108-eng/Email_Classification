import re
import pandas as pd

df = pd.read_csv('Email_Classification/data/college_emails.csv')
print("Total rows in college_emails.csv:", len(df))

RULES = {
    'hackathons': [
        r'\bhackathon(s)?\b', r'\bsmart india hackathon\b', r'\bsih\s*202\d\b',
        r'\bhackfest\b', r'\bdevpost\b', r'\bdevfolio\b', r'\bcodefest\b',
        r'\bideathon(s)?\b', r'\bmakeathon(s)?\b', r'\bhackbyte\b', r'\bhack-a-thon\b',
        r'\bhack4acause\b', r'\btoycathon\b'
    ],
    'exams': [
        r'\bdate\s*sheet\b', r'\bend\s*semester\s*exam(ination)?(s)?\b',
        r'\bmid\s*semester\s*exam(ination)?(s)?\b', r'\badmit\s*card(s)?\b',
        r'\bexamination\s*schedule\b', r'\bsupplementary\s*exam\b',
        r'\bmake-up\s*exam\b', r'\bexamination\s*branch\b', r'\best\s*exam\b',
        r'\bmst\s*exam\b', r'\bseating\s*plan\b', r'\broll\s*list\b'
    ],
    'hostel_notices': [
        r'\bhostel(s)?\b', r'\bfretbox\b', r'\broom\s*key(s)?\b', r'\bac\s*remote(s)?\b',
        r'\bhostel\s*allotment\b', r'\bhostel\s*accommodation\b', r'\bhostel\s*fee(s)?\b',
        r'\broom\s*booking\b', r'\bmess\s*fee(s)?\b', r'\broom\s*allocation\b',
        r'\bhostel\s*warden\b', r'\broom\s*vacating\b'
    ],
    'seminars': [
        r'\bwebinar(s)?\b', r'\bguest\s*lecture(s)?\b', r'\bkeynote\s*speaker\b',
        r'\bresearch\s*talk(s)?\b', r'\bcolloquium\b', r'\bsymposium\b',
        r'\bpanel\s*discussion\b', r'\bdistinguished\s*lecture\b',
        r'\bseminar\s*on\b', r'\binvited\s*talk\b', r'\btechnical\s*session\b'
    ],
    'sports': [
        r'\bbadminton\b', r'\bcricket\b', r'\bfootball\b', r'\bbasketball\b',
        r'\bathletics\b', r'\bsports\s*trial(s)?\b', r'\btable\s*tennis\b',
        r'\bvolleyball\b', r'\bchess\s*tournament\b', r'\bsports\s*meet\b',
        r'\bthaparlympics\b', r'\besports\s*showdown\b', r'\bgymnasium\b',
        r'\bswimming\s*pool\b', r'\blawn\s*tennis\b', r'\binter[- ]hostel\s*sports\b'
    ],
    'scholarships': [
        r'\bscholarship(s)?\b', r'\bfee\s*concession(s)?\b', r'\bmerit\s*scholarship(s)?\b',
        r'\bfinancial\s*assistance\b', r'\bfellowship\s*programme\b', r'\bfreeship\b',
        r'\balumni\s*scholarship\b', r'\bmerit-cum-means\b', r'\bpost\s*matric\s*scholarship\b',
        r'\byoung\s*researcher\s*fellowship\b', r'\btiet\s*scholarship\b'
    ],
    'assignments': [
        r'\bassignment\s*(submission|feedback|due|deadline)\b',
        r'\blab\s*submission\b', r'\bpractical\s*file\b',
        r'\bturnitin\s*submission\b', r'\btiet\s*lms\b.*\bassignment\b',
        r'\bcoursework\s*submission\b', r'\blms\s*assignment\b'
    ],
    'events': [
        r'\bsaturnalia\b', r'\bmudranite\b', r'\brubaru\b', r'\bcultural\s*fest\b',
        r'\bstar\s*night\b', r'\bopen\s*mic\b', r'\baudition(s)?\b',
        r'\bflash\s*mob\b', r'\bdance\s*competition\b', r'\bmusic\s*society\b',
        r'\be-summit\b', r'\bfreshers\s*party\b', r'\bfarewell\s*party\b'
    ],
    'placements': [
        r'\bplacement\s*drive\b', r'\bcampus\s*drive\b', r'\bshortlisted\s*for\s*interview\b',
        r'\bon-campus\s*recruitment\b', r'\bctc\s*:\s*\b', r'\bjob\s*description\b',
        r'\bsummer\s*internship\s*drive\b', r'\bppo\s*offer\b', r'\bplacement\s*cell\b',
        r'\bcentre\s*for\s*training\s*and\s*development\b', r'\bt&p\s*cell\b',
        r'\bhiring\s*drive\b', r'\brecruitment\s*process\b'
    ],
    'general_announcements': [
        r'\bholiday\s*notice\b', r'\boffice\s*order\b', r'\bcircular\b',
        r'\bcampus\s*maintenance\b', r'\btransport\s*schedule\b', r'\bbus\s*schedule\b',
        r'\bhealth\s*centre\b', r'\bdispensary\b', r'\bregistrar\s*office\b',
        r'\bdirector\s*office\b', r'\bid\s*card(s)?\b', r'\bfee\s*payment\s*notice\b'
    ]
}

counts = {}
for cat, patterns in RULES.items():
    combined_pat = '|'.join(patterns)
    # Check subject primarily
    subj_matches = df['subject'].fillna('').str.contains(combined_pat, case=False, regex=True)
    body_matches = df['body'].fillna('').str.contains(combined_pat, case=False, regex=True)
    counts[cat] = {'subject_matches': subj_matches.sum(), 'total_matches': (subj_matches | body_matches).sum()}

print(pd.DataFrame(counts).T)
