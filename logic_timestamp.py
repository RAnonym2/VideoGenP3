import whisper

def format_timestamp_srt(seconds):
    ms = int((seconds - int(seconds)) * 1000)
    seconds = int(seconds)
    minutes = seconds // 60
    hours = minutes // 60
    minutes = minutes % 60
    seconds = seconds % 60
    return f"{hours:02}:{minutes:02}:{seconds:02},{ms:03}"

def split_segment_to_max_words(segment, max_words=7):
    """
    Feldarabolja a hosszú szegmenseket kisebbekre.
    Az időbélyegeket arányosan elosztja a szavak száma alapján, így a szinkron megmarad.
    """
    text = segment['text'].strip()
    words = text.split()
    
    # Ha eleve rövid a mondat, nem nyúlunk hozzá
    if len(words) <= max_words:
        return [segment]
        
    duration = segment['end'] - segment['start']
    time_per_word = duration / len(words)
    
    split_segments = []
    for i in range(0, len(words), max_words):
        chunk_words = words[i:i + max_words]
        chunk_start = segment['start'] + (i * time_per_word)
        chunk_end = chunk_start + (len(chunk_words) * time_per_word)
        
        split_segments.append({
            "start": chunk_start,
            "end": chunk_end,
            "text": " ".join(chunk_words)
        })
        
    return split_segments

def generate_srt_file(segments, output_filename="GENERATED_CONTENT/TTS/subtitles.srt"):
    # 1. Lépés: Szegmensek finomítása, hogy maximum 7 szavasak legyenek
    refined_segments = []
    for seg in segments:
        refined_segments.extend(split_segment_to_max_words(seg, max_words=7))

    # 2. Lépés: SRT fájl generálása az új, darabolt szegmensekből
    with open(output_filename, "w", encoding="utf-8") as f:
        for i, segment in enumerate(refined_segments, start=1):
            start_time = format_timestamp_srt(segment['start'])
            end_time = format_timestamp_srt(segment['end'])
            text = segment['text'].strip()
            
            f.write(f"{i}\n")
            f.write(f"{start_time} --> {end_time}\n")
            f.write(f"{text}\n\n")
            
    print(f"Subtitle file saved: {output_filename}")

def get_timestamps_from_audio(audio_file):
    model = whisper.load_model("base")
    result = model.transcribe(audio_file)    
    return result["segments"]

def group_segments_by_time(segments, target_duration):
    grouped_chunks = []
    current_text = ""
    current_start = segments[0]['start'] 
    
    for seg in segments:
        # Kisebb javítás: Hozzáadtam egy szóközt, hogy az egymás mellé fűzött szegmenseknél ne tapadjanak egybe a szavak
        current_text += seg['text'] + " "
        
        if (seg['end'] - current_start) >= target_duration:
            grouped_chunks.append({
                "start": current_start,
                "end": seg['end'],
                "text": current_text.strip(),
                "duration": seg['end'] - current_start
            })
            
            current_text = ""
            current_start = seg['end']
            
    if current_text.strip():
        last_end = segments[-1]['end']
        grouped_chunks.append({
            "start": current_start,
            "end": last_end,
            "text": current_text.strip(),
            "duration": last_end - current_start
        })
            
    return grouped_chunks