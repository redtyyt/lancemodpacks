import tkinter as tk
from tkinter import ttk
import pyglet, requests, random, threading, os, tqdm
import re, zipfile
from urllib.parse import urlparse, parse_qs
from tkinter import filedialog, messagebox
from utilities.offline import cc_usrname, launch

appdataloc = os.getenv("LOCALAPPDATA")
if appdataloc:
    DOWNLOAD_DIR = os.path.join(appdataloc, "RedTy", "Lance Modpacks", "downloads")
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)  # Ensure the download directory exists

def random_text():
    random_texts = [
        "C'è stato un errore nel recuperare i modpacks.",
        "Sei connesso a internet?",
        "Se il problema persiste, contatta il supporto. (redty2011@gmail.com)",
        "Oh ma guarda, un errore!",
        "Sembra che ci sia un problema con la connessione.",
        "Forse il server è in manutenzione.",
        "Hai provato a spegnere e riaccendere il computer?",
        "A volte basta un semplice aggiornamento.",
        "Non è colpa tua, è colpa del server.",
        "Forse ti viene da esplodere",
        "Oh mio dio, non riesco a recuperare i modpack",
        "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAHhhhhhhhhhhhhhhhhhhhhhhhh",
        "Ops.. Forse GitHub è buggato :|",
        "Puoi giocare un attimo a minecraft non moddato?",
        "Perchè non funziona?",
        "Cavoletti di Bruxelles... Perchè non va?",
        "Devi chiedere a RedTy di fixare questo bug... Non funziona!",
        "Riaccendi e spegni il tuo router se non funziona mai",
        "Ma che diamine? Perchè non funziona?",
        "Ho speso letteralmente 100 anni a scrivere sti messaggi che vedi qui!",
        "Ok passiamo alle cose di Minecraft... Hai ucciso un delfino? Sei un MOSTRO!",
        "Mannaggia al server",
        "Quand'è che funzionerà? Chi lo sa?",
        "Ti ricordi la differenza tra CLIENT e SERVER??? Beh, in questo caso non funzionano.",
        "Qualcuno mi aiuti! Non funziona.",
        "Mi sa che il bro server è down...",
        "Non ti darò consigli utili, ma posso dirti che il tuo PC fa schifo :)",
        "Mannaggia al tuo PC...",
        "Mannaggia al tuo Wi-Fi",
        "Grazie alla Mannoia non funziona",
        "MA QUANTO è LENTO IL TUO WIFI?"
    ]
    return random.choice(random_texts)

# ------------------ HELPERS GOOGLE DRIVE ------------------
def _extract_gdrive_file_id(url: str) -> str | None:
    p = urlparse(url)
    if "drive.google.com" in (p.hostname or "").lower() or "docs.google.com" in (p.hostname or "").lower():
        qs = parse_qs(p.query or "")
        if "id" in qs and qs["id"]:
            return qs["id"][0]
        m = re.search(r"/file/d/([a-zA-Z0-9_-]+)", p.path or "")
        if m:
            return m.group(1)
    return None

def _filename_from_headers(resp, fallback: str = "download.bin") -> str:
    cd = resp.headers.get("Content-Disposition", "")
    m = re.search(r'filename\*?=(?:UTF-8\'\')?"?([^\";]+)"?', cd)
    if m:
        return os.path.basename(m.group(1)).strip()
    return fallback

def _save_stream(resp: requests.Response, dest_dir: str, suggested_name: str) -> str:
    os.makedirs(dest_dir, exist_ok=True)
    filename = _filename_from_headers(resp, fallback=suggested_name)
    path = os.path.join(dest_dir, filename)
    with open(path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=32768):
            if chunk:
                f.write(chunk)
    return path

def download_from_google_drive(url: str, dest_dir: str) -> str:
    file_id = _extract_gdrive_file_id(url)
    if not file_id:
        raise ValueError("URL di Google Drive non valido o ID non trovato.")

    session = requests.Session()
    base1 = "https://drive.google.com/uc"
    params = {"export": "download", "id": file_id}
    r1 = session.get(base1, params=params, stream=True)
    r1.raise_for_status()

    if "text/html" not in r1.headers.get("Content-Type", ""):
        return _save_stream(r1, dest_dir, f"{file_id}.bin")

    token = None
    for k, v in r1.cookies.items():
        if k.startswith("download_warning"):
            token = v
            break
    if not token:
        m = re.search(r'name="confirm"\s+value="([^"]+)"', r1.text)
        if m:
            token = m.group(1)
    if not token:
        raise RuntimeError("Impossibile ottenere il token di conferma da Google Drive.")

    base2 = "https://drive.usercontent.google.com/download"
    params["confirm"] = token
    r2 = session.get(base2, params=params, stream=True)
    r2.raise_for_status()
    if "text/html" in r2.headers.get("Content-Type", ""):
        raise RuntimeError("Google Drive ha restituito HTML invece del file.")
    return _save_stream(r2, dest_dir, f"{file_id}.bin")

# ------------------ DOWNLOAD MODPACK ------------------
def download_modpack(url: str, name: str):
    try:
        if any(h in url for h in ("drive.google.com", "docs.google.com", "drive.usercontent.google.com")):
            saved_path = download_from_google_drive(url, DOWNLOAD_DIR)
            print(f"✅ Salvato da Google Drive: {saved_path}")
            extract_zip(saved_path)
            return

        # Download normale
        r = requests.get(url, stream=True)
        r.raise_for_status()
        total_size = int(r.headers.get('content-length', 0))
        filename = os.path.basename(url.split("?")[0]) or name
        file_path = os.path.join(DOWNLOAD_DIR, filename)
        with open(file_path, "wb") as f, tqdm.tqdm(total=total_size, unit='B', unit_scale=True) as bar:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    bar.update(len(chunk))
        print(f"✅ Salvato: {file_path}")
        
    except Exception as e:
        print(f"❌ Errore download: {e}")

# --------------- APPLY MODPACK ----------------
def extract_zip(zip_path:str):
    appdata = os.getenv("APPDATA")
    if appdata:
        extract_dir = filedialog.askdirectory(title="Seleziona cartella delle mod minecraft o delle versions/mods", initialdir=os.path.join(appdata, ".minecraft"))
        if not extract_dir:
            print("Cancelled!")
            return
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_r:
                zip_r.extractall(extract_dir)
            print(f"Files extracted successfully! {extract_dir}")
        except Exception as e:
            print(f"Error while extracting: {e}")

# -------------- CRACKED or ONLINE -------------
def define_():
    yn = messagebox.askyesnocancel(title="CRACCATO O PREMIUM?", message="Vuoi usare Minecraft Premium?")
    if yn:
        print("NOT IMPLEMENTED!")
        return
    else:
        messagebox.showwarning(title="VAI SUL TERMINALE!", message="Scrivi sul terminale il nome che vuoi usare per minecraft!")
        messagebox.showerror(title="Error!", message="Non puoi ancora usare questa funzione! E' in sviluppo.. Ma se riesci ad abilitarla nel codice sorgente puoi usarla.")
        # usr = input("Inserisci qui l'username.")
        # cc_usrname(usr)
        # print("Grazie!")
        # sc = input("Vuoi lanciare minecraft 1.21.1 o 1.21.8?\n1 = 1.21.8\n2 = 1.21.1")
        # launch(sc)
        return
        

# ------------------ MAIN APP ------------------
def main():
    pyglet.font.add_file("resources\\font\\MinecraftEvenings.ttf")
    window = tk.Tk()

    window.title("Lance Modpacks")
    window.geometry("1280x720")
    window.configure(background="#2e2e2e")

    # Title
    title = tk.Label(window, text="Lance Modpacks", background="#2e2e2e",
                     foreground="#ff0000", font=("Minecraft Evenings", 40), anchor="center")
    title.pack()

    subtitle = tk.Label(window, text="A Custom Modpack Launcher", background="#2e2e2e",
                        foreground="#ffffff", font=("Minecraft Evenings", 23), anchor="center")
    subtitle.pack()

    # Scrollable frame
    canvas = tk.Canvas(window, background="#2e2e2e", highlightthickness=0)
    scrollbar = tk.Scrollbar(window, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, background="#2e2e2e")

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    def get_modpacklist():
        for widget in scrollable_frame.winfo_children():
            widget.destroy()

        try:
            modpacklist = requests.get(
                "https://raw.githubusercontent.com/redtyyt/lancemodpacks/resources/modpacks.json"
            )
            if modpacklist.status_code == 200:
                try:
                    modpacks = modpacklist.json()
                except Exception as e:
                    tk.Label(scrollable_frame, text=random_text(), bg="#2e2e2e", fg="white").pack()
                    print(e)
                    return

                if not modpacks:
                    tk.Label(scrollable_frame, text="Nessun modpack trovato.",
                             bg="#2e2e2e", fg="white").pack()
                else:
                    for modpack in modpacks:
                        row = tk.Frame(scrollable_frame, bg="#2e2e2e")
                        row.pack(fill="x", pady=5)

                        name_label = tk.Label(row, text=modpack['name'], bg="#2e2e2e",
                                              fg="white", font=("System", 22))
                        name_label.pack(side="left", padx=10)

                        dl_btn = tk.Button(row, text="Download",
                                           command=lambda url=modpack['url'], name=modpack['name']: threading.Thread(
                                               target=download_modpack, args=(url, name,)
                                           ).start())
                        dl_btn.pack(side="right", padx=10)
            else:
                tk.Label(scrollable_frame, text=random_text(),
                         bg="#2e2e2e", fg="white").pack()
        except requests.exceptions.ConnectionError:
            tk.Label(scrollable_frame, text=random_text(),
                     bg="#2e2e2e", fg="white").pack()

    # Refresh button
    refresh_button = ttk.Button(window, text="Aggiorna Modpacks",
                               command=lambda: threading.Thread(target=get_modpacklist).start())
    refresh_button.pack(pady=10)
    launch_button = ttk.Button(window, text="Lancia Minecraft", command=lambda: define_())
    launch_button.pack(pady=10)

    threading.Thread(target=get_modpacklist).start()

    window.mainloop()


if __name__ == "__main__":
    main()
