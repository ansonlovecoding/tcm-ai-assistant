// Pulse-sensor serial protocol
// -----------------------------
// Two firmware variants are supported on the same code path, distinguished
// per-line by the presence of a comma:
//
//   1. Legacy PulseSensor sketch — one integer per line:
//
//        int s = analogRead(A0);   // 0..1023
//        Serial.println(s);        // "123\r\n"
//
//   2. Extended sketch — six comma-separated values per line, in order:
//        raw_PPG, avg_PPG, filter_PPG, ppg_Peak, hr, hrv
//      i.e. raw ADC sample, smoothed PPG, band-pass-filtered PPG, peak flag,
//      heart rate (BPM) and HRV (SDNN, ms). Emitted by:
//
//        Serial.println(String(raw_PPG)    + "," +
//                       String(avg_PPG)    + "," +
//                       String(filter_PPG) + "," +
//                       String(ppg_Peak)   + "," +
//                       String(hr)         + "," +
//                       String(hrv));
//
// In both cases this module opens the port at 115200 8-N-1, decodes the
// byte stream as UTF-8, splits on newlines, and emits the raw PPG sample
// (first field) to `onSample`. For the extended variant the full record is
// also handed to an optional `onMetrics` callback. There are no commands to
// send — data starts flowing as soon as the port opens.
//
// Requires the Web Serial API (Chrome/Edge over https:// or http://localhost).

// Filter all device logs in DevTools by searching for "[device]".
const log = (...args) => console.log('[device]', ...args)
const warn = (...args) => console.warn('[device]', ...args)
const err = (...args) => console.error('[device]', ...args)

export class PulseSerialDevice {
  static get isSupported() {
    return typeof navigator !== 'undefined' && 'serial' in navigator
  }

  constructor() {
    this.port = null
    this.reader = null
    this.readableClosed = null
    this.connected = false
    this.capturing = false
    this._sampleCount = 0
    this._captureStartedAt = 0
  }

  async connect({ baudRate = 115200 } = {}) {
    log('connect()', { baudRate, isSupported: PulseSerialDevice.isSupported })
    if (!PulseSerialDevice.isSupported) {
      throw new Error('Web Serial API is not supported in this browser')
    }
    if (this.connected) {
      log('connect() skipped — already connected')
      return
    }

    this.port = await navigator.serial.requestPort()
    const info = typeof this.port.getInfo === 'function' ? this.port.getInfo() : {}
    log('port chosen', info)

    await this.port.open({
      baudRate,
      dataBits: 8,
      stopBits: 1,
      parity: 'none',
      bufferSize: 4096,
      flowControl: 'none'
    })
    this.connected = true
    log('port opened (115200 8-N-1)')
  }

  async disconnect() {
    log('disconnect()')
    await this.stopCapture()
    if (this.port) {
      try {
        await this.port.close()
        log('port closed')
      } catch (e) {
        warn('port.close() threw (likely already closed):', e?.message || e)
      }
      this.port = null
    }
    this.connected = false
  }

  // Begin streaming samples.
  //   `onSample(value: number)` fires once per parsed line with the raw
  //     PPG sample (first CSV field on the extended firmware, the whole
  //     integer on the legacy firmware).
  //   `onMetrics({raw, avg, filtered, peak, hr, hrv})` fires only for the
  //     extended CSV variant. Optional — pass nothing if you only care
  //     about the raw waveform.
  //   `onError(err)` fires on a decode/parse exception; the loop keeps
  //     running so a single bad line doesn't kill the capture.
  async startCapture({ onSample, onMetrics, onError } = {}) {
    if (!this.connected || !this.port) {
      throw new Error('not connected')
    }
    if (this.capturing) {
      log('startCapture() skipped — already capturing')
      return
    }

    this.capturing = true
    this._sampleCount = 0
    this._captureStartedAt = performance.now()
    log('startCapture() — streaming samples')

    // Bytes -> decoded text -> lines.
    const textDecoder = new TextDecoderStream()
    this.readableClosed = this.port.readable.pipeTo(textDecoder.writable).catch(() => {})
    const lineStream = textDecoder.readable.pipeThrough(new LineSplitterStream())
    this.reader = lineStream.getReader()

    // Drain in the background.
    ;(async () => {
      try {
        while (this.capturing) {
          const { value, done } = await this.reader.read()
          if (done) {
            log('reader.read() returned done=true; ending capture loop')
            break
          }
          if (value == null) continue
          const trimmed = value.trim()
          if (!trimmed) continue
          const parsed = parseLine(trimmed)
          if (parsed == null || parsed.raw < 50) {
            warn('unparsable line, skipping:', JSON.stringify(trimmed.slice(0, 64)))
            // onError?.(new Error(`unparsable line: ${trimmed.slice(0, 32)}`))
            continue
          }
          this._sampleCount += 1
          // Heartbeat every 50 samples so we can see the stream is alive
          // without flooding the console.
          if (this._sampleCount === 1 || this._sampleCount % 50 === 0) {
            const elapsed = (performance.now() - this._captureStartedAt) / 1000
            const rate = elapsed > 0 ? (this._sampleCount / elapsed).toFixed(1) : '–'
            const extra = parsed.metrics
              ? ` hr=${parsed.metrics.hr} hrv=${parsed.metrics.hrv}`
              : ''
            log(`sample #${this._sampleCount} value=${parsed.raw} elapsed=${elapsed.toFixed(2)}s rate=${rate}Hz${extra}`)
          }
          onSample?.(parsed.raw)
          if (parsed.metrics) onMetrics?.(parsed.metrics)
        }
      } catch (e) {
        err('capture loop threw:', e)
        onError?.(e)
      }
    })()
  }

  async stopCapture() {
    if (!this.capturing) return
    const elapsed = (performance.now() - this._captureStartedAt) / 1000
    const rate = elapsed > 0 ? (this._sampleCount / elapsed).toFixed(1) : '–'
    log(`stopCapture() — collected ${this._sampleCount} samples in ${elapsed.toFixed(2)}s (≈${rate}Hz)`)

    this.capturing = false
    if (this.reader) {
      try {
        await this.reader.cancel()
      } catch (e) {
        warn('reader.cancel() threw:', e?.message || e)
      }
      try {
        this.reader.releaseLock()
      } catch (e) {
        warn('reader.releaseLock() threw:', e?.message || e)
      }
      this.reader = null
    }
    if (this.readableClosed) {
      try {
        await this.readableClosed
      } catch (e) {
        warn('readableClosed awaited with error:', e?.message || e)
      }
      this.readableClosed = null
    }
  }
}

// Parse one trimmed serial line into `{ raw, metrics? }`, or `null` if the
// line is malformed. A comma in the line picks the 6-field extended format;
// anything else is treated as a plain integer sample from the legacy sketch.
function parseLine(line) {
  if (line.includes(',')) {
    const parts = line.split(',')
    if (parts.length !== 6) return null
    const nums = parts.map(Number)
    if (nums.some((n) => !Number.isFinite(n))) return null
    const [raw, avg, filtered, peak, hr, hrv] = nums
    return { raw, metrics: { raw, avg, filtered, peak, hr, hrv } }
  }
  const n = Number(line)
  if (!Number.isFinite(n)) return null
  return { raw: n }
}

// TransformStream that emits one line at a time. Buffers partial lines across
// chunks. Accepts both "\n" and "\r\n" line endings (Arduino println uses CRLF).
class LineSplitterStream extends TransformStream {
  constructor() {
    let buffer = ''
    super({
      transform(chunk, controller) {
        buffer += chunk
        const lines = buffer.split(/\r?\n/)
        buffer = lines.pop() ?? ''
        for (const line of lines) controller.enqueue(line)
      },
      flush(controller) {
        if (buffer) controller.enqueue(buffer)
        buffer = ''
      }
    })
  }
}
