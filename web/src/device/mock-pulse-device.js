// MockPulseDevice — drop-in stand-in for PulseSerialDevice.
//
// Mirrors the same interface (connect / disconnect / startCapture /
// stopCapture / isSupported) but never touches the Web Serial API.
// Generates a plausible PPG-shaped waveform at ~100 Hz so the UI flow
// (Connect → Start → progress → Done → submit) can be exercised end-to-end
// without real hardware. Useful for demos on Safari/Firefox and for testing
// from a dev machine that has no Arduino plugged in.

const log = (...args) => console.log('[device:mock]', ...args)

const SAMPLE_INTERVAL_MS = 10   // ~100 Hz, matches the Arduino sketch
const CONNECT_LATENCY_MS = 250  // simulated handshake

export class MockPulseDevice {
  static get isSupported() {
    return true
  }

  constructor() {
    this.connected = false
    this.capturing = false
    this._timer = null
    this._tick = 0
    this._sampleCount = 0
    this._captureStartedAt = 0
  }

  async connect({ baudRate = 115200 } = {}) {
    log('connect()', { baudRate })
    if (this.connected) {
      log('connect() skipped — already connected')
      return
    }
    await new Promise((r) => setTimeout(r, CONNECT_LATENCY_MS))
    this.connected = true
    log('connected (simulated)')
  }

  async disconnect() {
    log('disconnect()')
    await this.stopCapture()
    this.connected = false
  }

  async startCapture({ onSample, onError } = {}) {
    if (!this.connected) throw new Error('not connected')
    if (this.capturing) {
      log('startCapture() skipped — already capturing')
      return
    }
    this.capturing = true
    this._tick = 0
    this._sampleCount = 0
    this._captureStartedAt = performance.now()
    log('startCapture() — streaming simulated samples at ~100Hz')

    this._timer = setInterval(() => {
      if (!this.capturing) return
      try {
        // Synthetic PPG: ~72 bpm fundamental + dicrotic harmonic + noise,
        // mapped into the 0..1023 ADC range so the values look like the
        // real Arduino stream.
        const t = this._tick++ / 100  // seconds, given 100 Hz tick rate
        const beat = 0.6 * Math.sin(2 * Math.PI * 1.2 * t)
        const harmonic = 0.2 * Math.sin(2 * Math.PI * 2.4 * t + 0.5)
        const noise = 0.04 * (Math.random() - 0.5)
        // Centre ~512, swing ±~200, clamp to ADC range.
        let value = 512 + 320 * (beat + harmonic + noise)
        value = Math.max(0, Math.min(1023, Math.round(value)))

        this._sampleCount += 1
        if (this._sampleCount === 1 || this._sampleCount % 50 === 0) {
          const elapsed = (performance.now() - this._captureStartedAt) / 1000
          const rate = elapsed > 0 ? (this._sampleCount / elapsed).toFixed(1) : '–'
          log(`sample #${this._sampleCount} value=${value} elapsed=${elapsed.toFixed(2)}s rate=${rate}Hz`)
        }

        onSample?.(value)
      } catch (err) {
        onError?.(err)
      }
    }, SAMPLE_INTERVAL_MS)
  }

  async stopCapture() {
    if (!this.capturing) return
    const elapsed = (performance.now() - this._captureStartedAt) / 1000
    const rate = elapsed > 0 ? (this._sampleCount / elapsed).toFixed(1) : '–'
    log(`stopCapture() — produced ${this._sampleCount} samples in ${elapsed.toFixed(2)}s (≈${rate}Hz)`)
    this.capturing = false
    if (this._timer) {
      clearInterval(this._timer)
      this._timer = null
    }
  }
}
