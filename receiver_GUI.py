import customtkinter as ctk
import json
import os
from tkinter import messagebox

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")
DB_FILE = "mailbox.json"

# 1. PARTEA DE BACKEND (Logica de date)

def incarca_db():
    if not os.path.exists(DB_FILE):
        return []
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return []


def salveaza_db(lista_noua):
    with open(DB_FILE, "w") as f:
        json.dump(lista_noua, f, indent=4)


def filtreaza_emailuri(email_utilizator):
    """Returnează emailurile userului, cele mai noi primele."""
    toate = incarca_db()
    filtrate = [
        msg for msg in toate
        if msg.get('destinatar', '').strip().lower() == email_utilizator.strip().lower()
    ]
    return filtrate[::-1]


def sterge_email_din_db(id_mesaj):
    toate = incarca_db()
    lista_noua = [msg for msg in toate if msg['id'] != id_mesaj]

    if len(toate) != len(lista_noua):
        salveaza_db(lista_noua)
        return True
    return False

# 2. GUI

class ReceiverApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Inbox Client - Receiver")
        self.geometry("1100x700")

        # Variabile de stare
        self.current_user_email = ""
        self.selected_email_data = None  # Aici ținem minte ce email citim acum

        # Gestionăm ecranele (Login vs Inbox)
        self.container = ctk.CTkFrame(self)
        self.container.pack(fill="both", expand=True)

        # Pornim cu ecranul de Login
        self.show_login_screen()

    # --- ECRANUL 1: LOGIN ---
    def show_login_screen(self):
        # Curățăm tot ce e în container
        for widget in self.container.winfo_children():
            widget.destroy()

        # Cadru central
        frame_login = ctk.CTkFrame(self.container, width=400, height=300)
        frame_login.place(relx=0.5, rely=0.5, anchor="center")

        lbl_title = ctk.CTkLabel(frame_login, text="Autentificare Inbox", font=("Arial", 22, "bold"))
        lbl_title.pack(pady=(40, 20))

        self.entry_email = ctk.CTkEntry(frame_login, width=250, placeholder_text="Emailul tău (ex: victima@test.com)")
        self.entry_email.pack(pady=10)

        btn_login = ctk.CTkButton(frame_login, text="Vezi Mesaje ➤", command=self.do_login, width=200, height=40)
        btn_login.pack(pady=30)

    def do_login(self):
        email = self.entry_email.get()
        if not email:
            messagebox.showerror("Eroare", "Te rog introdu un email!")
            return

        self.current_user_email = email
        self.show_inbox_screen()

    # --- ECRANUL 2: DASHBOARD (INBOX) ---
    def show_inbox_screen(self):
        for widget in self.container.winfo_children():
            widget.destroy()

        # === LAYOUT PRINCIPAL ===
        # Stânga: Lista mesaje (Sidebar) | Dreapta: Citire mesaj
        self.frame_left = ctk.CTkFrame(self.container, width=350, corner_radius=0)
        self.frame_left.pack(side="left", fill="y")

        self.frame_right = ctk.CTkFrame(self.container, corner_radius=0, fg_color="transparent")
        self.frame_right.pack(side="right", fill="both", expand=True, padx=20, pady=20)

        # --- ZONA STÂNGA (LISTA) ---
        lbl_welcome = ctk.CTkLabel(self.frame_left, text=f"👤 {self.current_user_email}", font=("Arial", 14, "bold"))
        lbl_welcome.pack(pady=20, padx=10)

        btn_logout = ctk.CTkButton(self.frame_left, text="Iesire", command=self.show_login_screen, fg_color="#555555",
                                   height=25)
        btn_logout.pack(pady=(0, 20))

        btn_refresh = ctk.CTkButton(self.frame_left, text="🔄 Refresh", command=self.incarca_listele)
        btn_refresh.pack(pady=10)

        # Tab-uri pentru Inbox vs Junk
        self.tabview = ctk.CTkTabview(self.frame_left, width=320)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_inbox = self.tabview.add(" Inbox (Ham)")
        self.tab_junk = self.tabview.add(" Junk (Spam)")

        # Scrollable Frames în interiorul tab-urilor pentru a ține butoanele
        self.scroll_inbox = ctk.CTkScrollableFrame(self.tab_inbox, fg_color="transparent")
        self.scroll_inbox.pack(fill="both", expand=True)

        self.scroll_junk = ctk.CTkScrollableFrame(self.tab_junk, fg_color="transparent")
        self.scroll_junk.pack(fill="both", expand=True)

        # --- ZONA DREAPTĂ (CITIRE) ---
        # Header Mesaj
        self.lbl_subiect = ctk.CTkLabel(self.frame_right, text="Selectează un mesaj...", font=("Arial", 24, "bold"),
                                        anchor="w", wraplength=600)
        self.lbl_subiect.pack(fill="x", pady=(0, 10))

        self.info_frame = ctk.CTkFrame(self.frame_right, fg_color="transparent")
        self.info_frame.pack(fill="x")

        self.lbl_from = ctk.CTkLabel(self.info_frame, text="De la: -", font=("Arial", 14), anchor="w")
        self.lbl_from.pack(fill="x")

        self.lbl_date = ctk.CTkLabel(self.info_frame, text="Data: -", font=("Arial", 12), text_color="gray", anchor="w")
        self.lbl_date.pack(fill="x")

        self.lbl_verdict = ctk.CTkLabel(self.info_frame, text="Diagnostic AI: -", font=("Arial", 14, "bold"),
                                        anchor="w")
        self.lbl_verdict.pack(fill="x", pady=5)

        # Corp Mesaj
        self.textbox_read = ctk.CTkTextbox(self.frame_right, font=("Consolas", 14))
        self.textbox_read.pack(fill="both", expand=True, pady=20)
        self.textbox_read.configure(state="disabled")  # Read-only

        # Buton Ștergere
        self.btn_delete = ctk.CTkButton(self.frame_right, text="Șterge acest Email ❌", fg_color="red",
                                        hover_color="darkred", command=self.sterge_mesaj_curent)
        self.btn_delete.pack(anchor="e")
        self.btn_delete.configure(state="disabled")  # Dezactivat inițial

        # Încărcăm datele prima dată
        self.incarca_listele()

    # --- LOGICA DE AFIȘARE ---
    def incarca_listele(self):
        # 1. Ștergem butoanele vechi din liste
        for widget in self.scroll_inbox.winfo_children(): widget.destroy()
        for widget in self.scroll_junk.winfo_children(): widget.destroy()

        # 2. Luăm emailurile din JSON
        mesaje = filtreaza_emailuri(self.current_user_email)

        if not mesaje:
            lbl = ctk.CTkLabel(self.scroll_inbox, text="(Niciun mesaj)")
            lbl.pack()
            return

        # 3. Le sortăm și creăm butoane
        for msg in mesaje:
            verdict = msg.get('diagnostic', 'ham').lower()

            # Textul de pe buton
            subiect_scurt = (msg['subiect'][:25] + '..') if len(msg['subiect']) > 25 else msg['subiect']
            text_btn = f"{msg['expeditor']}\n{subiect_scurt}\n{msg['data']}"

            # Creăm butonul
            if verdict == 'spam':
                parent = self.scroll_junk
                culoare_hover = "#550000"  # Roșcat închis
            else:
                parent = self.scroll_inbox
                culoare_hover = "#004400"  # Verzui închis

            btn = ctk.CTkButton(
                parent,
                text=text_btn,
                anchor="w",
                height=60,
                fg_color="transparent",
                border_width=1,
                border_color="gray",
                hover_color=culoare_hover,
                # TRUC: Folosim lambda ca să ținem minte "msg"-ul curent
                command=lambda m=msg: self.deschide_email(m)
            )
            btn.pack(fill="x", pady=2)

    def deschide_email(self, msg):
        self.selected_email_data = msg

        # 1. Populăm Header-ul
        self.lbl_subiect.configure(text=msg['subiect'])
        self.lbl_from.configure(text=f"De la: {msg['expeditor']}")
        self.lbl_date.configure(text=f"Data: {msg['data']}")

        # 2. Verdict AI Colorat
        verdict = msg.get('diagnostic', 'N/A').upper()
        scor = msg.get('incredere', '0%')

        text_diag = f"Diagnostic AI: {verdict} (Scor: {scor})"
        if verdict == 'SPAM':
            self.lbl_verdict.configure(text=text_diag, text_color="red")
        else:
            self.lbl_verdict.configure(text=text_diag, text_color="#2CC985")  # Verde

        # 3. Corpul Mesajului
        self.textbox_read.configure(state="normal")  # Activăm scrierea
        self.textbox_read.delete("1.0", "end")
        self.textbox_read.insert("1.0", msg['mesaj'])
        self.textbox_read.configure(state="disabled")  # Blocăm la loc (Read only)

        # 4. Activăm butonul de ștergere
        self.btn_delete.configure(state="normal")

    def sterge_mesaj_curent(self):
        if not self.selected_email_data:
            return

        confirm = messagebox.askyesno("Confirmare", "Sigur vrei să ștergi acest email?")
        if confirm:
            succes = sterge_email_din_db(self.selected_email_data['id'])
            if succes:
                # Resetăm zona de citire
                self.selected_email_data = None
                self.lbl_subiect.configure(text="Selectează un mesaj...")
                self.lbl_from.configure(text="De la: -")
                self.textbox_read.configure(state="normal")
                self.textbox_read.delete("1.0", "end")
                self.textbox_read.configure(state="disabled")
                self.btn_delete.configure(state="disabled")
                self.lbl_verdict.configure(text="", text_color="gray")

                # Reîncărcăm lista
                self.incarca_listele()
                messagebox.showinfo("Succes", "Email șters definitiv.")


if __name__ == "__main__":
    app = ReceiverApp()
    app.mainloop()