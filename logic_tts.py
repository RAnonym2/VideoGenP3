from generators import generate_tts

tts_file = "GENERATED_CONTENT/TEXT/generated_TEXT/script.txt"
tts_content = open(tts_file).read()

generate_tts(tts_content, file_name="GENERATED_CONTENT/TTS/script.mp3")