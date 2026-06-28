"""
Preprocessor batch process semua MP3 di folder songs/
Extract melody dari setiap lagu, simpan ke data/songs.json
"""

import os
import json
import time
import subprocess
from .pitch_detector import detect_pitch_from_file
from .melody_extractor import extract_melody, smooth_melody


def separate_vocals(filepath):
    """
    Gunakan Demucs CLI untuk memisahkan vokal dari musik.
    Return path ke file vokal (.wav) yang dihasilkan.
    """
    filename = os.path.basename(filepath)
    name = os.path.splitext(filename)[0]
    
    separated_dir = 'separated'
    vocal_path = os.path.join(separated_dir, 'htdemucs', name, 'vocals.wav')
    
    # Jika sudah pernah diproses sebelumnya, langsung pakai
    if os.path.exists(vocal_path):
        print(f"Vokal terisolasi ditemukan: {vocal_path}")
        return vocal_path
        
    print(f"Memisahkan vokal menggunakan Demucs CLI...")
    
    # demucs --two-stems=vocals memisahkan menjadi vokal + accompaniment
    cmd = ["demucs", "--two-stems=vocals", "-o", separated_dir, filepath]
    
    try:
        # Jalankan secara terpisah (stdout/stderr di-mute agar log tidak berantakan)
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if os.path.exists(vocal_path):
            print(f"Vokal berhasil dipisahkan: {vocal_path}")
            return vocal_path
    except Exception as e:
        print(f"Demucs gagal dijalankan: {e}. Menggunakan audio asli.")
    
    return filepath


def process_song(filepath):
    """Process satu file MP3, return melody data."""
    filename = os.path.basename(filepath)
    # Parse nama file jadi title & artist 
    name = os.path.splitext(filename)[0]
    parts = name.rsplit('-', 1)
    title = parts[0].replace('-', ' ').title()
    artist = parts[1].replace('-', ' ').title() if len(parts) > 1 else 'Unknown'

    print(f"\n[Processing] {title} - {artist}")
    start = time.time()

    # Step 0: Pisahkan vokal terlebih dahulu menggunakan Demucs jika terinstal
    process_path = separate_vocals(filepath)

    # Step 1: Detect pitch menggunakan audio hasil pemisahan (atau audio asli jika gagal)
    pitch_result = detect_pitch_from_file(process_path)

    # Step 2: Extract & clean melody (threshold diturunkan agar lebih banyak nada terdeteksi)
    melody = extract_melody(
        pitch_result['frequencies'],
        pitch_result['confidences'],
        confidence_threshold=0.3
    )

    # Step 3: Smooth buat ngilangin glitch
    if len(melody['notes']) > 3:
        smoothed = smooth_melody(melody['notes'])
        
        # Hapus consecutive duplicates lagi setelah smoothing agar tidak ada selisih nol (interval=0)
        cleaned = [smoothed[0]]
        for note in smoothed[1:]:
            if note != cleaned[-1]:
                cleaned.append(note)
        melody['notes'] = cleaned
        
        # Recalculate intervals setelah smoothing & pembersihan ulang
        melody['intervals'] = []
        for i in range(1, len(melody['notes'])):
            melody['intervals'].append(melody['notes'][i] - melody['notes'][i - 1])
        from .pitch_detector import midi_to_note_name
        melody['note_names'] = [midi_to_note_name(n) for n in melody['notes']]

    elapsed = time.time() - start
    print(f"  Notes extracted: {len(melody['notes'])} | Time: {elapsed:.1f}s")

    return {
        'id': name,
        'title': title,
        'artist': artist,
        'filename': filename,
        'notes': melody['notes'],
        'intervals': melody['intervals'],
        'note_names': melody['note_names'],
        'num_notes': len(melody['notes'])
    }


def process_all_songs(songs_dir='songs', output_path='data/songs.json'):
    """Scan folder songs/, process semua MP3, simpan ke songs.json"""
    if not os.path.exists(songs_dir):
        print(f"Folder '{songs_dir}' gak ketemu!")
        return []

    mp3_files = sorted([f for f in os.listdir(songs_dir) if f.endswith('.mp3')])
    if not mp3_files:
        print(f"Gak ada file MP3 di '{songs_dir}/'")
        return []

    print(f"Found {len(mp3_files)} songs to process")
    print("=" * 50)

    database = []
    for i, filename in enumerate(mp3_files, 1):
        filepath = os.path.join(songs_dir, filename)
        print(f"\n[{i}/{len(mp3_files)}]", end="")
        
        try:
            song_data = process_song(filepath)
            if song_data['num_notes'] > 0:
                database.append(song_data)
            else:
                print(f"  [SKIP] No melody detected")
        except Exception as e:
            print(f"  [ERROR] {e}")

    # Simpan ke JSON
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(database, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 50)
    print(f"Done! {len(database)}/{len(mp3_files)} songs processed")
    print(f"Database saved to: {output_path}")

    return database


if __name__ == "__main__":
    process_all_songs()
