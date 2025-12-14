import json
import os
import time

DB_FILE = "mailbox.json"

#Functii de lucru:

def incarca_db():

    if not os.path.exists(DB_FILE):
        return []
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return []


def salveaza_db(lista_noua):
    """Scrie lista actualizată în JSON."""
    with open(DB_FILE, "w") as f:
        json.dump(lista_noua, f, indent=4)


def filtreaza_emailuri(email_utilizator):
    """Returnează doar emailurile care aparțin utilizatorului logat."""
    toate = incarca_db()
    # Filtrăm după destinatar (ignoram literele mari/mici)
    filtrate = [
        msg for msg in toate
        if msg.get('destinatar', '').strip().lower() == email_utilizator.strip().lower()
    ]
    # Le inversăm ca să apară cele mai noi primele
    return filtrate[::-1]


def sterge_email_din_db(id_mesaj):
    """Șterge un email din baza de date globală folosind ID-ul unic."""
    toate = incarca_db()
    # Păstrăm tot ce NU are acel ID
    lista_noua = [msg for msg in toate if msg['id'] != id_mesaj]

    if len(toate) != len(lista_noua):
        salveaza_db(lista_noua)
        return True
    return False


# --- 2. INTERFAȚA UTILIZATOR (CLI) ---

def afiseaza_detalii_email(mesaj):
    """Afișează un singur email complet (cand dai OPEN)."""
    os.system('cls' if os.name == 'nt' else 'clear')  # Curăță ecranul
    print("\n" + "=" * 50)
    print(f" VIZUALIZARE EMAIL")
    print("=" * 50)

    # Header
    print(f" Data:       {mesaj['data']}")
    print(f" De la:      {mesaj['expeditor']}")
    print(f" Subiect:    {mesaj['subiect']}")

    # Verdictul AI colorat (simulat prin text)
    verdict = mesaj.get('diagnostic', 'N/A').upper()
    incredere = mesaj.get('incredere', '0%')

    if verdict == 'SPAM':
        print(f" DIAGNOSTIC: [SPAM] (Siguranța diagnostic: {incredere}) ")
    else:
        print(f" DIAGNOSTIC: [HAM] (Siguranță: {incredere})")

    print("-" * 50)
    print(" CONȚINUT MESAJ:\n")
    print(mesaj['mesaj'])
    print("\n" + "=" * 50)
    input("Apasa Enter pentru a reveni la Inbox...")


def meniu_receiver():
    print("\n=== LOGIN INBOX ===")
    user_email = input("Introdu emailul tau (ex: mircea@test.com): ")

    while True:
        # 1. curatare ecran si incarcare date
        os.system('cls' if os.name == 'nt' else 'clear')
        mesajele_mele = filtreaza_emailuri(user_email)

        print(f"\n INBOX PENTRU: {user_email}")
        print(f"Total mesaje: {len(mesajele_mele)}")
        print("-" * 80)

        # 2. Afișăm LISTA SUMARĂ (Header)
        # Formatare: Index | Data | Expeditor | Subiect (trunchiat)
        print(f"{'NR':<4} | {'DATA':<12} | {'EXPEDITOR':<20} | {'SUBIECT'}")
        print("-" * 80)

        if not mesajele_mele:
            print("   (Inbox gol)")
        else:
            for i, msg in enumerate(mesajele_mele):
                # Tăiem subiectul dacă e prea lung
                sub_scurt = (msg['subiect'][:30] + '..') if len(msg['subiect']) > 30 else msg['subiect']
                # Tăiem expeditorul dacă e prea lung
                exp_scurt = (msg['expeditor'][:18] + '..') if len(msg['expeditor']) > 18 else msg['expeditor']
                # Luăm doar ora din dată sau data scurtă
                data_scurta = msg['data'].split(' ')[0]  # Luam doar YYYY-MM-DD

                # Afișăm rândul
                print(f"{i + 1:<4} | {data_scurta:<12} | {exp_scurt:<20} | {sub_scurt}")

        print("-" * 80)
        print("COMENZI:")
        print("  read <NR>   -> Deschide emailul (ex: read 1)")
        print("  del <NR>    -> Șterge emailul (ex: del 1)")
        print("  refresh     -> Reîncarcă lista")
        print("  exit        -> Ieșire")

        # 3. Citim comanda utilizatorului
        comanda = input("\n> ").strip().lower()

        if comanda == 'exit':
            break

        elif comanda == 'refresh':
            continue  # Reia bucla

        elif comanda.startswith('read '):
            try:
                # Extragem numărul (ex: "read 2" -> 2)
                nr = int(comanda.split()[1])
                # Verificăm dacă numărul e valid în listă
                if 1 <= nr <= len(mesajele_mele):
                    # Indexul în listă e nr-1
                    mesaj_ales = mesajele_mele[nr - 1]
                    afiseaza_detalii_email(mesaj_ales)
                else:
                    print(" Număr invalid!")
                    time.sleep(1)
            except ValueError:
                print(" Comandă greșită! Folosește: read 1")
                time.sleep(1)

        elif comanda.startswith('del '):
            try:
                nr = int(comanda.split()[1])
                if 1 <= nr <= len(mesajele_mele):
                    mesaj_de_sters = mesajele_mele[nr - 1]
                    # Ștergem folosind ID-ul unic (ca să fim siguri)
                    succes = sterge_email_din_db(mesaj_de_sters['id'])
                    if succes:
                        print(" Email șters!")
                        time.sleep(1)
                else:
                    print(" Număr invalid!")
                    time.sleep(1)
            except ValueError:
                print(" Comandă greșită! Folosește: del 1")
                time.sleep(1)


if __name__ == "__main__":
    meniu_receiver()