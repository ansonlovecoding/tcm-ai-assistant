# `web/src/device/` — external hardware adapters

JavaScript adapters for the external devices used by the TCM Assistant web
app. They live inside `web/src/` because they run in the browser (Web
Serial / Web USB / Web Bluetooth) and are exposed to the rest of the SPA
through the Vite alias `@device/...` (see `web/vite.config.js`).

Today there is just one adapter: the **PulseSensor** (Arduino + analogue
PPG finger sensor on pin A0).

## Pulse sensor — wire protocol

`pulse-serial-device.js` supports **two firmware variants** on the same
code path. The transport is identical in both cases — USB-CDC, 115200
8-N-1, device → host only, one record per `\r\n`-terminated line. The
parser tells them apart per-line by the presence of a comma.

| Setting        | Value        |
|----------------|--------------|
| Baud rate      | `115200`     |
| Frame format   | 8-N-1, no flow control |
| Direction      | Device → host only (no commands) |
| Encoding       | UTF-8 ASCII digits (+ `,` for the extended variant) |
| Framing        | One record per line, terminated by `\r\n` |
| Sample rate    | ~100 Hz (`delay(10)`; jitter from execution time) |

### Variant 1 — legacy `pulse_sensor.ino` (single int per line)

```cpp
int const PULSE_SENSOR_PIN = 0;

int Signal;
int Threshold = 550;

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  Serial.begin(115200);
}

void loop() {
  Signal = analogRead(PULSE_SENSOR_PIN);   // 0..1023
  Serial.println(Signal);                  // prints int + "\r\n"
  if (Signal > Threshold) digitalWrite(LED_BUILTIN, HIGH);
  else                    digitalWrite(LED_BUILTIN, LOW);
  delay(10);                                // ~100 Hz
}
```

Each line is a single 10-bit ADC reading in the range `0`–`1023`.

### Variant 2 — extended sketch (6 CSV fields per line)

```cpp
Serial.println(String(raw_PPG)    + "," +   // 原始数据 (raw ADC)
               String(avg_PPG)    + "," +   // 平滑滤波数据 (smoothed)
               String(filter_PPG) + "," +   // 带通滤波数据 (band-pass)
               String(ppg_Peak)   + "," +   // 心跳检测数据 (peak flag)
               String(hr)         + "," +   // 心率 (BPM)
               String(hrv));                // HRV / SDNN (ms)
```

Per-line layout:

| Index | Field        | Type    | Meaning                                                      |
|-------|--------------|---------|--------------------------------------------------------------|
| 0     | `raw_PPG`    | int     | Raw ADC reading — same role as Variant 1's single value.     |
| 1     | `avg_PPG`    | int     | Moving-average smoothed PPG.                                 |
| 2     | `filter_PPG` | int     | Band-pass filtered PPG (removes baseline drift + HF noise).  |
| 3     | `ppg_Peak`   | 0 / 1   | Heartbeat detector — `1` on a detected systolic peak.        |
| 4     | `hr`         | int     | Heart rate, beats per minute.                                |
| 5     | `hrv`        | int     | HRV as SDNN, milliseconds.                                   |

The first field (`raw_PPG`) is what `onSample` receives, so the existing
256-sample window flow works unchanged with this firmware. The full
record is also delivered to an optional `onMetrics({raw, avg, filtered,
peak, hr, hrv})` callback for any UI that wants to display HR / HRV
without re-deriving them in the browser.

Note that the model in `pulse/` was trained on a 125 Hz PPG dataset, so
there is a small rate mismatch with both variants. The model's z-score
normalisation in `pulse/predict.py` absorbs the amplitude scale; the
rate difference is acceptable for demo / classroom use.

## `pulse-serial-device.js`

Browser-side wrapper around the [Web Serial API][webserial]. Exposes a tiny
class:

```js
import { PulseSerialDevice } from '@device/pulse-serial-device.js'

if (!PulseSerialDevice.isSupported) { /* fall back / show message */ }

const dev = new PulseSerialDevice()
await dev.connect()                       // prompts the user to pick a port
await dev.startCapture({
  onSample:  (value)   => { /* raw_PPG, one ADC reading at a time */ },
  onMetrics: (metrics) => { /* {raw, avg, filtered, peak, hr, hrv} — Variant 2 only */ },
  onError:   (err)     => { /* parse / stream errors */ }
})
// later …
await dev.stopCapture()
await dev.disconnect()
```

The class:

- buffers partial lines across read chunks (Arduino `println` may straddle
  USB packets);
- accepts both `\n` and `\r\n` line endings;
- auto-detects the firmware variant per-line — a comma means CSV (6 fields),
  no comma means a single integer. `onSample` fires for both; `onMetrics`
  only fires for the CSV variant;
- ignores blank lines and unparsable junk (calls `onError` for those, keeps
  reading).

## Browser support

Web Serial currently ships in **Chromium-based** browsers (Chrome, Edge,
Brave, Opera). Safari and Firefox do not implement it. The page must be
served from `https://` or `http://localhost`.

[webserial]: https://developer.mozilla.org/en-US/docs/Web/API/Web_Serial_API
