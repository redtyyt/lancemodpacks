import minecraft_launcher_lib

client_id = "00000000-0000-0000-0000-000000000000"  # <-- devi mettere il tuo Client ID Azure
redirect_uri = "http://localhost:8000"             # <-- configurato su Azure

# Avvia login Microsoft
login_url, state, code_verifier = minecraft_launcher_lib.microsoft_account.get_secure_login_data(
    client_id, redirect_uri
)

print("Apri questo link nel browser per accedere:")
print(login_url)

# Dopo login, l'utente viene reindirizzato al redirect_uri con il codice
authorization_code = input("Inserisci il codice ottenuto: ")

# Ottieni i dati dell'account
login_data = minecraft_launcher_lib.microsoft_account.complete_login(
    client_id, redirect_uri, authorization_code, code_verifier
)

print("Login completato!")
print(login_data)
