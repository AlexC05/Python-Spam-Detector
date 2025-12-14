import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import sqlite3
import pandas as pd
import datetime
import os

# --- AI & MACHINE LEARNING LIBRARIES ---
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.pipeline import Pipeline

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect("server.db")
    c = conn.cursor()
    # Create a table to store sent emails
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

class LocalEmailSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("Local SMTP & SVM Spam Filter")
        self.root.geometry("900x750")
        
        init_db()
        self.model = None
        
        # --- 1. SENDER SECTION (Top) ---
        sender_frame = tk.LabelFrame(root, text="SENDER CLIENT (Compose Email) ", font=("Arial", 10, "bold"), bg="#f0f0f0")
        sender_frame.pack(fill="x", padx=10, pady=5, ipady=5)

        # Inputs
        tk.Label(sender_frame, text="From:", bg="#f0f0f0").grid(row=0, column=0, sticky="e", padx=5)
        self.ent_from = tk.Entry(sender_frame, width=30)
        self.ent_from.insert(0, "spammer@bad.net")
        self.ent_from.grid(row=0, column=1, padx=5)

        tk.Label(sender_frame, text="To:", bg="#f0f0f0").grid(row=0, column=2, sticky="e", padx=5)
        self.ent_to = tk.Entry(sender_frame, width=30)
        self.ent_to.insert(0, "me@local.com")
        self.ent_to.grid(row=0, column=3, padx=5)

        tk.Label(sender_frame, text="Subject:", bg="#f0f0f0").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.ent_subject = tk.Entry(sender_frame, width=75)
        self.ent_subject.grid(row=1, column=1, columnspan=3, padx=5, pady=5)

        tk.Label(sender_frame, text="Body:", bg="#f0f0f0").grid(row=2, column=0, sticky="ne", padx=5)
        self.txt_body = scrolledtext.ScrolledText(sender_frame, height=6, width=80)
        self.txt_body.grid(row=2, column=1, columnspan=3, padx=5, pady=5)

        # Send Button
        self.btn_send = tk.Button(sender_frame, text="SEND EMAIL", bg="#2196F3", fg="white", font=("bold"), command=self.send_email)
        self.btn_send.grid(row=3, column=1, columnspan=3, pady=10)

        # --- 2. SERVER STATUS (Middle) ---
        self.lbl_status = tk.Label(root, text="Server Status: Loading emails.csv...", fg="blue", font=("Arial", 11))
        self.lbl_status.pack(pady=5)

        # --- 3. RECEIVER SECTION (Bottom) ---
        receiver_frame = tk.LabelFrame(root, text=" 📥 RECEIVER CLIENT (Inbox) ", font=("Arial", 10, "bold"), bg="#e0e0e0")
        receiver_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.tabs = ttk.Notebook(receiver_frame)
        self.tabs.pack(fill="both", expand=True, padx=5, pady=5)

        self.tab_inbox = tk.Frame(self.tabs)
        self.tabs.add(self.tab_inbox, text="Inbox (Ham)  ")
        
        self.tab_spam = tk.Frame(self.tabs)
        self.tabs.add(self.tab_spam, text=" Junk Folder  ")

        self.tree_inbox = self.create_email_list(self.tab_inbox)
        self.tree_spam = self.create_email_list(self.tab_spam)

        tk.Button(receiver_frame, text="Refresh Inboxes", command=self.load_emails).pack(pady=5)

        # Start Training immediately
        self.train_ai()

    def create_email_list(self, parent):
        tree = ttk.Treeview(parent, columns=("ID", "Sender", "Subject", "Time"), show='headings', height=8)
        tree.heading("ID", text="ID")
        tree.heading("Sender", text="From")
        tree.heading("Subject", text="Subject")
        tree.heading("Time", text="Received")
        
        tree.column("ID", width=30)
        tree.column("Sender", width=150)
        tree.column("Subject", width=300)
        tree.column("Time", width=150)
        
        tree.pack(fill="both", expand=True)
        tree.bind("<Double-1>", self.read_email)
        return tree

    def train_ai(self):
        try:
            # 1. Load Data
            if not os.path.exists('emails.csv'):
                self.lbl_status.config(text="Error: emails.csv file missing!", fg="red")
                return

            df = pd.read_csv('emails.csv')
            
            # Check for correct columns
            if 'text' not in df.columns or 'spam' not in df.columns:
                self.lbl_status.config(text="Error: CSV needs 'text' and 'spam' columns", fg="red")
                return

            X = df['text'].astype(str)
            y = df['spam']
            
            # 2. Build Pipeline (The "Brain")
            # We use TF-IDF + N-Grams + LinearSVC for high accuracy
            self.model = Pipeline([
                ('vectorizer', TfidfVectorizer(stop_words='english', ngram_range=(1, 2))),
                ('classifier', LinearSVC(class_weight='balanced', dual='auto'))
            ])
            
            # 3. Train
            self.model.fit(X, y)
            
            # 4. Success Message
            acc = self.model.score(X, y)
            self.lbl_status.config(text=f"Server Online | Model: SVM (Fine-Tuned) | Training Size: {len(df)} emails", fg="green")
            self.load_emails()

        except Exception as e:
            self.lbl_status.config(text=f"Training Failed: {str(e)}", fg="red")
            print(e)

    def send_email(self):
        if not self.model:
            messagebox.showerror("Error", "Model not trained. Check emails.csv")
            return

        sender = self.ent_from.get()
        recipient = self.ent_to.get()
        subject = self.ent_subject.get()
        body = self.txt_body.get("1.0", tk.END).strip()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if not body:
            messagebox.showwarning("Empty", "Body is empty.")
            return

        # --- INTELLIGENT DETECTION ---
        # We combine Subject + Body to catch spam hidden in headers
        full_content = f"{subject} {body}"
        
        try:
            prediction = self.model.predict([full_content])[0]
            is_spam = int(prediction) # 1 = Spam, 0 = Ham
        except Exception as e:
            messagebox.showerror("Prediction Error", str(e))
            return

        # Save to Local DB
        conn = sqlite3.connect("server.db")
        c = conn.cursor()
        c.execute("INSERT INTO emails (sender, recipient, subject, body, timestamp, is_spam) VALUES (?, ?, ?, ?, ?, ?)",
                  (sender, recipient, subject, body, timestamp, is_spam))
        conn.commit()
        conn.close()

        # UI Updates
        self.txt_body.delete("1.0", tk.END)
        self.ent_subject.delete(0, tk.END)
        
        if is_spam == 1:
            self.lbl_status.config(text="SERVER LOG: Email identified as SPAM -> Routed to Junk", fg="#d32f2f")
        else:
            self.lbl_status.config(text="SERVER LOG: Email identified as SAFE -> Routed to Inbox", fg="#388e3c")

        self.load_emails()

    def load_emails(self):
        # Clear lists
        for row in self.tree_inbox.get_children(): self.tree_inbox.delete(row)
        for row in self.tree_spam.get_children(): self.tree_spam.delete(row)

        conn = sqlite3.connect("server.db")
        c = conn.cursor()
        
        # Load Ham (Inbox)
        c.execute("SELECT id, sender, subject, timestamp FROM emails WHERE is_spam=0 ORDER BY id DESC")
        for row in c.fetchall():
            self.tree_inbox.insert("", "end", values=row)

        # Load Spam (Junk)
        c.execute("SELECT id, sender, subject, timestamp FROM emails WHERE is_spam=1 ORDER BY id DESC")
        for row in c.fetchall():
            self.tree_spam.insert("", "end", values=row)

        conn.close()

    def read_email(self, event):
        tree = event.widget
        selection = tree.selection()
        if not selection: return
        
        item = tree.item(selection[0])
        email_id = item['values'][0]

        conn = sqlite3.connect("server.db")
        c = conn.cursor()
        c.execute("SELECT sender, subject, body FROM emails WHERE id=?", (email_id,))
        data = c.fetchone()
        conn.close()

        if data:
            top = tk.Toplevel(self.root)
            top.title(f"Reading Email #{email_id}")
            top.geometry("500x450")
            
            tk.Label(top, text=f"From: {data[0]}", font=("bold")).pack(anchor="w", padx=10, pady=5)
            tk.Label(top, text=f"Subject: {data[1]}", font=("bold")).pack(anchor="w", padx=10)
            tk.Frame(top, height=2, bd=1, relief=tk.SUNKEN).pack(fill="x", padx=10, pady=10)
            
            msg_area = scrolledtext.ScrolledText(top, height=15, width=60)
            msg_area.pack(padx=10, pady=5)
            msg_area.insert(tk.END, data[2])
            msg_area.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    app = LocalEmailSimulator(root)
    root.mainloop()
