import os
import pickle
import random
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from PIL import Image, ImageDraw, ImageFont

# Saját modulok
from generators import generate_text, generate_image_horizontal

# --- KONFIGURÁCIÓ ---
# A korábbi egyetlen YouTube jogosultság mellé bekerül a Spreadsheets jogosultság is
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/spreadsheets"
]
CLIENT_SECRETS_FILE = "client_secrets.json"
TOKEN_FILE = "token.pickle"

def get_authenticated_service():
    """Belépteti a felhasználót és visszaadja a YouTube service objektumot."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CLIENT_SECRETS_FILE):
                print("HIBA: Nincs client_secrets.json fájl! Töltsd le a Google Cloud Console-ból.")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open(TOKEN_FILE, "wb") as token:
            pickle.dump(creds, token)

    return build("youtube", "v3", credentials=creds)

def clean_text_formatting(text):
    """
    Kíméletlen tisztító funkció.
    Eltávolítja a markdown formázásokat, felesleges karaktereket 
    ÉS AZ AI-ra UTALÓ JELEKET (Stealth Mode).
    """
    replacements = {
        "**": "",   # Bold
        "##": "",   # Header
        "__": "",   # Italic
        "Title:": "",
        "Description:": "",
        "Hook:": "",
        "Caption:": "",
        "Intro:": "", 
        "Outro:": "", 
        "Body:": "",
        "[": "",
        "]": "",
        "#ai": "",       # TILTOTT
        "#AI": "",       # TILTOTT
        "#chatgpt": "",  # TILTOTT
        "#ChatGPT": "",  # TILTOTT
        "AI generated": "",
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)

    # Szöveges AI említések cseréje semlegesre (Case Insensitive megoldás egyszerűsítve)
    forbidden_terms = ["artificial intelligence", "language model", "chatgpt", "ai", "#ai"]
    for term in forbidden_terms:
        # Ha kisbetűsítve benne van, cseréljük az eredetit
        if term in text.lower():
            # Ez egy egyszerű csere, feltételezve a kisbetűs egyezést. 
            # Robusztusabb lenne regexszel, de ez is megteszi a legtöbb esetben.
            text = text.replace(term, "modern science") 
            text = text.replace(term.title(), "Modern Science")
            text = text.replace(term.upper(), "MODERN SCIENCE")

    # Extra tisztítás: üres sorok és felesleges szóközök
    lines = [line.strip() for line in text.split("\n") if line.strip() != ""]
    return "\n\n".join(lines).strip()

def generate_metadata(title, script_content):
    """
    Generál:
    1. SEO optimalizált leírást (Formázásmentes, AI-említés nélkül)
    2. Tageket (Rejtett AI kulcsszavak nélkül)
    3. Thumbnail SZÖVEGET
    4. Thumbnail VIZUÁLIS LEÍRÁST
    """
    print("--- 🚀 YouTube Metadata Generálás (Anti-AI Stealth Mode) ---")
    
    # ---------------------------------------------------------
    # 1. DESCRIPTION (SEO & Story, NO AI, NO Lists)
    # ---------------------------------------------------------
    desc_system = """You are a professional YouTube Strategist. 
CRITICAL RULES:
1. NO MARKDOWN: Do not use bold (**), italics, or headers. Plain text only.
2. NO TIMESTAMPS: Do not include 0:00 or similar timestamps.
3. NO LISTS: Do not write "Key takeaways" or bullet points. Write in full paragraphs.
4. STRICT BAN: NEVER mention 'AI', 'Artificial Intelligence', 'ChatGPT', 'Generated', or 'Midjourney'. Act as if a human wrote this.
5. NO META-LABELS: Do not write "Here is the description:" or "Hook:".
"""
    
    desc_prompt = f"""
    Write a highly engaging, SEO-optimized YouTube video description for:
    VIDEO TITLE: "{title}"
    SCRIPT SNIPPET: "{script_content[:600]}..."
    STRUCTURE:
    - Paragraph 1 (The Hook): A punchy opening sentence to grab attention.
    - Paragraph 2 (The Value): A natural summary of the video's topic. Weave keywords into sentences naturally (e.g. Space, Physics). Do NOT list them.
    - Paragraph 3 (CTA): A short sentence asking to subscribe.
    - Hashtags: End with exactly 3 relevant hashtags (e.g. #Space #Science).

    TONE: Mysterious, exciting, human-like.
    LENGTH: Short and punchy (under 150 words).
    """
    generate_text(desc_prompt, "GENERATED_CONTENT/TEXT/description.txt", 0.7, desc_system)
    
    # Beolvasás és extra tisztítás Pythonnal
    desc_raw = open("GENERATED_CONTENT/TEXT/description.txt", "r", encoding="utf-8").read()
    description = clean_text_formatting(desc_raw)

    # ---------------------------------------------------------
    # 2. TAGS (High Search Volume, NO AI tags)
    # ---------------------------------------------------------
    tags_system = "You are a YouTube SEO Expert. You create high-volume search tags."
    tags_prompt = f"""
    Generate 20 high-performing tags for a video titled "{title}".
    
    RULES:
    - Comma-separated list ONLY.
    - NO AI TAGS: Do not use #AI, #ChatGPT, #ArtificialIntelligence.
    - Focus on the TOPIC (e.g., Space, History, Mystery).
    """
    generate_text(tags_prompt, "GENERATED_CONTENT/TEXT/tags.txt", 0.5, tags_system)
    tags_raw = open("GENERATED_CONTENT/TEXT/tags.txt", "r", encoding="utf-8").read()
    
    # Tisztítás és extra védelem a YouTube limitek miatt
    # 1. Kicseréljük az új sorokat vesszőkre, és eltüntetjük a felesleges idézőjeleket
    tags_raw = tags_raw.replace('\n', ',').replace('"', '').replace("'", "")
    
    # 2. Alap tisztítás a te függvényeddel
    tags_clean = clean_text_formatting(tags_raw)
    tags_list = [t.strip() for t in tags_clean.split(',')]
    
    final_tags = []
    total_chars = 0
    
    for t in tags_list:
        t_lower = t.lower()
        # Ha nem üres a tag, és nincs benne tiltott szó
        if t and "ai" not in t_lower and "chatgpt" not in t_lower:
            # YouTube nem enged < > karaktereket a tagekben, és a # jelet is érdemes levenni róluk
            clean_tag = t.replace('<', '').replace('>', '').replace('#', '')
            
            # YouTube szabály: a tagek összesített hossza szigorúan max 500 karakter lehet.
            # Biztonsági okokból 450 karakternél elvágjuk.
            if total_chars + len(clean_tag) + 1 <= 450: 
                final_tags.append(clean_tag)
                total_chars += len(clean_tag) + 1

    tags = final_tags

    # ---------------------------------------------------------
    # 3. THUMBNAIL TEXT (Short & Punchy)
    # ---------------------------------------------------------
    thumb_text_system = "You are a Viral Marketing Psychologist."
    thumb_text_prompt = f"""
    Create a text overlay for a thumbnail for: "{title}".
    RULES:
    - MAX 3 WORDS.
    - SHOCKING or MYSTERIOUS.
    - NO AI mentions.
    - Output ONLY the text.
    """
    generate_text(thumb_text_prompt, "GENERATED_CONTENT/TEXT/thumb_text.txt", 0.85, thumb_text_system)
    thumb_text = open("GENERATED_CONTENT/TEXT/thumb_text.txt", "r", encoding="utf-8").read().strip().replace('"', '')

    # ---------------------------------------------------------
    # 4. THUMBNAIL VISUAL PROMPT
    # ---------------------------------------------------------
    visual_system = "You are a cinematic Art Director."
    visual_prompt = f"""
    Write a text-to-image prompt for: "{title}".
    STYLE: Photorealistic, 8k, dramatic lighting, cinematic composition.
    NO TEXT: Do not ask for text inside the image.
    NO AI ROBOTS: Do not visualize AI concepts. Visualize the topic itself (e.g. space, nature).
    Output: A single descriptive sentence.
    """
    generate_text(visual_prompt, "GENERATED_CONTENT/TEXT/thumb_visual.txt", 0.8, visual_system)
    thumb_visual_prompt = open("GENERATED_CONTENT/TEXT/thumb_visual.txt", "r", encoding="utf-8").read().strip()

    return description, tags, thumb_text, thumb_visual_prompt

def create_thumbnail(thumb_text, thumb_visual_prompt, output_path="GENERATED_CONTENT/IMAGE/thumbnail.jpg"):
    """
    1. Legenerálja a képet a 'thumb_visual_prompt' alapján.
    2. Ráírja a 'thumb_text'-et.
    """
    print(f"--- Thumbnail Készítés ---")
    print(f"   🖼️ Visual: {thumb_visual_prompt}")
    print(f"   🔤 Text: {thumb_text}")
    
    # 1. Kép generálása
    final_image_prompt = f"{thumb_visual_prompt}, hyper-realistic, 8k, dramatic lighting, youtube thumbnail background"
    generate_image_horizontal(final_image_prompt, output_path)
    
    if not os.path.exists(output_path):
        print("Hiba: Thumbnail kép generálás sikertelen.")
        return None

    # 2. Szöveg ráírása (Pillow)
    try:
        img = Image.open(output_path).convert("RGB")
        draw = ImageDraw.Draw(img)
        
        # Font betöltése
        font_path = "FONT/BebasNeue-Regular.ttf"
        
        # Dinamikus betűméret
        width, height = img.size
        font_size = int(height * 0.25)
        
        try:
            font = ImageFont.truetype(font_path, font_size)
        except:
            print("Warning: BebasNeue font not found, using default.")
            font = ImageFont.load_default()

        # Méretezés, ha túl széles
        while draw.textbbox((0, 0), thumb_text, font=font)[2] > width * 0.9:
            font_size -= 10
            try: font = ImageFont.truetype(font_path, font_size)
            except: break
            if font_size < 20: break

        # Pozicionálás (Közép)
        text_bbox = draw.textbbox((0, 0), thumb_text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        x = (width - text_width) / 2
        y = (height - text_height) / 2

        # ERŐS KÖRVONAL (Outline)
        stroke_width = int(font_size * 0.05)
        
        draw.text((x, y), thumb_text, font=font, fill="white", stroke_width=stroke_width, stroke_fill="black")
        
        img.save(output_path, "JPEG", quality=95)
        return output_path

    except Exception as e:
        print(f"Thumbnail feliratozási hiba: {e}")
        return output_path

def upload_video_to_youtube(video_path, title, description, tags, category_id="27", privacy_status="public", thumbnail_path=None):
    """
    Feltölti a videót és a thumbnailt.
    """
    youtube = get_authenticated_service()
    if not youtube:
        return False

    print(f"--- Feltöltés indítása: {title} ---")
    
    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags,
            "categoryId": category_id
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False
        }
    }

    # Videó feltöltés
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Feltöltés: {int(status.progress() * 100)}%")

    video_id = response.get("id")
    print(f"✅ Videó feltöltve! ID: {video_id}")
    print(f"🔗 Link: https://youtu.be/{video_id}")

    # Thumbnail feltöltés
    if thumbnail_path and os.path.exists(thumbnail_path):
        print("Thumbnail feltöltése...")
        try:
            request = youtube.thumbnails().set(videoId=video_id, media_body=MediaFileUpload(thumbnail_path))
            request.execute()
            print("✅ Thumbnail beállítva.")
        except Exception as e:
            print(f"Thumbnail upload hiba: {e}")

    return True