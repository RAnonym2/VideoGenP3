import os
from generators import generate_text, generate_image_horizontal, generate_image_vertical
import re

def clean_text_for_url(text):
    """
    Ez a függvény eltünteti a "gyilkos" karaktereket.
    1. A perjelet (/) kicseréli ' or '-ra, hogy ne törje el a webcímet.
    2. A sortöréseket és dupla szóközöket egyetlen szóközre cseréli.
    """
    # Kicseréljük a perjeleket (pl. "day/night" -> "day or night")
    text = text.replace("/", " or ")
    
    # Kicseréljük az egyéb veszélyes karaktereket is, ami bezavarhat a URL-be
    text = text.replace("\\", "")
    
    # Sortörések és felesleges szóközök takarítása
    text = text.strip()
    return re.sub(r'\s+', ' ', text)

def generate_prompts_for_chunks(chunks):
    # --- SPACE & UNIVERSE SYSTEM PROMPT (REVAMPED) ---
    raw_system = """
    You are the Senior Visual Director for a high-budget BBC or National Geographic space documentary.
    
    YOUR GOAL: 
    Translate script segments into varied, scientifically accurate, cinematic image prompts. 
    You must AVOID repetitive imagery. Every shot must feel distinct in scale, angle, and lighting.

    STRICT VISUAL RULES (The "NASA Aesthetic"):
    1. REALISM: No sci-fi fantasy art. No cartoon colors. Use "National Geographic" realism.
    2. LIGHTING: Harsh, unidirectional sunlight (high contrast). Deep distinct shadows (chiaroscuro).
    3. VARIETY STRATEGY (Must use different approaches):
       - MACRO: Close-ups of dust, ice crystals, chemical reactions, surface textures.
       - ORBITAL: Satellite views, horizons, atmospheric layers (nadir or oblique angles).
       - TELESCOPIC: Deep field, nebulae (James Webb style infrared), galaxies.
       - PHYSICS: Abstract representations of gravity, magnetic fields (using particles and distortion, not glowing lines).
    
    OUTPUT FORMAT: Return ONLY the raw prompt string.
    """
    
    system = clean_text_for_url(raw_system)
    
    temperature = 0.7 # Kicsit emeltem a kreativitás miatt, de a rendszer prompt korlátozza a hülyeséget
    print("--- Generating Varied Image Prompts ---")
    
    for i, chunk in enumerate(chunks):
        text_segment = chunk['text']

        # --- DYNAMIC USER PROMPT ---
        # Itt kényszerítjük rá a változatos kameraállásokat és skálákat
        raw_user_prompt = f"""
        SOURCE SCRIPT: "{text_segment}"
        
        TASK: Create a visually unique, photorealistic prompt for this specific moment.
        
        INSTRUCTIONS FOR VARIETY (Pick ONE specific visual approach based on the text):
        A) If talking about particles or atoms -> Use "MACRO PHOTOGRAPHY", shallow depth of field, tactile textures.
        B) If talking about planets or moons -> Use "ORBITAL CAM", "SATELLITE VIEW", or "LOW FLYBY". Focus on geology and atmosphere.
        C) If talking about universe or void -> Use "HUBBLE or JWST IMAGING", diffraction spikes, gravitational lensing, dense star fields.
        D) If talking about concepts (time or gravity) -> Use "OPTICAL DISTORTION", "LIGHT LEAKS", "INTERSTELLAR DUST SILHOUETTES".

        REQUIRED PROMPT STRUCTURE:
        [Subject] + [Camera Angle or Scale] + [Scientific Detail] + [Lighting or Atmosphere] + [Style Keywords]

        STYLE KEYWORDS TO MIX (Use 2-3): 
        "IMAX 70mm footage", "Electron microscope view", "False-color infrared", "Raw satellite capture", "Volumetric lighting", "Cinematic composition".

        Describe the image now (30-50 words):
        """

        user_prompt = clean_text_for_url(raw_user_prompt)

        temp_prompt_file = f"GENERATED_CONTENT/TEXT/temp_prompt_{i}.txt"
        
        generate_text(user_prompt, temp_prompt_file, temperature=temperature, system=system)

        if os.path.exists(temp_prompt_file):
            with open(temp_prompt_file, "r", encoding="utf-8") as f:
                image_prompt = f.read().strip()
            
            image_prompt = clean_text_for_url(image_prompt)
            
            if len(image_prompt) < 5 or "{" in image_prompt:
                 image_prompt = "Deep space photography, distant stars, high contrast, 8k nasa style."
            
            os.remove(temp_prompt_file)
        else:
            image_prompt = "Deep space photography, distant stars, high contrast, 8k nasa style."

        chunk['image_prompt'] = image_prompt
        print(f"   Frame {i}: {image_prompt[:50]}...")

    return chunks


def generate_images_from_chunks(chunks, mode, output_folder="GENERATED_CONTENT/IMAGE"):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    print(f"--- Generating Images ({mode}) ---")

    for i, chunk in enumerate(chunks):
        # Itt is biztosítjuk, hogy a kép promptja tiszta legyen
        raw_prompt = chunk.get('image_prompt', "space galaxy 8k")
        prompt = clean_text_for_url(raw_prompt) 
        
        filename = f"{output_folder}/image_{i:03}.png"
        
        if mode == "horizontal":
            generate_image_horizontal(prompt, filename)
        else:
            generate_image_vertical(prompt, filename)
            
        chunk['image_path'] = filename
        
    return chunks