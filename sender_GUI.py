import customtkinter as ctk
import socket
from tkinter import messagebox

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class SenderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # 1. config fereastra
        self.title("Simulator Sender Email ")
        self.geometry("1000x700")
        self.resizable(True, True)

        # 2. Titlu
        self.lbl_titlu = ctk.CTkLabel(self, text="Send Email (SMTP Standard)", font=("Arial", 20, "bold"))
        self.lbl_titlu.pack(pady=30)

        # 3. zona de IP/Port
        self.frame_server = ctk.CTkFrame(self)
        self.frame_server.pack(padx=20, pady=5, fill="x")
        #fara cele 2 linii de mai sus le ar pune default unele sub altele de aceea cream un 'raft'
        self.entry_ip = ctk.CTkEntry(self.frame_server, placeholder_text="IP Server")
        self.entry_ip.insert(0, "127.0.0.1")  # Default Localhost
        self.entry_ip.pack(side="left", padx=10, pady=10, fill="x", expand=True)

        self.entry_port = ctk.CTkEntry(self.frame_server, width=80, placeholder_text="Port")
        self.entry_port.insert(0, "1025")
        self.entry_port.pack(side="right", padx=10, pady=10)

        # 4. Zona Date Email (From, To, Subject)
        self.entry_from = ctk.CTkEntry(self, placeholder_text="De la (ex: mircea@test.com)")
        self.entry_from.pack(padx=20, pady=10, fill="x")

        self.entry_to = ctk.CTkEntry(self, placeholder_text="Către (ex: mircea@test.com)")
        self.entry_to.pack(padx=20, pady=10, fill="x")

        self.entry_subject = ctk.CTkEntry(self, placeholder_text="Subiect")
        self.entry_subject.pack(padx=20, pady=10, fill="x")

        # 5. Zona Mesaj
        self.lbl_msg = ctk.CTkLabel(self, text="Continut Mesaj:", anchor="w")#w->west(stanga)
        self.lbl_msg.pack(padx=25, pady=(10, 0), anchor="w")

        self.textbox_msg = ctk.CTkTextbox(self, height=150)
        self.textbox_msg.pack(padx=20, pady=5, fill="x")

        # 6. Buton Trimite
        self.btn_send = ctk.CTkButton(self, text="TRIMITE ACUM ➤", command=self.trimite_email, height=50,
                                      font=("Arial", 14, "bold"))
        self.btn_send.pack(padx=20, pady=20, fill="x")

        # 7. Status Bar (jos)
        self.lbl_status = ctk.CTkLabel(self, text="Status: Așteptare...", text_color="gray")
        self.lbl_status.pack(side="bottom", pady=10)

    def trimite_email(self):

        # A. Preluăm datele din căsuțe
        ip = self.entry_ip.get()
        port_str = self.entry_port.get()
        expeditor = self.entry_from.get()
        destinatar = self.entry_to.get()
        subiect = self.entry_subject.get()
        mesaj_text = self.textbox_msg.get("1.0", "end-1c")  # Tot textul fara ultimul caracter ca libraria
                                                                          # pune default /n la final
        # Validare campuri
        if not expeditor or not destinatar or not subiect:
            messagebox.showerror("Eroare", "Completeaza toate campurile!")
            return

        self.lbl_status.configure(text="Se conectează la server...", text_color="orange")
        self.update()  # Forțeaza actualizarea graficii,inainte de a ajunge la mainloop()

        # B. LOGICA DE SOCKET
        client_socket = None
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(5)
            client_socket.connect((ip, int(port_str)))

            def primeste():
                msg = client_socket.recv(1024).decode()
                print(f"[DEBUG SERVER]: {msg.strip()}")
                return msg

            # Pas 0: Salut
            primeste()

            # Pas 1: HELO
            client_socket.send(b"HELO sender_gui\r\n")
            primeste()

            # Pas 2: MAIL FROM
            client_socket.send(f"MAIL FROM: <{expeditor}>\r\n".encode())
            primeste()

            # Pas 3: RCPT TO
            client_socket.send(f"RCPT TO: <{destinatar}>\r\n".encode())
            primeste()

            # Pas 4: DATA
            client_socket.send(b"DATA\r\n")
            primeste()  # Așteptăm 354

            # Pas 5: Trimitem Headers + Corp (Standardul nou)
            full_email = (
                f"Subject: {subiect}\r\n"
                f"From: {expeditor}\r\n"
                f"To: {destinatar}\r\n"
                f"\r\n"
                f"{mesaj_text}"
            )

            client_socket.send(f"{full_email}\r\n.\r\n".encode())

            # Pas 6: Verdictul Final
            raspuns_final = primeste()

            # Pas 7: QUIT
            client_socket.send(b"QUIT\r\n")
            client_socket.close()

            # C. Afișare Rezultat pe Ecran
            if "250" in raspuns_final:
                self.lbl_status.configure(text=" Mesaj Trimis cu Succes!", text_color="#2CC985")  # Verde
                messagebox.showinfo("Succes", f"Serverul a acceptat mesajul!\nRăspuns: {raspuns_final.strip()}")
            else:
                self.lbl_status.configure(text=" Mesaj Respins/Eroare!", text_color="red")
                messagebox.showwarning("Atenție", f"Serverul a respins mesajul.\nRăspuns: {raspuns_final.strip()}")

        except Exception as e:
            self.lbl_status.configure(text="Eroare Conexiune", text_color="red")
            messagebox.showerror("Eroare Critică", f"Nu m-am putut conecta la {ip}:{port_str}\n\nDetalii: {e}")
            if client_socket:
                client_socket.close()

if __name__ == "__main__":
    app = SenderApp()
    app.mainloop()