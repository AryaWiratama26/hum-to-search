"""
Pitch detection pakai pYIN (Probabilistic YIN).

"""

import librosa
import numpy as np

# Range frekuensi vokal manusia untuk humming (dipertinggi agar mengabaikan bass gitar)
FMIN = 130      # Hz, batas bawah (sekitar C3)
FMAX = 800      # Hz, batas atas
SAMPLE_RATE = 22050
FRAME_LENGTH = 2048   # 93ms per frame
HOP_LENGTH = 1024     # Diperbesar dari 512 ke 1024 agar proses 2x lebih cepat


def detect_pitch_from_file(audio_path):
    """Load audio file lalu detect pitch. Return dict of frequencies, confidences, times."""
    print(f"  Loading: {audio_path}")
    y, sr = librosa.load(audio_path, sr=SAMPLE_RATE)
    print(f"  Duration: {len(y)/sr:.1f}s | Samples: {len(y):,}")
    return detect_pitch_from_array(y, sr)


def detect_pitch_from_array(audio_array, sr=SAMPLE_RATE):
    """Detect pitch dari numpy array. Dipakai buat preprocessing MP3 & real-time humming."""
    print(f"  Running pYIN...")
    
    # f0 = frequency per frame (NaN kalau gak ada pitch)
    # voiced_flag = boolean, True kalau ada vokal
    # voiced_probs = probability voiced (0-1)
    f0, voiced_flag, voiced_probs = librosa.pyin(
        audio_array,
        fmin=FMIN, fmax=FMAX,
        sr=sr,
        frame_length=FRAME_LENGTH,
        hop_length=HOP_LENGTH
    )
    
    times = librosa.times_like(f0, sr=sr, hop_length=HOP_LENGTH)
    
    valid = np.sum(~np.isnan(f0))
    total = len(f0)
    print(f"  Pitch detected: {valid}/{total} frames ({valid/total*100:.1f}%)")
    
    return {
        'frequencies': f0,
        'confidences': voiced_probs,
        'times': times,
        'sample_rate': sr
    }


def frequency_to_midi(freq):
    """
    Convert Hz ke MIDI note number.
    Formula: 69 + 12 * log2(freq / 440)
    A4 = 440Hz = MIDI 69, setiap oktaf = 12 semitone.
    """
    if freq <= 0 or np.isnan(freq):
        return np.nan
    return 69 + 12 * np.log2(freq / 440.0)


def midi_to_note_name(midi_number):
    """Convert MIDI number ke note name. Contoh: 60 -> C4, 69 -> A4"""
    if np.isnan(midi_number):
        return 'N/A'
    notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    midi_int = int(round(midi_number))
    return f"{notes[midi_int % 12]}{(midi_int // 12) - 1}"


if __name__ == "__main__":
    # Quick test frequency conversion
    test_freqs = [261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88, 523.25]
    print("Freq -> MIDI -> Note:")
    for freq in test_freqs:
        midi = frequency_to_midi(freq)
        print(f"  {freq:.2f} Hz -> MIDI {midi:.1f} -> {midi_to_note_name(midi)}")

    # Test dengan file MP3
    import os
    songs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'songs')
    if os.path.exists(songs_dir):
        mp3s = [f for f in os.listdir(songs_dir) if f.endswith('.mp3')]
        if mp3s:
            print(f"\nTesting: {mp3s[0]}")
            result = detect_pitch_from_file(os.path.join(songs_dir, mp3s[0]))
            
            # Filter: ambil pitch yang > FMIN (skip bass/noise di batas bawah)
            freqs = result['frequencies']
            valid = freqs[~np.isnan(freqs) & (freqs > FMIN + 10)]
            print(f"  Valid vocal pitches: {len(valid)}")
            
            # Ambil 15 sample dari tengah lagu (biasanya ada vokal)
            if len(valid) > 15:
                mid = len(valid) // 2
                samples = valid[mid - 7:mid + 8]
            else:
                samples = valid[:15]
            
            print(f"\n  Sample pitches (from middle):")
            for f in samples:
                midi = frequency_to_midi(f)
                print(f"  {f:.1f} Hz -> {midi_to_note_name(midi)}")
