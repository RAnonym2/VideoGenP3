from generators import generate_text
import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# --- KONFIGURÁCIÓ ---
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/spreadsheets"
]
CLIENT_SECRETS_FILE = "client_secrets.json"
TOKEN_FILE = "token.pickle"

# A TE GOOGLE TÁBLÁZATOD AZONOSÍTÓJA:
SPREADSHEET_ID = "1a6aHkll2o7Jp-3K9YcPEyomZRXJGJsp-E1K8Ds9YGxA"
RANGE_NAME = "A2:A" # Az 'A' oszlopot olvassa és írja, a fejlécet (A1) kihagyva

def get_authenticated_service():
    """Belépteti a felhasználót és visszaadja a Google API service objektumot."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CLIENT_SECRETS_FILE):
                print("HIBA: Nincs client_secrets.json fájl!")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open(TOKEN_FILE, "wb") as token:
            pickle.dump(creds, token)

    return build("sheets", "v4", credentials=creds)

def get_used_titles(service):
    """Lekéri a már használt címeket a Google Táblázatból."""
    try:
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
        values = result.get('values', [])
        
        if not values:
            return ""
        
        titles = [row[0] for row in values if row]
        return "\n".join(titles)
    except Exception as e:
        print(f"⚠️ Hiba a Google Táblázat olvasásakor: {e}")
        return None

def append_title_to_sheet(service, title):
    """Hozzáfűzi az új címet a Google Táblázat végéhez."""
    try:
        sheet = service.spreadsheets()
        body = {'values': [[title]]}
        sheet.values().append(
            spreadsheetId=SPREADSHEET_ID, 
            range=RANGE_NAME, 
            valueInputOption="USER_ENTERED", 
            body=body
        ).execute()
        print("✅ Új cím sikeresen feltöltve a Google Táblázathoz!")
    except Exception as e:
        print(f"⚠️ Hiba a Google Táblázatba íráskor: {e}")

def generate_title():
    used_titles_path = "SCRIPTS/used_titles.txt"
    os.makedirs(os.path.dirname(used_titles_path), exist_ok=True)

    print("--- 1. Google Táblázat szinkronizálása a TXT fájlba ---")
    service = get_authenticated_service()
    
    # Kiolvassuk a Spreadsheetből a címeket
    if service:
        cloud_titles = get_used_titles(service)
        if cloud_titles is not None:
            # --- ÚJ RÉSZ: Kiprinteljük a felhőből érkező címeket ---
            print("\n--- Jelenleg használt címek a Google Táblázatból ---")
            if cloud_titles.strip():
                print(cloud_titles)
            else:
                print("Még nincs mentett cím a táblázatban.")
            print("----------------------------------------------------\n")

            # Megcsináljuk/Felülírjuk a TXT fájlt a Spreadsheet adatokkal
            with open(used_titles_path, "w", encoding="utf-8") as f:
                if cloud_titles.strip():
                    f.write(cloud_titles + "\n")
            print("✅ Helyi TXT fájl felépítve a Spreadsheet alapján.")
    else:
        print("⚠️ Nem sikerült kapcsolódni a felhőhöz, az eddigi TXT-t próbáljuk használni.")

    # Ezt a TXT-t használjuk a promptban (és máshol a rendszeredben)
    if os.path.exists(used_titles_path):
        with open(used_titles_path, "r", encoding="utf-8") as f:
            used_titles_content = f.read().strip()
    else:
        used_titles_content = ""

    # --- SYSTEM PROMPT ---
    system_prompt = """You are a Science Editor for a channel focused on Astrophysics and Cosmology. Your goal is to write titles that appeal to intellectual curiosity about physics and reality.

    SYSTEM INTEGRITY PROTOCOLS:
    1. NO Markdown formatting.
    2. NO quotation marks, emojis, or special symbols.
    3. NO conversational filler.
    4. Output MUST be a single line of text only.
    5. Prioritize "The Mystery" or "The Impossible" aspects of physics.
    6. MAXIMUM LENGTH: 75 characters. Keep it short and punchy.
    """

    # --- USER PROMPT ---
    base_prompt = f"""
    TASK: Generate a single, scientifically grounded YouTube title about The Universe.

    STYLE GUIDE (Scientific vs Philosophical):
    - BAD: "Does The Universe Care About Us?" OR "Why You Are Made of Stardust"
    - GOOD: "The Star That Is Older Than The Universe" OR "What Happens If You Fall Into a Magnetar?"
    
    INSTRUCTIONS:
    1. Focus on specific anomalies, paradoxes, extreme physics, or cosmic horror.
    2. Use concrete terms like: Black Hole, Vacuum Decay, Light Speed, Entropy, Dark Energy, Iron Stars.
    3. The title must promise a specific explanation of a physical phenomenon, not a feeling.
    4. STRICT LENGTH LIMIT: The title MUST be extremely concise, UNDER 75 characters in total length.

    NEGATIVE CONSTRAINTS:
    - Do not use questions about "Meaning of Life" or "Consciousness".
    - Do not be poetic. Be dramatic but factual.
    - Ensure the title is completely different from these previously used titles:
    ---
    {used_titles_content}
    ---

    Generate the single raw title line now.
    """

    output_file = "GENERATED_CONTENT/TEXT/title.txt"
    max_retries = 10
    attempt = 0
    base_temp = 0.85
    last_char_count = 0
    current_title = ""

    print("--- 2. Generating Title ---")

    while attempt < max_retries:
        attempt += 1
        print(f"--- Title Attempt {attempt}/{max_retries} ---")
        
        current_prompt = base_prompt
        if attempt > 1:
            current_prompt += f"\n\nCRITICAL INSTRUCTION FOR RETRY: Your previous attempt was {last_char_count} characters, which is TOO LONG. You MUST cut down the text this time. Do not exceed 75 characters!"
        
        current_temp = base_temp + (attempt * 0.02)
        generate_text(current_prompt, file_name=output_file, temperature=current_temp, system=system_prompt)
        
        if os.path.exists(output_file):
            with open(output_file, "r", encoding="utf-8") as f:
                raw_title = f.read().strip()
                raw_title = raw_title.replace('"', '').replace("'", "")
            
            last_char_count = len(raw_title)
            print(f"--- Generated Title Length: {last_char_count} characters ---")

            if last_char_count <= 75:
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(raw_title)
                print(f"✅ Title elfogadva és elmentve: {raw_title}")
                current_title = raw_title
                break
            else:
                print(f"⚠️ A cím túl hosszú ({last_char_count} karakter, limit: 75). Újragenerálás rákényszerítve...")
                if attempt == max_retries:
                    print("❌ Max próbálkozás elérve. A legutóbbit Python vágja el az utolsó értelmes szónál.")
                    cut_title = raw_title[:74]
                    if " " in cut_title:
                        cut_title = cut_title.rsplit(" ", 1)[0]
                    with open(output_file, "w", encoding="utf-8") as f:
                        f.write(cut_title)
                    current_title = cut_title
                    print(f"✅ Vágott Title elmentve: {current_title}")
                    break

    # --- 3. Új title feltöltése és hozzáírása a TXT-hez ---
    if current_title:
        # A) Beírjuk a helyi TXT-be
        with open(used_titles_path, "a", encoding="utf-8") as f:
            f.write(current_title + "\n")
        print(f"✅ Új cím beleírva a lokális {used_titles_path} fájlba.")
        
        # B) Feltöltjük a Spreadsheetre
        if service:
            append_title_to_sheet(service, current_title)