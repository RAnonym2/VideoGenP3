import os
import requests
import re
import urllib.parse

# Kivesszük a fix kulcsokat, és a környezeti változóból olvassuk be
keys_env = os.environ.get("POLLINATIONS_API_KEYS")
API_KEYS = [k.strip() for k in keys_env.split(",")]


def generate_text(prompt, file_name, temperature, system):
    url = "https://gen.pollinations.ai/v1/chat/completions"
    
    for key in API_KEYS:
        try:
            # Structure the payload in the standard OpenAI Chat Completions format
            payload = { #openai
                "model": "openai",
                "temperature": temperature,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt}
                ]
            }
            
            r = requests.post(
                url,
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json"
                },
                json=payload
            )

            if r.status_code == 200:
                # The response is a JSON object, so we extract just the text content
                response_json = r.json()
                generated_text = response_json["choices"][0]["message"]["content"]
                
                with open(file_name, "w", encoding="utf-8") as f:
                    f.write(generated_text)
                return

            elif r.status_code == 402:
                continue

            else:
                print(f"❌ ERROR RECEIVED")
                print(f"Status Code: {r.status_code}")
                print(f"Response Text: {r.text}")
                break

        except Exception as e:
            print("🚨 Request Exception:", str(e))
            break


def generate_image_horizontal(prompt, file_name):
    url = f"https://gen.pollinations.ai/image/{prompt}"
    for key in API_KEYS: # klein-large # gptimage #grok-gptimage-large
        r = requests.get(url, headers={"Authorization": f"Bearer {key}"}, params={"model": "gptimage", "width": 1920, "height": 1080, "safe": True})
        if r.status_code == 200:
            with open(file_name, "wb") as f: f.write(r.content)
            return
        elif r.status_code == 402: continue
        else: break

def generate_image_vertical(prompt, file_name):
    url = f"https://gen.pollinations.ai/image/{prompt}"
    for key in API_KEYS: # klein-large # gptimage #grok-imagine
        r = requests.get(url, headers={"Authorization": f"Bearer {key}"}, params={"model": "gptimage", "width": 1080, "height": 1920, "safe": True})
        if r.status_code == 200:
            with open(file_name, "wb") as f: f.write(r.content)
            return
        elif r.status_code == 402: continue
        else: break



def smart_split_text(text, max_chars=700):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current_chunk = ""
    for sentence in sentences:
        if len(current_chunk) + len(sentence) > max_chars:
            if current_chunk: chunks.append(current_chunk.strip())
            current_chunk = sentence
        else: current_chunk += " " + sentence
    if current_chunk: chunks.append(current_chunk.strip())
    return chunks

def generate_tts(full_text, file_name):
    chunks = smart_split_text(full_text)
    temp_files = []

    for i, chunk in enumerate(chunks):
        temp_file = f"temp_tts_{i}.mp3"
        chunk_success = False

        payload = {
            "model": "qwen3-tts",
            "voice": "echo",
            "input": chunk,
            "style": "cinematic deep space documentary, dark mysterious cosmic tone, scientific storytelling, immersive and atmospheric",

"instructions": """Speak in a deep, calm, and authoritative voice, like a high-end space documentary narrator. 
Your tone should feel vast, mysterious, and intellectually captivating, as if explaining the secrets of the universe itself.

Use slow pacing with intentional pauses to create suspense and awe. Emphasize key scientific terms such as 'black hole', 'event horizon', 'singularity', and 'spacetime' with subtle intensity.

Your delivery should feel immersive and slightly ominous, as if the listener is drifting through space while uncovering profound cosmic truths.

Avoid sounding robotic or overly emotional. Instead, balance scientific clarity with a sense of wonder and existential depth.

Let silence and pacing enhance the scale of the universe. Each sentence should feel meaningful, as if revealing something ancient and powerful.

Overall style: cinematic, intelligent, mysterious, and awe-inspiring."""
}

        for key in API_KEYS:
            # 1. JAVÍTÁS: Hozzáadjuk a kulcsot az URL-hez (?key=...)
            url = f"https://gen.pollinations.ai/v1/audio/speech?key={key}"
            
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json"
            }
            
            try:
                r = requests.post(url, headers=headers, json=payload)
                
                if r.status_code == 200:
                    with open(temp_file, "wb") as f:
                        f.write(r.content)
                    temp_files.append(temp_file)
                    chunk_success = True
                    break
                elif r.status_code == 402:
                    # Nincs elég kredit, próbáljuk a következő kulccsal
                    continue
                else:
                    print(f"Hiba a {i}. chunknál (Status: {r.status_code}): {r.text}")
                    break # Ha nem 402-es hiba, lépjünk ki a kulcs-ciklusból, hogy lássuk a hibát
                    
            except Exception as e:
                print(f"Kivétel a {i}. chunknál:", str(e))
                continue

        if not chunk_success:
            print(f"Chunk {i} failed")

    if temp_files:
        with open(file_name, "wb") as outfile:
            for f_name in temp_files:
                with open(f_name, "rb") as infile:
                    outfile.write(infile.read())
                os.remove(f_name)
        return True

    return False
