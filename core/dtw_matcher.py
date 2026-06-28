"""
DTW Matcher — Dynamic Time Warping untuk matching melody.
DTW bisa compare dua sequence yang beda tempo/kecepatan.
"""

import numpy as np
import json


def compute_dtw(seq1, seq2):
    """
    Hitung DTW distance antara 2 sequence.
    
    Bikin cost matrix (n x m), isi tiap cell dengan:
    cost[i][j] = |seq1[i] - seq2[j]| + min(cost kiri, atas, diagonal)
    
    Return: normalized distance (makin kecil = makin mirip)
    """
    n, m = len(seq1), len(seq2)
    if n == 0 or m == 0:
        return float('inf')

    # Init cost matrix dengan infinity
    dtw = np.full((n + 1, m + 1), np.inf)
    dtw[0][0] = 0

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = abs(seq1[i - 1] - seq2[j - 1])
            dtw[i][j] = cost + min(
                dtw[i - 1][j],      # atas (skip di seq1)
                dtw[i][j - 1],      # kiri (skip di seq2)
                dtw[i - 1][j - 1]   # diagonal (match)
            )

    # Normalize by path length biar fair antara lagu pendek & panjang
    return dtw[n][m] / (n + m)


def compute_dtw_normalized(seq1, seq2):
    """
    Hitung DTW distance antara dua sekuens yang sudah di-mean center.
    """
    n, m = len(seq1), len(seq2)
    dtw = np.full((n + 1, m + 1), np.inf)
    dtw[0, 0] = 0
    
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = abs(seq1[i - 1] - seq2[j - 1])
            dtw[i, j] = cost + min(
                dtw[i - 1, j],
                dtw[i, j - 1],
                dtw[i - 1, j - 1]
            )
            
    # Normalisasi dengan total panjang perbandingan
    return dtw[n, m] / (n + m)


def subsequence_dtw_normalized(query, reference):
    """
    Key-Normalized Subsequence DTW.
    Sangat kebal terhadap suara sumbang dan perbedaan kunci dasar (key).
    Mengatasi kelemahan pencocokan berbasis interval relatif.
    """
    n = len(query)
    m = len(reference)
    if n == 0 or m == 0:
        return float('inf')
        
    # Lakukan mean centering (normalisasi kunci dasar) pada query
    query_arr = np.array(query, dtype=float)
    query_centered = query_arr - np.mean(query_arr)
    
    best_dist = float('inf')
    
    # Coba beberapa ukuran window untuk toleransi tempo
    for scale in [0.8, 1.0, 1.2]:
        win_size = int(n * scale)
        if win_size < 3 or win_size > m:
            continue
            
        # Geser window sepanjang reference dengan step 1 untuk akurasi maksimal
        for start in range(0, m - win_size + 1):
            segment = np.array(reference[start:start + win_size], dtype=float)
            segment_centered = segment - np.mean(segment)
            
            dist = compute_dtw_normalized(query_centered, segment_centered)
            if dist < best_dist:
                best_dist = dist
                
    return best_dist


def distance_to_confidence(distance, max_distance=3.0):
    """
    Convert normalized mean-centered DTW distance ke confidence percentage.
    Makin dekat ke 0 → 100%, makin dekat ke max_distance → 0%
    """
    if distance >= max_distance:
        return 0.0
    return max(0.0, (1 - distance / max_distance) * 100)


def match_all(humming_notes, database, top_n=5):
    """
    Bandingkan sekuens nada humming (absolut MIDI) dengan lagu di database menggunakan Key-Normalized DTW.
    Return top N matches sorted by confidence.
    """
    if len(humming_notes) < 3:
        return []

    results = []
    for song in database:
        song_notes = song.get('notes', [])
        if len(song_notes) < 3:
            continue

        dist = subsequence_dtw_normalized(humming_notes, song_notes)
        confidence = distance_to_confidence(dist, max_distance=3.0)

        results.append({
            'title': song['title'],
            'artist': song['artist'],
            'confidence': round(confidence, 1),
            'distance': round(dist, 4),
            'filename': song.get('filename', '')
        })

    # Urutkan berdasarkan confidence tertinggi
    results.sort(key=lambda x: x['confidence'], reverse=True)
    return results[:top_n]


def load_database(path='data/songs.json'):
    """Load song database dari JSON file."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


if __name__ == "__main__":
    melody_a = [2, 2, 1, 2, 2, 2, 1]       # major scale (do re mi fa sol la si)
    melody_b = [2, 2, 1, 2, 2, 2, 1]       # identical
    melody_c = [2, 1, 2, 2, 1, 2, 2]       # minor scale (beda pattern)
    melody_d = [5, -3, 5, -3, 1, 1, -2]    # totally different melody

    print("DTW Tests:")
    dist_ab = compute_dtw(melody_a, melody_b)
    dist_ac = compute_dtw(melody_a, melody_c)
    dist_ad = compute_dtw(melody_a, melody_d)
    print(f"  A vs B (identical):  dist={dist_ab:.4f}  confidence={distance_to_confidence(dist_ab):.1f}%")
    print(f"  A vs C (minor key):  dist={dist_ac:.4f}  confidence={distance_to_confidence(dist_ac):.1f}%")
    print(f"  A vs D (different):  dist={dist_ad:.4f}  confidence={distance_to_confidence(dist_ad):.1f}%")
