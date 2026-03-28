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
                "model": "openai-fast",
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


#def generate_text(prompt, file_name, temperature, system):
    # 1. LÉPÉS: Kódoljuk a promptot URL-barát formátumra
    # A .strip() leszedi a felesleges szóközt/entert az elejéről/végéről
    # A quote() átalakítja a speciális karaktereket (pl. szóköz -> %20)
#    encoded_prompt = urllib.parse.quote(prompt.strip())
    
    # 2. LÉPÉS: A kódolt szöveget illesztjük a URL-be
#    url = f"https://gen.pollinations.ai/text/{encoded_prompt}"
    
#    for key in API_KEYS:
#        try:
#            r = requests.get(
#                url,
#                headers={"Authorization": f"Bearer {key}"},
#                params={
#                    "model": "openai",
#                    "temperature": temperature,
#                    "system": system
#                }
#            )

#            if r.status_code == 200:
#                with open(file_name, "w", encoding="utf-8") as f:
#                    f.write(r.text)
#                return

#            elif r.status_code == 402:
#                continue

#            elif r.status_code == 404:
#                print("❌ 404 ERROR RECEIVED")
#                print("Status Code:", r.status_code)
#                print("URL (ellenőrizd, hogy nincs-e benne %0A az elején):", r.url)
#                print("Response Text:", r.text)
#                return

#            else:
#                print(f"⚠️ Unexpected error: {r.status_code}")
#                break

#        except Exception as e:
#            print("🚨 Request Exception:", str(e))
#            break


def generate_image_horizontal(prompt, file_name):
    url = f"https://gen.pollinations.ai/image/{prompt}"
    for key in API_KEYS: # klein-large # gptimage #grok-imagine
        r = requests.get(url, headers={"Authorization": f"Bearer {key}"}, params={"model": "zimage", "width": 1920, "height": 1080, "safe": True})
        if r.status_code == 200:
            with open(file_name, "wb") as f: f.write(r.content)
            return
        elif r.status_code == 402: continue
        else: break

def generate_image_vertical(prompt, file_name):
    url = f"https://gen.pollinations.ai/image/{prompt}"
    for key in API_KEYS: # klein-large # gptimage #grok-imagine
        r = requests.get(url, headers={"Authorization": f"Bearer {key}"}, params={"model": "zimage", "width": 1080, "height": 1920, "safe": True})
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
        encoded_prompt = urllib.parse.quote(chunk)
        temp_file = f"temp_tts_{i}.mp3"
        chunk_success = False

        for key in API_KEYS:
            url = f"https://gen.pollinations.ai/audio/{encoded_prompt}?model=whisper&voice=echo&key={key}"
            
            r = requests.get(url)
            
            if r.status_code == 200:
                with open(temp_file, "wb") as f:
                    f.write(r.content)
                temp_files.append(temp_file)
                chunk_success = True
                break
            elif r.status_code == 402:
                continue
            else:
                continue

        # opcionális: ha egy chunk nem sikerül
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
