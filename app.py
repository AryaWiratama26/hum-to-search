import os
import io
import numpy as np

# Load .env secara manual untuk membaca FFMPEG_PATH
env_path = '.env'
if os.path.exists(env_path):
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, val = line.split('=', 1)
                os.environ[key.strip()] = val.strip()

ffmpeg_bin = os.environ.get("FFMPEG_PATH")
if ffmpeg_bin and os.path.exists(ffmpeg_bin) and ffmpeg_bin not in os.environ["PATH"]:
    os.environ["PATH"] = ffmpeg_bin + os.path.pathsep + os.environ["PATH"]

import librosa
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from core.preprocessor import process_all_songs
from core.pitch_detector import detect_pitch_from_array, SAMPLE_RATE
from core.melody_extractor import extract_melody
from core.dtw_matcher import match_all, load_database

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

DATABASE_PATH = 'data/songs.json'
SONGS_DIR = 'songs'


@app.route('/')
def index():
    return send_from_directory('static', 'index.html')


@app.route('/api/preprocess', methods=['POST'])
def preprocess():
    """Process semua MP3 di folder songs/ dan simpan ke database."""
    try:
        database = process_all_songs(SONGS_DIR, DATABASE_PATH)
        return jsonify({
            'status': 'ok',
            'count': len(database),
            'songs': [{'title': s['title'], 'artist': s['artist'], 'notes': s['num_notes']} for s in database]
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/match', methods=['POST'])
def match():
    """Terima audio dari browser, extract melody, cocokkan ke database."""
    if 'audio' not in request.files:
        return jsonify({'status': 'error', 'message': 'No audio file'}), 400

    try:
        db = load_database(DATABASE_PATH)
    except FileNotFoundError:
        return jsonify({'status': 'error', 'message': 'Database belum ada. Process songs dulu.'}), 400

    try:
        audio_file = request.files['audio']
        
        # Simpan ke temp file dulu agar librosa bisa load dengan aman
        temp_path = os.path.join('uploads', 'temp_humming.wav')
        audio_file.save(temp_path)

        # Decode audio pakai librosa
        y, sr = librosa.load(temp_path, sr=SAMPLE_RATE)
        
        # Hapus temp file setelah di-load
        if os.path.exists(temp_path):
            os.remove(temp_path)

        # Detect pitch
        pitch_result = detect_pitch_from_array(y, sr)

        # Extract melody
        melody = extract_melody(
            pitch_result['frequencies'],
            pitch_result['confidences'],
            confidence_threshold=0.3  # lebih rendah buat humming (suara lebih pelan)
        )

        if len(melody['intervals']) < 3:
            return jsonify({
                'status': 'error',
                'message': 'Melody terlalu pendek. Coba humming lebih lama (5-10 detik).'
            }), 400

        # Match
        results = match_all(melody['intervals'], db, top_n=5)

        return jsonify({
            'status': 'ok',
            'melody_length': len(melody['notes']),
            'results': results
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/songs', methods=['GET'])
def list_songs():
    """List lagu di database."""
    try:
        db = load_database(DATABASE_PATH)
        return jsonify({
            'status': 'ok',
            'count': len(db),
            'songs': [{'title': s['title'], 'artist': s['artist'], 'notes': s['num_notes']} for s in db]
        })
    except FileNotFoundError:
        return jsonify({'status': 'ok', 'count': 0, 'songs': []})


@app.route('/api/status', methods=['GET'])
def status():
    """Cek apakah database sudah ada."""
    has_db = os.path.exists(DATABASE_PATH)
    mp3_count = len([f for f in os.listdir(SONGS_DIR) if f.endswith('.mp3')]) if os.path.exists(SONGS_DIR) else 0
    return jsonify({'has_database': has_db, 'mp3_count': mp3_count})


if __name__ == '__main__':
    os.makedirs('data', exist_ok=True)
    os.makedirs('uploads', exist_ok=True)
    app.run(debug=True, port=5000)
