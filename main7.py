import os
import sys
import sqlite3
import pandas as pd
import datetime
import time

# --- AI & MACHINE LEARNING LIBRARIES ---
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.pipeline import Pipeline

# --- TERMINAL FORMATTING CODES ---
class Style:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'

# --- DATABASE INITIALIZATION ---
def init_db():
    conn = sqlite3.connect("server.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS emails (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender TEXT,
                    recipient TEXT,
                    subject TEXT,
                    body TEXT,
                    timestamp TEXT,
                    is_spam INTEGER
                )''')
    conn.commit()
    conn.close()

# --- UTILITY FUNCTIONS ---
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(title):
    clear_screen()
    print(f"{Style.BLUE}{'-' * 80}{Style.RESET}")
    print(f"{Style.BOLD}{title.upper()}{Style.RESET}")
    print(f"{Style.BLUE}{'-' * 80}{Style.RESET}\n")

# --- MODEL TRAINING ENGINE ---
def train_model():
    print(f"{Style.BOLD}System Initialization{Style.RESET}")
    print(" > Checking integrity of training data (emails.csv)...")
    
    try:
        if not os.path.exists('emails.csv'):
            print(f"{Style.FAIL} [ERROR] File 'emails.csv' not found.{Style.RESET}")
            print("   Please ensure the training dataset is present in the root directory.")
            input("\nPress Enter to terminate...")
            sys.exit()

        df = pd.read_csv('emails.csv')
        
        if 'text' not in df.columns or 'spam' not in df.columns:
            print(f"{Style.FAIL} [ERROR] CSV schema validation failed.{Style.RESET}")
            print("   Required columns: 'text', 'spam'.")
            sys.exit()

        print(" > Vectorizing text data (TF-IDF)...")
        print(" > Training Support Vector Machine (LinearSVC)...")

        X = df['text'].astype(str)
        y = df['spam']

        # SVM Pipeline Configuration
        model = Pipeline([
            ('vectorizer', TfidfVectorizer(stop_words='english', ngram_range=(1, 2))),
            ('classifier', LinearSVC(class_weight='balanced', dual='auto'))
        ])
        
        model.fit(X, y)
        accuracy = model.score(X, y)
        
        print(f"{Style.GREEN} [OK] Model training complete.{Style.RESET}")
        print(f"   - Algorithm: SVM (LinearSVC)")
        print(f"   - Dataset Size: {len(df)} records")
        print(f"   - Accuracy Score: {accuracy:.4f}")
        time.sleep(1.5)
        return model

    except Exception as e:
        print(f"{Style.FAIL} [FATAL] An exception occurred during initialization: {e}{Style.RESET}")
        sys.exit()

# --- SIMULATOR FUNCTIONS ---
def send_email(model):
    print_header("Compose Message")
    
    print(f"{Style.BOLD}Message Headers{Style.RESET}")
    sender = input(" From    : ").strip() or "unknown@sender.net"
    recipient = input(" To      : ").strip() or "user@internal.loc"
    subject = input(" Subject : ").strip()
    
    print(f"\n{Style.BOLD}Message Body (Press Enter twice to finalize){Style.RESET}")
    lines = []
    while True:
        line = input()
        if line:
            lines.append(line)
        else:
            break
    body = "\n".join(lines)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not body:
        print(f"\n{Style.WARNING} [!] Operation aborted: Message body cannot be empty.{Style.RESET}")
        time.sleep(1.5)
        return

    # AI Prediction Logic
    print(f"\n{Style.BLUE} > Analyzing content vector...{Style.RESET}")
    time.sleep(0.5)
    
    full_content = f"{subject} {body}"
    is_spam = int(model.predict([full_content])[0])

    # Database Transaction
    conn = sqlite3.connect("server.db")
    c = conn.cursor()
    c.execute("INSERT INTO emails (sender, recipient, subject, body, timestamp, is_spam) VALUES (?, ?, ?, ?, ?, ?)",
              (sender, recipient, subject, body, timestamp, is_spam))
    conn.commit()
    conn.close()

    # Result Output
    if is_spam == 1:
        print(f"{Style.FAIL} [BLOCK] SPAM DETECTED{Style.RESET}")
        print(f"   Classification: High Probability Spam")
        print(f"   Action: Routed to Quarantine Folder")
    else:
        print(f"{Style.GREEN} [PASS] MESSAGE VERIFIED{Style.RESET}")
        print(f"   Classification: Legitimate (Ham)")
        print(f"   Action: Delivered to Inbox")
    
    input(f"\n{Style.BOLD}[Press Enter to continue]{Style.RESET}")

def view_mailbox(box_type):
    # box_type: 0 = Inbox, 1 = Spam
    folder_name = "INBOX DIRECTORY" if box_type == 0 else "QUARANTINE (SPAM) DIRECTORY"
    row_color = Style.RESET if box_type == 0 else Style.FAIL
    
    while True:
        print_header(folder_name)
        
        conn = sqlite3.connect("server.db")
        c = conn.cursor()
        c.execute("SELECT id, sender, subject, timestamp FROM emails WHERE is_spam=? ORDER BY id DESC", (box_type,))
        emails = c.fetchall()
        conn.close()

        # Table Header
        print(f"{Style.UNDERLINE}{'ID':<5} | {'SENDER':<25} | {'SUBJECT':<30} | {'TIMESTAMP':<20}{Style.RESET}")

        if not emails:
            print(f"\n   (No records found in this directory)")
        
        for email in emails:
            eid, sender, subject, time_sent = email
            sub_display = (subject[:27] + '..') if len(subject) > 27 else subject
            print(f"{eid:<5} | {sender:<25} | {row_color}{sub_display:<30}{Style.RESET} | {time_sent:<20}")

        print(f"\n{Style.BLUE}{'-' * 80}{Style.RESET}")
        print("Commands: [ID] to read message  |  [0] Return to Dashboard")
        
        choice = input(f"\nSelect >> ").strip()

        if choice == '0':
            break
        elif choice.isdigit():
            read_email(int(choice), box_type)

def read_email(email_id, box_type):
    conn = sqlite3.connect("server.db")
    c = conn.cursor()
    c.execute("SELECT sender, recipient, subject, body, timestamp FROM emails WHERE id=? AND is_spam=?", (email_id, box_type))
    data = c.fetchone()
    conn.close()

    if data:
        sender, recipient, subject, body, timestamp = data
        print_header(f"MESSAGE VIEWER [ID: {email_id}]")
        
        print(f"{Style.BOLD}From    :{Style.RESET} {sender}")
        print(f"{Style.BOLD}To      :{Style.RESET} {recipient}")
        print(f"{Style.BOLD}Date    :{Style.RESET} {timestamp}")
        print(f"{Style.BOLD}Subject :{Style.RESET} {subject}")
        print(f"{Style.BLUE}{'-' * 80}{Style.RESET}")
        print(body)
        print(f"{Style.BLUE}{'-' * 80}{Style.RESET}")
        
        input(f"\n{Style.BOLD}[Press Enter to close]{Style.RESET}")
    else:
        print(f"\n{Style.FAIL} [ERROR] Message ID not found in current directory.{Style.RESET}")
        time.sleep(1)

# --- MAIN EXECUTION LOOP ---
def main():
    init_db()
    clear_screen()
    
    # Initialize Model
    model = train_model()

    while True:
        print_header("Enterprise Mail Filter - Dashboard")
        print(" 1. Compose Message")
        print(" 2. Access Inbox (Legitimate)")
        print(f" 3. Access Quarantine ({Style.FAIL}Spam{Style.RESET})")
        print(" 4. Terminate Session")
        
        choice = input(f"\nSelect Option >> ").strip()

        if choice == '1':
            send_email(model)
        elif choice == '2':
            view_mailbox(0) # 0 = Ham
        elif choice == '3':
            view_mailbox(1) # 1 = Spam
        elif choice == '4':
            print(f"\n{Style.BOLD}Terminating session...{Style.RESET}")
            sys.exit()
        else:
            print(f"{Style.FAIL}Invalid input.{Style.RESET}")
            time.sleep(0.5)

if __name__ == "__main__":
    main()
