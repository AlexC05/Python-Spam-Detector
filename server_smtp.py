import os
import json
from datetime import datetime
from transformers import pipeline
from aiosmtpd.controller import Controller
from email import message_from_bytes

# Config
HOST = '127.0.0.1'
PORT = 1025
DB_FILE = "mailbox.json"

# incarcare AI
print("[SERVER] Se incarca modelul AI...")
classifier = pipeline("text-classification", model="dima806/email-spam-detection-distilbert")
print("[SERVER] Model AI incarcat")


# functie salvare in fisier
def salveaza_in_json(expeditor, destinatar, subiect, mesaj, verdict, scor):
    email_nou = {
        "id": datetime.now().strftime("%Y%m%d%H%M%S"),
        "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "expeditor": expeditor,
        "destinatar": destinatar,
        "subiect": subiect,
        "mesaj": mesaj,
        "diagnostic": verdict,
        "incredere": f"{scor:.2f}%"
    }

    lista = []
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                lista = json.load(f)
        except:
            lista = []

    lista.append(email_nou)
    with open(DB_FILE, "w") as f:
        json.dump(lista, f, indent=4)
    print(f"[DATABASE] Salvat: {subiect} -> {verdict}")


# gestionare email-uri,modificam doar functia handle_DATA ,restul le folosim ca default
class SpamHandler:
    async def handle_DATA(self, server, session, envelope):
        print(f"\n[SERVER] Mesaj primit de la: {envelope.mail_from}")

        # 'envelope.content' conține tot textul brut (inclusiv headers)
        mesaj_email = message_from_bytes(envelope.content)

        # Extragere date automat
        subiect = mesaj_email.get('Subject', 'Fara Subiect')#cauta linie cu Subject ,daca nu este pune default Fara Subiect
        expeditor = envelope.mail_from #salvat de la mesajele date anterior prin MAIL FROM: ..
        destinatar = envelope.rcpt_tos[0]  # e o lista ca merge sa dai mai multi destinatari

        # Extragem doar corpul textului (fără headers)
        corp_mesaj = ""
        if mesaj_email.is_multipart():
            for part in mesaj_email.walk():
                if part.get_content_type() == "text/plain":
                    corp_mesaj = part.get_payload(decode=True).decode()
                    break
        else:
            corp_mesaj = mesaj_email.get_payload(decode=True).decode()

        # --- LOGICA AI ---
        print("[AI] Analizez...")
        # Concatenam Subiect + Corp
        text_de_analizat = f"{subiect} {corp_mesaj}"

        rezultat = classifier(text_de_analizat[:512], truncation=True, max_length=512)
        eticheta = rezultat[0]['label']
        scor = rezultat[0]['score'] * 100

        verdict = 'spam' if eticheta.lower() in ['spam', 'label_1'] else 'ham'

        # --- SALVARE ---
        salveaza_in_json(expeditor, destinatar, subiect, corp_mesaj, verdict, scor)

        # Returnam codul 250 OK
        return '250 OK Message accepted for delivery'


# 4. PORNIRE CONTROLLER (Înlocuiește Socket Bind/Listen)
if __name__ == '__main__':
    handler = SpamHandler()
    controller = Controller(handler, hostname=HOST, port=PORT)

    # Pornește serverul în background
    controller.start()
    print(f"[SERVER] Rulează pe {HOST}:{PORT}. Apasă Ctrl+C pentru a opri.")

    # Ținem programul deschis
    try:
        import time

        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        controller.stop()