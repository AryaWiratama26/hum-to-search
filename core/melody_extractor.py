"""
Melody extractor — bersihin raw pitch jadi clean melody sequence.
"""

import numpy as np
from .pitch_detector import frequency_to_midi


def extract_melody(frequencies, confidences, confidence_threshold=0.5):
    """
    Convert raw pitch array jadi clean melody.
    
    Steps:
    1. Buang frame dengan confidence rendah (noise/silence)
    2. Convert frequency -> MIDI note
    3. Quantize ke nearest semitone (bulatkan)
    4. Hapus consecutive duplicates (kita cuma peduli pitch sequence, bukan durasi)
    5. Hitung intervals (selisih antar note)
    
    Returns dict: notes (MIDI numbers), intervals (selisih), note_names
    """
    midi_raw = []
    
    for freq, conf in zip(frequencies, confidences):
        if np.isnan(freq) or conf < confidence_threshold:
            continue
        midi = frequency_to_midi(freq)
        if not np.isnan(midi):
            midi_raw.append(midi)
    
    if len(midi_raw) == 0:
        return {'notes': [], 'intervals': [], 'note_names': []}
    
    # Quantize ke nearest semitone
    quantized = [int(round(m)) for m in midi_raw]
    
    # Hapus consecutive duplicates
    # [60, 60, 60, 62, 62, 64] -> [60, 62, 64]
    cleaned = [quantized[0]]
    for note in quantized[1:]:
        if note != cleaned[-1]:
            cleaned.append(note)
    
    # Hitung intervals — ini yang dipakai buat matching
    # Key-independent: orang humming di nada berapapun tetap cocok
    intervals = []
    for i in range(1, len(cleaned)):
        intervals.append(cleaned[i] - cleaned[i - 1])
    
    # Note names buat debugging
    from .pitch_detector import midi_to_note_name
    names = [midi_to_note_name(n) for n in cleaned]
    
    return {
        'notes': cleaned,
        'intervals': intervals,
        'note_names': names
    }


def smooth_melody(notes, window=3):
    """
    Median filter buat ngilangin outlier/glitch.
    Window=3 artinya tiap note di-compare sama 1 tetangga kiri & kanan.
    """
    if len(notes) < window:
        return notes
    
    arr = np.array(notes, dtype=float)
    smoothed = np.copy(arr)
    half = window // 2
    
    for i in range(half, len(arr) - half):
        smoothed[i] = np.median(arr[i - half:i + half + 1])
    
    return [int(round(x)) for x in smoothed]


if __name__ == "__main__":
    # Simulasi: do re mi fa sol la si do
    fake_freqs = np.array([261.63, 261.63, 293.66, 293.66, 329.63, 
                           349.23, 349.23, 392.00, 440.00, 493.88, 523.25])
    fake_confs = np.ones(len(fake_freqs))  # semua confidence = 1.0
    
    result = extract_melody(fake_freqs, fake_confs)
    print("Notes:", result['note_names'])
    print("MIDI:", result['notes'])
    print("Intervals:", result['intervals'])
