class AudioRecorder {
    constructor() {
        this.stream = null;
        this.audioContext = null;
        this.scriptProcessor = null;
        this.analyser = null;
        this.isRecording = false;
        this.leftchannel = [];
        this.recordingLength = 0;
        this.sampleRate = 44100; // Will be set by AudioContext
    }

    async start() {
        this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        
        // Buat AudioContext
        const AudioContextClass = window.AudioContext || window.webkitAudioContext;
        this.audioContext = new AudioContextClass();
        this.sampleRate = this.audioContext.sampleRate;

        const source = this.audioContext.createMediaStreamSource(this.stream);

        // Analyser untuk visualisasi waveform
        this.analyser = this.audioContext.createAnalyser();
        this.analyser.fftSize = 2048;
        source.connect(this.analyser);

        // ScriptProcessor untuk mengambil raw PCM data
        // buffer size 4096, 1 input channel, 1 output channel
        this.scriptProcessor = this.audioContext.createScriptProcessor(4096, 1, 1);
        
        this.leftchannel = [];
        this.recordingLength = 0;

        this.scriptProcessor.onaudioprocess = (e) => {
            if (!this.isRecording) return;
            const left = e.inputBuffer.getChannelData(0);
            this.leftchannel.push(new Float32Array(left));
            this.recordingLength += left.length;
        };

        source.connect(this.scriptProcessor);
        this.scriptProcessor.connect(this.audioContext.destination);

        this.isRecording = true;
    }

    stop() {
        return new Promise((resolve) => {
            this.isRecording = false;

            if (this.scriptProcessor) {
                this.scriptProcessor.disconnect();
            }
            if (this.stream) {
                this.stream.getTracks().forEach(t => t.stop());
            }
            if (this.audioContext) {
                this.audioContext.close();
            }

            // Gabungkan semua buffer float array menjadi satu
            const samples = this.flattenBuffer(this.leftchannel, this.recordingLength);
            
            // Encode menjadi WAV (PCM 16-bit)
            const wavBuffer = this.encodeWAV(samples, this.sampleRate);
            const blob = new Blob([wavBuffer], { type: 'audio/wav' });
            
            resolve(blob);
        });
    }

    flattenBuffer(channelBuffer, recordingLength) {
        const result = new Float32Array(recordingLength);
        let offset = 0;
        for (let i = 0; i < channelBuffer.length; i++) {
            const buffer = channelBuffer[i];
            result.set(buffer, offset);
            offset += buffer.length;
        }
        return result;
    }

    encodeWAV(samples, sampleRate) {
        const buffer = new ArrayBuffer(44 + samples.length * 2);
        const view = new DataView(buffer);

        const writeString = (view, offset, string) => {
            for (let i = 0; i < string.length; i++) {
                view.setUint8(offset + i, string.charCodeAt(i));
            }
        };

        // RIFF identifier
        writeString(view, 0, 'RIFF');
        // File length
        view.setUint32(4, 36 + samples.length * 2, true);
        // RIFF type
        writeString(view, 8, 'WAVE');
        // Format chunk identifier
        writeString(view, 12, 'fmt ');
        // Format chunk length
        view.setUint32(16, 16, true);
        // Sample format (raw PCM = 1)
        view.setUint16(20, 1, true);
        // Channel count (1 = mono)
        view.setUint16(22, 1, true);
        // Sample rate
        view.setUint32(24, sampleRate, true);
        // Byte rate (sampleRate * blockAlign)
        view.setUint32(28, sampleRate * 2, true);
        // Block align (channels * bytes per sample = 1 * 2)
        view.setUint16(32, 2, true);
        // Bits per sample (16-bit)
        view.setUint16(34, 16, true);
        // Data chunk identifier
        writeString(view, 36, 'data');
        // Data chunk length
        view.setUint32(40, samples.length * 2, true);

        // Tulis samples PCM 16-bit
        let offset = 44;
        for (let i = 0; i < samples.length; i++, offset += 2) {
            let s = Math.max(-1, Math.min(1, samples[i]));
            view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
        }

        return buffer;
    }

    getAnalyser() {
        return this.analyser;
    }
}
