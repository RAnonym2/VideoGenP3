import os
import random
import requests
from moviepy import *
from moviepy.video.tools.subtitles import SubtitlesClip

# --- KONFIGURÁCIÓ ---
# ZOOM: 1.1-ről indul és 1.25-ig megy.
# Így SOHA nem lesz kisebb a kép a képernyőnél, nincs fekete káva.
ZOOM_MIN = 1.10
ZOOM_MAX = 1.25 
FADE_DURATION = 0.4
MUSIC_VOLUME = 0.15

# ZENE LISTA
MUSIC_URLS = [
    "https://drive.google.com/file/d/1ENHhoBnMBAxDblwa0e24tYOKLlXU-9qi/view?usp=drive_link",
    "https://drive.google.com/file/d/1YQcZse2rwvahnPjINv5HHXmGsaEEFRd1/view?usp=drive_link"
]

def _get_one_random_music(music_folder):
    """Zene kiválasztása vagy letöltése."""
    if not os.path.exists(music_folder):
        os.makedirs(music_folder)

    existing_files = [f for f in os.listdir(music_folder) if f.endswith(('.mp3', '.wav'))]
    if existing_files:
        chosen = random.choice(existing_files)
        print(f"   ♫ Lokális zene kiválasztva: {chosen}")
        return os.path.join(music_folder, chosen)

    print(f"--- Zene letöltése ---")
    if not MUSIC_URLS: return None

    chosen_url = random.choice(MUSIC_URLS)
    try:
        if "drive.google.com" in chosen_url:
            file_id = chosen_url.split("/d/")[1].split("/")[0]
            chosen_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        
        filename = os.path.join(music_folder, "downloaded_music.mp3")
        print(f"⬇️ Letöltés indul: {chosen_url}")
        
        r = requests.get(chosen_url, stream=True)
        if r.status_code == 200:
            with open(filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    f.write(chunk)
            print("✅ Letöltés kész.")
            return filename
    except Exception as e:
        print(f"❌ Kivétel hiba a zene letöltésnél: {e}")
        return None
    return None

def _create_zooming_clip(image_path, duration, index, target_size):
    """
    Létrehoz egy klippet, ami garantáltan kitölti a target_size-t,
    és a dobozon BELÜL zoomol (Cookie Cutter módszer).
    target_size: (width, height) tuple
    """
    w, h = target_size
    
    # 1. Alap kép betöltése
    img_clip = ImageClip(image_path).with_duration(duration).with_fps(24)

    # 2. Kezdeti méretezés: A kép töltse ki a képernyőt teljesen (cover)
    ratio_img = img_clip.w / img_clip.h
    ratio_target = w / h

    if ratio_img > ratio_target:
        # A kép szélesebb -> Magasságra igazítunk
        img_clip = img_clip.with_effects([vfx.Resize(height=h)])
    else:
        # A kép magasabb -> Szélességre igazítunk
        img_clip = img_clip.with_effects([vfx.Resize(width=w)])
    
    # ZOOM logika
    zoom_diff = ZOOM_MAX - ZOOM_MIN

    if index % 2 == 0:
        # ZOOM IN: 1.1x -> 1.25x
        zoom_func = lambda t: ZOOM_MIN + (zoom_diff * (t / duration))
    else:
        # ZOOM OUT: 1.25x -> 1.1x
        zoom_func = lambda t: ZOOM_MAX - (zoom_diff * (t / duration))

    # Nagyítjuk a képet, de...
    zooming_clip = img_clip.with_effects([vfx.Resize(zoom_func)]).with_position('center')

    # ...levágjuk a kilógó részeket a CompositeVideoClip méretével
    final_clip = CompositeVideoClip([zooming_clip], size=target_size)
    
    return final_clip

def _add_background_music(video_clip, original_audio, music_folder):
    music_path = _get_one_random_music(music_folder)

    if not music_path or not os.path.exists(music_path):
        print("WARNING: Nem sikerült zenét szerezni, marad a néma háttér.")
        return video_clip

    try:
        music_clip = AudioFileClip(music_path)
        if music_clip.duration < video_clip.duration:
            loops = int(video_clip.duration / music_clip.duration) + 2
            music_clip = concatenate_audioclips([music_clip] * loops)

        music_clip = music_clip.with_duration(video_clip.duration)
        music_clip = music_clip.with_volume_scaled(MUSIC_VOLUME)
        music_clip = music_clip.with_effects([afx.AudioFadeIn(2.0), afx.AudioFadeOut(2.0)])

        final_audio = CompositeAudioClip([original_audio, music_clip])
        return video_clip.with_audio(final_audio)
    except Exception as e:
        print(f"Music mix error: {e}")
        return video_clip

def create_long_video(audio_path, visual_data, srt_path, output_path, music_folder="MUSIC"):
    FONT_PATH = "FONT/BebasNeue-Regular.ttf"
    TARGET_SIZE = (1920, 1080)

    try:
        audio_clip = AudioFileClip(audio_path)
        clips = []

        for i, item in enumerate(visual_data):
            if not item.get('image_path'): continue
            clip_duration = item['duration'] + FADE_DURATION
            clip = _create_zooming_clip(item['image_path'], clip_duration, i, TARGET_SIZE)
            clip = clip.with_effects([vfx.CrossFadeIn(FADE_DURATION)])
            clips.append(clip)

        if not clips: return False

        base_video = concatenate_videoclips(clips, method="compose", padding=-FADE_DURATION)
        base_video = base_video.with_audio(audio_clip).with_duration(audio_clip.duration)
        base_video = _add_background_music(base_video, audio_clip, music_folder)

        if os.path.exists(srt_path):
            # JAVÍTÁS: 'text_align' használata 'align' helyett
            generator = lambda txt: TextClip(
                text=txt, font=FONT_PATH, font_size=80, color='white', 
                method='caption', size=(1900, 200), text_align='center' 
            )
            subtitles = SubtitlesClip(srt_path, make_textclip=generator)
            
            subtitles = subtitles.with_position(('center', 0.85), relative=True).with_duration(base_video.duration)
            final_video = CompositeVideoClip([base_video, subtitles])
        else:
            final_video = base_video

        final_video.write_videofile(output_path, fps=24, threads=4, preset='medium', logger='bar')
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def create_short_video(audio_path, visual_data, srt_path, output_path, music_folder="MUSIC"):
    FONT_PATH = "FONT/BebasNeue-Regular.ttf"
    TARGET_SIZE = (1080, 1920)

    try:
        audio_clip = AudioFileClip(audio_path)
        clips = []

        for i, item in enumerate(visual_data):
            if not item.get('image_path'): continue
            clip_duration = item['duration'] + FADE_DURATION
            clip = _create_zooming_clip(item['image_path'], clip_duration, i, TARGET_SIZE)
            clip = clip.with_effects([vfx.CrossFadeIn(FADE_DURATION)])
            clips.append(clip)

        if not clips: return False

        base_video = concatenate_videoclips(clips, method="compose", padding=-FADE_DURATION)
        base_video = base_video.with_audio(audio_clip).with_duration(audio_clip.duration)
        base_video = _add_background_music(base_video, audio_clip, music_folder)

        if os.path.exists(srt_path):
            # JAVÍTÁS: 'text_align' használata 'align' helyett
            generator = lambda txt: TextClip(
                text=txt, font=FONT_PATH, font_size=55, color='yellow', 
                method='caption', size=(1000, 180), text_align='center'
            )
            subtitles = SubtitlesClip(srt_path, make_textclip=generator)

            subtitles = subtitles.with_position(('center', 0.80), relative=True).with_duration(base_video.duration)
            
            final_video = CompositeVideoClip([base_video, subtitles])
        else:
            final_video = base_video

        final_video.write_videofile(output_path, fps=24, threads=4, preset='medium', logger='bar')
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False