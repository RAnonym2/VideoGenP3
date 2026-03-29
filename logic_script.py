import os
import re
from generators import generate_text

def clean_script_text(text):
    text = re.sub(r'\*\*|__', '', text)
    text = re.sub(r'\*|_', '', text)
    text = re.sub(r'^#+\s.*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^(Intro|Hook|Chapter \d+|Segment|Conclusion|Outro|Narrator|Part \d+):\s*', '', text, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r'\(.*?\)', '', text)
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'\n\s*\n', '\n\n', text).strip()
    return text

def generate_long_script():
    title_path = "GENERATED_CONTENT/TEXT/title.txt"
    if os.path.exists(title_path):
        with open(title_path, "r", encoding="utf-8") as f:
            title_content = f.read().strip()
    else:
        title_content = "The Universe" # Példa cím

    # --- SYSTEM PROMPT: PONTOSAN AZ EREDETI ---
    system_prompt = """
    You are the Lead Writer for a high-quality educational channel (like 'Vox', 'Kurzgesagt', or 'Lemmino').
    
    YOUR GOAL: 
    Write a deep, engaging, and structured script based on the provided title.
    
    LENGTH CONSTRAINT (CRITICAL):
    - Target Word Count: ~1100 words. 
    - ABSOLUTE LIMIT: Do NOT exceed 1300 words. It is better to be concise and dense than long and repetitive.
    - If you find yourself repeating ideas just to fill space: STOP.
    
    STYLE GUIDELINES:
    1. UNIVERSAL STRUCTURE: Adopt a narrative structure that fits the specific topic (whether it's history, physics, or biology).
    2. CONTINUOUS FLOW: The output must be raw text for voiceover. No headers, no bold text, no labels.
    3. DEPTH OVER FLUFF: Do not use filler words. Explain the 'Why' and 'How' with concrete examples.
    """

    # --- USER PROMPT ALAP: PONTOSAN AZ EREDETI ---
    base_prompt = f"""
    Write a complete spoken narrative script for the video title: "{title_content}"

    STRICT LENGTH CONTROL: Aim for exactly 1100 words. Do not go over 1300.

    USE THIS FLEXIBLE NARRATIVE ARC (Do not label the sections, just follow the flow):

    1. THE HOOK (approx 150 words): 
        Start with the most interesting fact, a misconception, or a direct question that creates an "Open Loop" in the viewer's mind. Why should they care about this *right now*?

    2. THE CONTEXT, THE BACKGROUND (approx 250 words): 
        Set the stage. If it's history, what led to this event? If it's science, what was the prevailing theory before? If it's a phenomenon, where do we see it? 
        (Focus on the "Before" state).

    3. THE CORE MECHANISM, THE DEEP DIVE (approx 300 words): 
        This is the meat of the script. Explain the main concept in detail. 
        - Use an analogy if the topic is complex.
        - Tell the story of the discovery or the event.
        - Focus on the "How" and "What".

    4. THE BROADER IMPLICATIONS (approx 200 words): 
        Why does this matter? How does this affect the modern world, the future, or our understanding of reality? Connect the specific topic to a bigger picture.

    5. CONCLUSION (approx 150 words): 
        Summarize the journey briefly and end with a final, thought-provoking statement (a "mic drop" moment).

      - End with a quick, punchy sentence asking for a subscription if they want more.
    REMINDER: 
    - Output must be one continuous stream of text. NO MARKDOWN.
    - Stop writing if you have covered the topic fully; do not force length if it hurts quality.
    """
    
    output_file = "GENERATED_CONTENT/TEXT/script.txt"
    base_max_words = 1400
    max_retries = 8  # Biztonsági okokból maximum 5-ször próbálja újra
    attempt = 0
    base_temp = 0.7
    last_word_count = 0
    
    print(f"--- Generating Script for: {title_content} ---")
    
    while attempt < max_retries:
        attempt += 1
        
        # Minden próbálkozásnál levonunk 30 szót a maximumból
        # 1. kör: 1400, 2. kör: 1370, 3. kör: 1340...
        current_max_words = base_max_words - ((attempt - 1) * 30)
        
        print(f"--- Attempt {attempt}/{max_retries} (Max words allowed: {current_max_words}) ---")
        
        # A prompt módosítása CSAK HA már újra kell generálni
        current_prompt = base_prompt
        if attempt > 1:
            current_prompt += f"\n\nCRITICAL INSTRUCTION FOR RETRY: Your previous attempt was exactly {last_word_count} words, which is TOO LONG. You MUST cut down the text this time. Be more concise and do not exceed {current_max_words} words!"
        
        # A hőmérséklet pici növelése minden körben, hogy eltérő szöveget adjon (0.7 -> 0.75 -> 0.8...)
        current_temp = base_temp + (attempt * 0.05)
        
        # Generálás
        generate_text(current_prompt, file_name=output_file, temperature=current_temp, system=system_prompt)
        
        # Utófeldolgozás
        if os.path.exists(output_file):
            with open(output_file, "r", encoding="utf-8") as f:
                raw_script = f.read()
                
            clean_script = clean_script_text(raw_script)
            words = clean_script.split()
            word_count = len(words)
            last_word_count = word_count # Eltároljuk a hosszt, hogy be tudjuk írni a következő figyelmeztetésbe
            print(f"--- Generated Word Count: {word_count} ---")

            if word_count <= 1500:
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(clean_script)
                print(f"✅ Script elfogadva és elmentve: {output_file}")
                break
            else:
                print(f"⚠️ A script túl hosszú ({word_count} szó, limit: {1500}). Újragenerálás rákényszerítve...")
                if attempt == max_retries:
                    print("❌ Max próbálkozás elérve. A legutóbbit mentjük.")
                    with open(output_file, "w", encoding="utf-8") as f:
                        f.write(clean_script)

def clean_text(text): 
    text = text.strip() 
    text = re.sub(r'\s+', ' ', text)
    return text

def generate_short_script():
    title_path = "GENERATED_CONTENT/TEXT/title.txt"
    with open(title_path, 'r', encoding='utf-8') as f:
        title_content = f.read().strip()
    
    system_prompt = """You are a captivating Storyteller for viral Shorts (TikTok, YT Shorts). 
Your output will be converted directly to Text-to-Speech audio, so the text must be perfectly clean.

CRITICAL RULES:
1. NO MARKDOWN: Do not use bold (**), italics, headers, or bullet points. Write in plain text only.
2. NO VISUALS: Do not include visual cues in brackets (e.g., [Show image]). Write ONLY the spoken words.
3. NO LABELS: Do not write "Hook:" or "Outro:". Just the raw narrative.
4. STYLE: High-energy, conversational, and direct (Grade 6 reading level). No fluff.
"""

    prompt = f"""
Write a high-energy script strictly between 80-110 words based on this title: "{title_content}"

STRUCTURE:
1. THE HOOK (First 5s): Start instantly with a shocking statement or question to grab attention.
2. THE PAYOFF: Dive straight into the story or facts. Use transition words to keep the flow continuous. Explain WHY this is interesting.
3. THE OUTRO: A quick, punchy sentence asking for a subscription.

Remember: Output ONLY the spoken words ready for audio generation.
"""
    
    generate_text(
        prompt, 
        file_name="GENERATED_CONTENT/TEXT/script.txt", 
        temperature=0.8, 
        system=system_prompt
    )
