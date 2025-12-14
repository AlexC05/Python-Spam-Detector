import socket

# --- CONFIGURARE ---
HOST = '127.0.0.1'
PORT = 1025


def trimite_email_manual():
    print("\n=== SIMULATOR SENDER (STANDARD SMTP) ===")

    # 1. Culegem datele
    expeditor = input("De la (ex: hacker@test.com): ")
    destinatar = input("Către (ex: victima@test.com): ")
    subiect = input("Subiect: ")
    print("Scrie mesajul (apoi apasă Enter):")
    mesaj_text = input("> ")

    print("\n--- ÎNCEP COMUNICAREA CU SERVERUL ---\n")

    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((HOST, PORT))

        def primeste_raspuns():
            raspuns = client_socket.recv(1024).decode()
            print(f"[SERVER]: {raspuns.strip()}")
            return raspuns

        # Pas 0: Salutul
        primeste_raspuns()

        # Pas 1: HELO
        print(f"[CLIENT]: HELO sender")
        client_socket.send(b"HELO sender\r\n")
        primeste_raspuns()

        # Pas 2: MAIL FROM
        print(f"[CLIENT]: MAIL FROM: <{expeditor}>")
        client_socket.send(f"MAIL FROM: <{expeditor}>\r\n".encode())
        primeste_raspuns()

        # Pas 3: RCPT TO
        print(f"[CLIENT]: RCPT TO: <{destinatar}>")
        client_socket.send(f"RCPT TO: <{destinatar}>\r\n".encode())
        primeste_raspuns()

        # Pas 4: DATA
        print(f"[CLIENT]: DATA")
        client_socket.send(b"DATA\r\n")
        primeste_raspuns()  # Așteptăm 354 Start input

        full_email = (
            f"Subject: {subiect}\r\n"
            f"From: {expeditor}\r\n"
            f"To: {destinatar}\r\n"
            f"\r\n"  # Linia goala care separa antetul de corp
            f"{mesaj_text}"
        )

        print(f"[CLIENT]: (Trimite Headers + Corp + . final)")
        client_socket.send(f"{full_email}\r\n.\r\n".encode())
        # -----------------------------------

        # Pas 5: Verdictul
        raspuns = primeste_raspuns()

        # Pas 6: QUIT
        client_socket.send(b"QUIT\r\n")
        primeste_raspuns()

        client_socket.close()

    except Exception as e:
        print(f"EROARE: {e}")


if __name__ == "__main__":

    while True:
        trimite_email_manual()
        continuam = input("\nVrei să mai trimiți unul? (d/n): ")
        if continuam.lower() != 'd':
            break