import os
from logic_title import generate_title
from logic_script import generate_short_script
from generators import generate_tts
from logic_timestamp import get_timestamps_from_audio, generate_srt_file, group_segments_by_time
from logic_image import generate_prompts_for_chunks, generate_images_from_chunks
from logic_video import create_short_video
# ÚJ IMPORT:
from logic_youtube import generate_metadata, upload_video_to_youtube

TEXT_FILE = "GENERATED_CONTENT/TEXT/script.txt"
TITLE_FILE = "GENERATED_CONTENT/TEXT/title.txt"
AUDIO_FILE = "GENERATED_CONTENT/TTS/script.mp3"
SRT_FILE = "GENERATED_CONTENT/TTS/subtitles.srt"
IMAGE_FOLDER = "GENERATED_CONTENT/IMAGE"
FINAL_VIDEO = "GENERATED_CONTENT/VIDEO/short_video.mp4"
IMAGE_PACE = 6.0

paths = [
    "GENERATED_CONTENT/TEXT",
    "GENERATED_CONTENT/TTS",
    "GENERATED_CONTENT/IMAGE",
    "GENERATED_CONTENT/VIDEO",
    "SCRIPTS"
]
for path in paths:
    if not os.path.exists(path):
        os.makedirs(path)

# --- GENERÁLÁSI FOLYAMAT ---
generate_title()
generate_short_script()

if os.path.exists(TEXT_FILE):
    script_content = open(TEXT_FILE, encoding="utf-8").read()
    if not generate_tts(script_content, AUDIO_FILE):
        exit()
else:
    exit()

raw_segments = get_timestamps_from_audio(AUDIO_FILE)
generate_srt_file(raw_segments, SRT_FILE)

visual_chunks = group_segments_by_time(raw_segments, target_duration=IMAGE_PACE)
chunks_with_prompts = generate_prompts_for_chunks(visual_chunks)
final_data = generate_images_from_chunks(chunks_with_prompts, mode="vertical", output_folder=IMAGE_FOLDER)

# VIDEÓ KÉSZÍTÉSE
create_short_video(AUDIO_FILE, final_data, SRT_FILE, FINAL_VIDEO)

# --- YOUTUBE AUTOMATIZÁCIÓ (ÚJ RÉSZ) ---
if os.path.exists(FINAL_VIDEO):
    title_content = open(TITLE_FILE, encoding="utf-8").read().strip()
    
    # 1. Metaadatok generálása (Thumbnail kép itt nem kell, de a fv 4 értéket ad vissza)
    description, tags, _, _ = generate_metadata(title_content, script_content)
    
    # 2. Shorts optimalizálás (hashtag a címbe)
    short_title = f"{title_content} #shorts"
    short_description = f"{description}\n\n#shorts #fyp #viral"
    
    # 3. Feltöltés (thumbnail_path nélkül)
    upload_video_to_youtube(
        video_path=FINAL_VIDEO,
        title=short_title,
        description=short_description,
        tags=tags,
        privacy_status="public",
        thumbnail_path=None
    )
