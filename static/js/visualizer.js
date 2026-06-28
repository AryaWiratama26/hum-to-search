class Visualizer {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.animationId = null;
        this.resize();
        window.addEventListener('resize', () => this.resize());
    }

    resize() {
        const rect = this.canvas.getBoundingClientRect();
        this.canvas.width = rect.width * window.devicePixelRatio;
        this.canvas.height = rect.height * window.devicePixelRatio;
        this.ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
        this.width = rect.width;
        this.height = rect.height;
    }

    start(analyser) {
        this.analyser = analyser;
        this.bufferLength = analyser.frequencyBinCount;
        this.dataArray = new Uint8Array(this.bufferLength);
        this.draw();
    }

    draw() {
        this.animationId = requestAnimationFrame(() => this.draw());
        this.analyser.getByteTimeDomainData(this.dataArray);

        const ctx = this.ctx;
        ctx.clearRect(0, 0, this.width, this.height);

        ctx.lineWidth = 1.5;
        ctx.strokeStyle = '#fff';
        ctx.beginPath();

        const sliceWidth = this.width / this.bufferLength;
        let x = 0;

        for (let i = 0; i < this.bufferLength; i++) {
            const v = this.dataArray[i] / 128.0;
            const y = (v * this.height) / 2;

            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
            x += sliceWidth;
        }

        ctx.lineTo(this.width, this.height / 2);
        ctx.stroke();
    }

    stop() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
            this.animationId = null;
        }
        this.drawIdle();
    }

    drawIdle() {
        const ctx = this.ctx;
        ctx.clearRect(0, 0, this.width, this.height);
        ctx.strokeStyle = '#222';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(0, this.height / 2);
        ctx.lineTo(this.width, this.height / 2);
        ctx.stroke();
    }
}
