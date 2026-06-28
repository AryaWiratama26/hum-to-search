# Hum to Search — Melody Matching Prototype

Aplikasi web sederhana untuk mencari dan mendeteksi judul lagu hanya dengan senandung (humming). Proyek ini dibangun menggunakan Python (Flask) untuk pengolahan audio di backend dan Vanilla HTML/CSS/JS di frontend.

Proyek ini sangat bagus untuk mempelajari konsep dasar Audio Signal Processing, Pitch Detection (pYIN), dan Dynamic Time Warping (DTW).

---

## Bagaimana Sistem Ini Bekerja?

Sistem ini terbagi menjadi dua fase utama:

### 1. Fase Preprocessing (Batch Processing MP3)
Sebelum aplikasi bisa mencocokkan senandung, sistem harus mempelajari melodi dari lagu-lagu asli (MP3) yang dimasukkan ke folder songs/.
```
[File MP3] -> [pYIN Algorithm] -> [Extract Notes & Intervals] -> [Simpan ke songs.json]
```
*   **Pitch Detection (pYIN)**: Menganalisis file audio MP3 dan mendeteksi frekuensi nada (Hz) yang dominan pada setiap frame waktu.
*   **Melody Extraction**: Frekuensi suara diubah menjadi format angka nada (MIDI Note Numbers).
*   **Interval Conversion**: Dibandingkan mencocokkan nada mutlak, kita menghitung selisih antar nada (Interval). Contoh: Nada C4 -> D4 -> E4 dikonversi menjadi interval [+2, +2]. Hal ini membuat sistem tetap akurat meskipun user bernyanyi dengan nada lebih rendah atau tinggi dari penyanyi aslinya.
*   **Database**: Hasil ekstraksi disimpan dalam file terstruktur di data/songs.json.

### 2. Fase Pencocokan (Real-time Matching)
Saat user bersenandung di depan microphone browser:
```
[Humming di Mic] -> [Audio WebM] -> [Kirim ke Flask API]
                                            │
                                            ▼
[Hasil Deteksi Lagu] <- [DTW Matcher] <- [Extract Notes & Intervals]
```
*   **Recording**: Browser merekam suara senandung user dan mengirimkannya ke Flask server.
*   **Matching (Dynamic Time Warping)**: Algoritma DTW membandingkan pola interval senandung dengan database lagu. DTW sangat fleksibel karena bisa mencocokkan melodi meskipun user bernyanyi lebih lambat atau lebih cepat (fleksibel terhadap tempo).
*   **Output**: Aplikasi mengembalikan 5 lagu dengan persentase kecocokan (confidence rate) tertinggi.

---

## Struktur Proyek

```
humming/
├── app.py                    # Flask server & API Endpoint
├── requirements.txt          # Dependensi Python
├── README.md                 # Dokumentasi proyek
├── core/                     # Logika pengolahan audio (Python)
│   ├── __init__.py           
│   ├── pitch_detector.py     # Deteksi frekuensi suara dengan pYIN
│   ├── melody_extractor.py   # Pembersihan nada & ekstraksi interval
│   ├── dtw_matcher.py        # Algoritma pencocokan Dynamic Time Warping
│   └── preprocessor.py       # Pemroses otomatis batch file MP3
├── data/
│   └── songs.json            # Database melodi hasil pre-process (output)
├── songs/                    # Tempat menaruh file MP3 lagu asli
└── static/                   # File UI Frontend (HTML/CSS/JS)
    ├── css/
    │   └── style.css         # Gaya tampilan minimalis gelap (dark mode)
    ├── js/
    │   ├── app.js            # Controller logika interaksi UI
    │   ├── recorder.js       # Perekam suara dari mic browser
    │   └── visualizer.js     # Visualisasi waveform gelombang suara
    └── index.html            # Tampilan utama web
```

---

## Panduan Instalasi & Penggunaan

### 1. Prasyarat (Prerequisites)
Pastikan Anda sudah menginstal Python 3.8 ke atas di komputer Anda.

### 2. Clone Repository & Setup Virtual Environment
```bash
# Clone proyek ini
git clone https://github.com/AryaWiratama26/hum-to-search.git
cd hum-to-search

# Buat virtual environment
python -m venv venv

# Aktifkan virtual environment (Windows)
.\venv\Scripts\activate

# Install dependensi
pip install -r requirements.txt
```

### 3. Masukkan Lagu & Jalankan Preprocessing
1. Buat folder songs/ (jika belum ada).
2. Taruh beberapa file lagu favorit Anda berformat .mp3 ke dalam folder songs/ tersebut. Beri nama file yang rapi seperti judul-artis.mp3 (Contoh: tujuh-belas-tulus.mp3).
3. Jalankan pembuat database melodi lewat terminal:
   ```bash
   python -m core.preprocessor
   ```
   *Tunggu beberapa menit hingga semua lagu selesai diproses dan menghasilkan file data/songs.json.*

### 4. Jalankan Aplikasi Web
```bash
python app.py
```
Buka browser Anda dan akses alamat: http://localhost:5000

### 5. Cara Mencari Lagu
1. Klik tombol Microphone di halaman web.
2. Izinkan akses microphone jika browser memintanya.
3. Mulailah bersenandung (humming / "hmmm-hmmm") melodi lagu pilihan Anda selama 5 hingga 10 detik.
4. Klik tombol Stop.
5. Sistem akan menganalisis melodi suara Anda dan menampilkan hasil tebakan lagunya beserta persentase kemiripannya!

---

## Teknologi yang Digunakan

*   **Librosa**: Pustaka Python utama untuk analisis musik dan audio.
*   **Flask**: Micro-framework Python untuk backend web server.
*   **Numpy & Scipy**: Penghitungan matriks matematika secara cepat untuk algoritma DTW.
*   **Web Audio API**: Perekaman audio real-time dan analisis frekuensi secara langsung di sisi client browser.
*   **Phosphor Icons**: CDN icon set minimalis untuk mempercantik UI.
