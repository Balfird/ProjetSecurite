#!/usr/bin/env python3
import imaplib

# VOS INFORMATIONS
EMAIL = "contact@anne-gerard.net"
PASSWORD = "mdppxk3y8t7Y8y"

servers_to_test = [
    "mail.anne-gerard.net",
    "imap.anne-gerard.net",
    "anne-gerard.net",
]

port = 993

print("=" * 60)
print("TEST DE CONNEXION IMAP")
print("=" * 60)

for server in servers_to_test:
    try:
        print(f"\n Test: {server}:{port}")
        
        conn = imaplib.IMAP4_SSL(server, port, timeout=10)

        print(f"    Connexion au serveur réussie!")
        
        # Tentative de login
        conn.login(EMAIL, PASSWORD)
        print(f"    LOGIN RÉUSSI {server}:{port}")
        
        conn.logout()
        print("\n" + "=" * 60)
        print(" SUCCÈS ! ")
        print(f'   "imap_server": "{server}",')
        print(f'   "imap_port": {port},')
        print("=" * 60)
        exit(0)
        
    except imaplib.IMAP4.error as e:
        print(f"    Erreur d'authentification: {e}")
    except ConnectionRefusedError:
        print(f"    Connexion refusée (port fermé)")
    except Exception as e:
        print(f"    Échec: {type(e).__name__}: {e}")

print("\n" + "=" * 60)
print(" Aucun serveur n'a fonctionné")
print("=" * 60)