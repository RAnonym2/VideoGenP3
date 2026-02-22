import os
import requests
import random
import shutil

# --- KONFIGURÁCIÓ ---
MUSIC_FOLDER = "MUSIC_TEST"

MUSIC_URLS = [
    "https://drive.google.com/file/d/1ENHhoBnMBAxDblwa0e24tYOKLlXU-9qi/view?usp=drive_link",
    "https://drive.google.com/file/d/1YQcZse2rwvahnPjINv5HHXmGsaEEFRd1/view?usp=drive_link"
]

def download_one_random_music():
    print(f"--- 1. TESZT: Mappa tisztítása ({MUSIC_FOLDER}) ---")
    if os.path.exists(MUSIC_FOLDER):
        shutil.rmtree(MUSIC_FOLDER)
    os.makedirs(MUSIC_FOLDER)

    print(f"--- 2. TESZT: Random URL kiválasztása és letöltése ---")
    
    # ITT TÖRTÉNIK A MÁGIA: Előbb választunk, aztán töltünk
    chosen_url = random.choice(MUSIC_URLS)
    print(f"🎲 A gép választása: {chosen_url}")

    try:
        # Drive fix
        if "drive.google.com" in chosen_url:
            file_id = chosen_url.split("/d/")[1].split("/")[0]
            chosen_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        
        filename = os.path.join(MUSIC_FOLDER, "downloaded_music.mp3")
        
        r = requests.get(chosen_url, stream=True)
        if r.status_code == 200:
            with open(filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    f.write(chunk)
            
            # ELLENŐRZÉS
            files_in_folder = os.listdir(MUSIC_FOLDER)
            print(f"\n📂 Fájlok a mappában: {files_in_folder}")
            
            if len(files_in_folder) == 1:
                print("✅ SIKER! Csak 1 db fájl töltődött le.")
            else:
                print(f"❌ HIBA! {len(files_in_folder)} fájl van a mappában 1 helyett.")
                
        else:
            print(f"❌ HIBA: HTTP Státusz {r.status_code}")
            
    except Exception as e:
        print(f"❌ KIVÉTEL HIBA: {e}")

if __name__ == "__main__":
    download_one_random_music()