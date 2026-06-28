const recorder = new AudioRecorder();
const visualizer = new Visualizer(document.getElementById('waveform'));
visualizer.drawIdle();

// Elements
const btnRecord = document.getElementById('btn-record');
const recordStatus = document.getElementById('record-status');
const recordTimer = document.getElementById('record-timer');
const resultsDiv = document.getElementById('results');
const resultsList = document.getElementById('results-list');
const noDbWarning = document.getElementById('no-db-warning');
const btnProcess = document.getElementById('btn-process');
const processStatus = document.getElementById('process-status');
const songList = document.getElementById('song-list');
const mp3Count = document.getElementById('mp3-count');
const tabs = document.querySelectorAll('.tab');

let timerInterval = null;
let seconds = 0;

// Tab switching
tabs.forEach(tab => {
    tab.addEventListener('click', () => {
        tabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
        document.getElementById('panel-' + tab.dataset.tab).classList.add('active');
    });
});

// Check status on load
checkStatus();

async function checkStatus() {
    try {
        const res = await fetch('/api/status');
        const data = await res.json();
        mp3Count.textContent = data.mp3_count + ' file MP3 ditemukan di songs/';

        if (!data.has_database) {
            noDbWarning.classList.remove('hidden');
        } else {
            noDbWarning.classList.add('hidden');
            loadSongs();
        }
    } catch (e) {
        console.error(e);
    }
}

// Record
btnRecord.addEventListener('click', async () => {
    if (!recorder.isRecording) {
        await startRecording();
    } else {
        await stopRecording();
    }
});

async function startRecording() {
    resultsDiv.classList.add('hidden');
    await recorder.start();

    btnRecord.classList.add('recording');
    btnRecord.innerHTML = '<i class="ph ph-stop"></i>';
    recordStatus.textContent = 'humming sekarang...';

    visualizer.start(recorder.getAnalyser());

    seconds = 0;
    recordTimer.textContent = '0:00';
    timerInterval = setInterval(() => {
        seconds++;
        const m = Math.floor(seconds / 60);
        const s = (seconds % 60).toString().padStart(2, '0');
        recordTimer.textContent = m + ':' + s;
    }, 1000);
}

async function stopRecording() {
    clearInterval(timerInterval);
    visualizer.stop();

    btnRecord.classList.remove('recording');
    btnRecord.innerHTML = '<i class="ph ph-microphone"></i>';
    recordStatus.textContent = 'menganalisis...';
    recordTimer.textContent = '';

    const blob = await recorder.stop();
    await sendForMatching(blob);
}

async function sendForMatching(blob) {
    const formData = new FormData();
    formData.append('audio', blob, 'humming.wav');

    try {
        const res = await fetch('/api/match', { method: 'POST', body: formData });
        const data = await res.json();

        if (data.status === 'ok') {
            showResults(data.results);
            recordStatus.textContent = data.melody_length + ' nada terdeteksi';
        } else {
            recordStatus.textContent = data.message;
        }
    } catch (e) {
        recordStatus.textContent = 'gagal menghubungi server';
        console.error(e);
    }
}

function showResults(results) {
    resultsList.innerHTML = '';

    if (results.length === 0) {
        resultsList.innerHTML = '<p class="status-text">tidak ditemukan</p>';
        resultsDiv.classList.remove('hidden');
        return;
    }

    results.forEach((r, i) => {
        const card = document.createElement('div');
        card.className = 'result-card';
        card.innerHTML = `
            <div class="result-info">
                <span class="result-title">${r.title}</span>
                <span class="result-artist">${r.artist}</span>
            </div>
            <span class="result-score">${r.confidence}%</span>
        `;
        resultsList.appendChild(card);
    });

    resultsDiv.classList.remove('hidden');
}

// Process songs
btnProcess.addEventListener('click', async () => {
    btnProcess.disabled = true;
    processStatus.textContent = 'processing... ini bisa makan waktu beberapa menit';

    try {
        const res = await fetch('/api/preprocess', { method: 'POST' });
        const data = await res.json();

        if (data.status === 'ok') {
            processStatus.textContent = data.count + ' lagu berhasil diproses';
            noDbWarning.classList.add('hidden');
            showSongList(data.songs);
        } else {
            processStatus.textContent = 'error: ' + data.message;
        }
    } catch (e) {
        processStatus.textContent = 'gagal menghubungi server';
    }

    btnProcess.disabled = false;
});

async function loadSongs() {
    try {
        const res = await fetch('/api/songs');
        const data = await res.json();
        if (data.count > 0) showSongList(data.songs);
    } catch (e) {
        console.error(e);
    }
}

function showSongList(songs) {
    songList.innerHTML = '';
    songs.forEach(s => {
        const item = document.createElement('div');
        item.className = 'song-item';
        item.innerHTML = `
            <span class="song-item-title">${s.title} — ${s.artist}</span>
            <span class="song-item-notes">${s.notes} notes</span>
        `;
        songList.appendChild(item);
    });
}
