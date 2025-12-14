import tkinter as tk
from tkinter import messagebox, scrolledtext
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class GmailSpamApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Spam Detector")
        self.root.geometry("600x750")
        self.model = None
        self.last_prediction = None 

        # --- HEADER ---
        tk.Label(root, text="Gmail Spam Filter & AI", font=("Helvetica", 16, "bold")).pack(pady=10)
        
        # Status Label (Shows training result immediately)
        self.status_label = tk.Label(root, text="Initializing...", fg="blue", font=("Arial", 10))
        self.status_label.pack()

        # --- EMAIL BODY INPUT ---
        tk.Label(root, text="1. Write Email Content(English only):", font=("Arial", 10, "bold")).pack(pady=(15, 5))
        self.text_input = scrolledtext.ScrolledText(root, height=8, width=65)
        self.text_input.pack(pady=5)

        # --- DETECT BUTTON ---
        # Note: Train button is gone. We only have Detect.
        self.detect_btn = tk.Button(root, text="Analyze Email", command=self.detect_spam, bg="#add8e6", font=("Arial", 11), state=tk.DISABLED)
        self.detect_btn.pack(pady=10)

        # Result Label
        self.result_label = tk.Label(root, text="", font=("Helvetica", 12, "bold"))
        self.result_label.pack(pady=5)

        # --- GMAIL LOGIN SECTION ---
        tk.Frame(root, height=2, bd=1, relief=tk.SUNKEN).pack(fill=tk.X, padx=20, pady=10)
        tk.Label(root, text="2. Gmail Login", font=("Arial", 10, "bold")).pack()

        login_frame = tk.Frame(root)
        login_frame.pack(pady=5)

        tk.Label(login_frame, text="Your Gmail:").grid(row=0, column=0, sticky="e")
        self.entry_user = tk.Entry(login_frame, width=35)
        self.entry_user.grid(row=0, column=1, padx=5, pady=2)

        tk.Label(login_frame, text="App Password:").grid(row=1, column=0, sticky="e")
        self.entry_pass = tk.Entry(login_frame, width=35, show="*")
        self.entry_pass.grid(row=1, column=1, padx=5, pady=2)
        
        tk.Label(root, text="(Use Google App Password)", font=("Arial", 8), fg="gray").pack()

        # --- RECIPIENT SECTION ---
        tk.Label(root, text="3. Send Details", font=("Arial", 10, "bold")).pack(pady=(15, 5))
        
        send_frame = tk.Frame(root)
        send_frame.pack(pady=5)

        tk.Label(send_frame, text="Send To:").grid(row=0, column=0, sticky="e")
        self.entry_to = tk.Entry(send_frame, width=35)
        self.entry_to.grid(row=0, column=1, padx=5, pady=2)

        tk.Label(send_frame, text="Subject:").grid(row=1, column=0, sticky="e")
        self.entry_subject = tk.Entry(send_frame, width=35)
        self.entry_subject.grid(row=1, column=1, padx=5, pady=2)

        # --- SEND BUTTON ---
        self.send_btn = tk.Button(root, text="Send Email (Safe Only)", command=self.send_via_gmail, bg="#90ee90", state=tk.DISABLED, font=("Arial", 10, "bold"))
        self.send_btn.pack(pady=20)

        # TRIGGER AUTOMATIC TRAINING
        self.train_model()

    def train_model(self):
        try:
            # Load CSV
            df = pd.read_csv('emails.csv')
            
            if 'text' not in df.columns or 'spam' not in df.columns:
                raise ValueError("CSV needs 'text' and 'spam' columns")

            X = df['text'].astype(str)
            y = df['spam']

            # Build Pipeline
            self.model = Pipeline([
                ('vectorizer', CountVectorizer()),
                ('classifier', MultinomialNB())
            ])
            
            # Train on EVERYTHING (since we don't need a test set for the app to function)
            self.model.fit(X, y)

            # Update UI
            self.status_label.config(text=f"System Ready (Trained on {len(df)} emails)", fg="green")
            self.detect_btn.config(state=tk.NORMAL)

        except FileNotFoundError:
            self.status_label.config(text="Error: emails.csv not found!", fg="red")
            messagebox.showerror("Missing File", "Could not find 'emails.csv'. Please create it and restart the app.")
        except Exception as e:
            self.status_label.config(text="Training Error", fg="red")
            messagebox.showerror("Error", f"Training failed:\n{e}")

    def detect_spam(self):
        if not self.model: return

        text = self.text_input.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Warning", "Please write an email first.")
            return

        try:
            # 1. Get Probabilities (Confidence)
            # returns [[prob_ham, prob_spam]] -> e.g. [[0.05, 0.95]]
            probabilities = self.model.predict_proba([text])[0]
            
            # We assume class 0 is Ham, class 1 is Spam (standard sort order)
            # You can check self.model.classes_ to be 100% sure, but usually 0 comes before 1
            prob_ham = probabilities[0]
            prob_spam = probabilities[1]

            # 2. Determine Result
            if prob_spam > prob_ham:
                # IT IS SPAM
                self.last_prediction = 1
                confidence = prob_spam * 100
                self.result_label.config(text=f"SPAM DETECTED ({confidence:.1f}% confidence)", fg="red")
                self.send_btn.config(state=tk.DISABLED, text="Cannot Send Spam", bg="#ffcccc")
            else:
                # IT IS HAM
                self.last_prediction = 0
                confidence = prob_ham * 100
                self.result_label.config(text=f"SAFE TO SEND ({confidence:.1f}% confidence)", fg="green")
                self.send_btn.config(state=tk.NORMAL, text="Send Email", bg="#90ee90")

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def send_via_gmail(self):
        if self.last_prediction == 1:
            messagebox.showerror("Blocked", "This email is flagged as SPAM and cannot be sent.")
            return

        user_email = self.entry_user.get().strip()
        user_pass = self.entry_pass.get().strip()
        receiver = self.entry_to.get().strip()
        subject = self.entry_subject.get().strip()
        body = self.text_input.get("1.0", tk.END).strip()

        if not user_email or not user_pass or not receiver:
            messagebox.showwarning("Missing Info", "Please fill in all fields.")
            return

        try:
            msg = MIMEMultipart()
            msg['From'] = user_email
            msg['To'] = receiver
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            context = ssl.create_default_context()

            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls(context=context)
                server.login(user_email, user_pass)
                server.sendmail(user_email, receiver, msg.as_string())

            messagebox.showinfo("Success", "Email Sent Successfully!")

        except smtplib.SMTPAuthenticationError:
            messagebox.showerror("Login Failed", "Auth failed. Did you use an App Password?")
        except Exception as e:
            messagebox.showerror("Error", f"Could not send email:\n{e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = GmailSpamApp(root)
    root.mainloop()
