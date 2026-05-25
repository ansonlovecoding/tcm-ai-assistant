# `web/src/device/` — external hardware adapters

JavaScript adapters for the external devices used by the TCM Assistant web
app. They live inside `web/src/` because they run in the browser (Web
Serial / Web USB / Web Bluetooth) and are exposed to the rest of the SPA
through the Vite alias `@device/...` (see `web/vite.config.js`).

Today there is just one adapter: the **PulseSensor** (Arduino + analogue
PPG finger sensor on pin A0).

## Pulse sensor — wire protocol

Firmware sketch (`pulse_sensor.ino`):

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

Resulting stream over USB-CDC:

| Setting        | Value        |
|----------------|--------------|
| Baud rate      | `115200`     |
| Frame format   | 8-N-1, no flow control |
| Direction      | Device → host only (no commands) |
| Encoding       | UTF-8 ASCII digits |
| Framing        | One integer per line, terminated by `\r\n` |
| Sample range   | `0`–`1023` (10-bit ADC) |
| Sample rate    | ~100 Hz (`delay(10)`; jitter from execution time) |

Note that the model in `pulse/` was trained on a 125 Hz PPG dataset, so
there is a small rate mismatch. The model's z-score normalisation in
`pulse/predict.py` absorbs the amplitude scale; the rate difference is
acceptable for demo / classroom use.

## `pulse-serial-device.js`

Browser-side wrapper around the [Web Serial API][webserial]. Exposes a tiny
class:

```js
import { PulseSerialDevice } from '@device/pulse-serial-device.js'

if (!PulseSerialDevice.isSupported) { /* fall back / show message */ }

const dev = new PulseSerialDevice()
await dev.connect()                       // prompts the user to pick a port
await dev.startCapture({
  onSample: (value) => { /* one ADC reading at a time */ },
  onError:  (err)   => { /* parse / stream errors */ }
})
// later …
await dev.stopCapture()
await dev.disconnect()
```

The class:

- buffers partial lines across read chunks (Arduino `println` may straddle
  USB packets);
- accepts both `\n` and `\r\n` line endings;
- ignores blank lines and unparsable junk (calls `onError` for those, keeps
  reading).

## Browser support

Web Serial currently ships in **Chromium-based** browsers (Chrome, Edge,
Brave, Opera). Safari and Firefox do not implement it. The page must be
served from `https://` or `http://localhost`.

[webserial]: https://developer.mozilla.org/en-US/docs/Web/API/Web_Serial_API
