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


def subsequence_dtw(query, reference):
    """
    True Subsequence DTW (Open-Begin-End DTW).
    Mencari sub-sequence terbaik di reference yang cocok dengan query.
    Sangat akurat untuk matching humming yang hanya di bagian reff/chorus.
    """
    n, m = len(query), len(reference)
    if n == 0 or m == 0:
        return float('inf')

    # Jika query lebih panjang dari reference, lakukan DTW standar
    if n >= m:
        return compute_dtw(query, reference)

    # Inisialisasi cost matrix dengan infinity
    dtw = np.full((n + 1, m + 1), np.inf)
    
    # Baris pertama = 0 (membolehkan pencocokan mulai dari indeks mana saja di reference)
    dtw[0, :] = 0
    dtw[0, 0] = 0

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = abs(query[i - 1] - reference[j - 1])
            dtw[i, j] = cost + min(
                dtw[i - 1, j],      # insertion (skip di query)
                dtw[i, j - 1],      # deletion (skip di reference)
                dtw[i - 1, j - 1]   # match
            )

    # Ambil nilai minimum dari baris terakhir (titik akhir pencocokan terbaik)
    min_dist = np.min(dtw[n, 1:])
    
    # Normalisasi jarak dengan membaginya dengan panjang query
    return min_dist / n


def distance_to_confidence(distance, max_distance=8.0):
    """
    Convert DTW distance ke confidence percentage.
    distance=0 → 100%, distance>=max_distance → 0%
    """
    if distance >= max_distance:
        return 0.0
    return max(0.0, (1 - distance / max_distance) * 100)


def match_all(humming_intervals, database, top_n=5):
    """
    Compare humming melody ke semua lagu di database.
    Return top N matches sorted by confidence.
    """
    if len(humming_intervals) < 3:
        return []

    results = []
    for song in database:
        song_intervals = song.get('intervals', [])
        if len(song_intervals) < 3:
            continue

        dist = subsequence_dtw(humming_intervals, song_intervals)
        confidence = distance_to_confidence(dist)

        results.append({
            'title': song['title'],
            'artist': song['artist'],
            'confidence': round(confidence, 1),
            'distance': round(dist, 4),
            'filename': song.get('filename', '')
        })

    # Sort by confidence (highest first)
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
