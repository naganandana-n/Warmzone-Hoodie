/*
// Original program

#include <Adafruit_NeoPixel.h>

// ── USER CONFIG ───────────────────────────────────────────────────────────
#define LED_PIN    23
#define NUM_LEDS   24
// Baud rate for Serial
const uint32_t SERIAL_BAUD = 115200;
// ──────────────────────────────────────────────────────────────────────────

Adafruit_NeoPixel strip(NUM_LEDS, LED_PIN, NEO_GRB + NEO_KHZ800);

void setup() {
  // Initialize Serial over USB
  Serial.begin(SERIAL_BAUD);
  while (!Serial) {
    delay(10);
  }
  Serial.println("ESP32 NeoPixel Serial Bridge Starting...");

  // Initialize NeoPixel strip
  strip.begin();
  strip.setBrightness(128);
  strip.show(); // turn off all pixels
}

void loop() {
  // Wait until we have at least NUM_LEDS*3 bytes available
  if (Serial.available() >= NUM_LEDS * 3) {
    uint8_t buf[NUM_LEDS * 3];
    Serial.readBytes(buf, NUM_LEDS * 3);

    // Write to NeoPixel strip
    for (int i = 0; i < NUM_LEDS; i++) {
      int idx = i * 3;
      uint8_t r = buf[idx];
      uint8_t g = buf[idx + 1];
      uint8_t b = buf[idx + 2];
      strip.setPixelColor(i, strip.Color(r, g, b));
    }
    strip.show();
  }

  // Optional small delay
  // delay(1);
}

*/


/*
// Achieved smoothing:
// best working one

#include <Adafruit_NeoPixel.h>

// ── USER CONFIG ───────────────────────────────────────────────────────────
#define LED_PIN    23
#define NUM_LEDS   24
const uint32_t SERIAL_BAUD = 115200;
// ──────────────────────────────────────────────────────────────────────────

Adafruit_NeoPixel strip(NUM_LEDS, LED_PIN, NEO_GRB + NEO_KHZ800);

// --- EASING CONFIG --------------------------------------------------------
const unsigned long FRAME_INTERVAL = 50;  // ms between accepting new frames
const float          EASE_FACTOR    = 0.2; // 0.0–1.0 fraction per step
const unsigned long EASE_STEP_DELAY = 10;  // ms between easing steps
// --------------------------------------------------------------------------

uint8_t currentR[NUM_LEDS], currentG[NUM_LEDS], currentB[NUM_LEDS];
uint8_t targetR[NUM_LEDS],  targetG[NUM_LEDS],  targetB[NUM_LEDS];
unsigned long lastFrameTime = 0;

void setup() {
  // Initialize Serial over USB
  Serial.begin(SERIAL_BAUD);
  while (!Serial) { delay(10); }
  Serial.println("ESP32 NeoPixel Serial Bridge Starting...");

  // Initialize NeoPixel strip
  strip.begin();
  strip.setBrightness(128);
  strip.show(); // turn off all pixels

  // Initialize both current and target arrays to off
  for (int i = 0; i < NUM_LEDS; i++) {
    currentR[i] = currentG[i] = currentB[i] = 0;
    targetR[i]  = targetG[i]  = targetB[i]  = 0;
  }
}

void loop() {
  unsigned long now = millis();

  // 1) If it's time for a new frame and we have enough bytes, read it
  if (now - lastFrameTime >= FRAME_INTERVAL && Serial.available() >= NUM_LEDS * 3) {
    lastFrameTime = now;
    uint8_t buf[NUM_LEDS * 3];
    Serial.readBytes(buf, NUM_LEDS * 3);

    // Copy into target arrays
    for (int i = 0; i < NUM_LEDS; i++) {
      int idx = i * 3;
      targetR[i] = buf[idx];
      targetG[i] = buf[idx + 1];
      targetB[i] = buf[idx + 2];
    }
  }

  // 2) Ease current[] toward target[] and update strip
  bool changed = false;
  for (int i = 0; i < NUM_LEDS; i++) {
    int dr = int(targetR[i]) - int(currentR[i]);
    int dg = int(targetG[i]) - int(currentG[i]);
    int db = int(targetB[i]) - int(currentB[i]);

    if (abs(dr) > 1 || abs(dg) > 1 || abs(db) > 1) {
      currentR[i] = currentR[i] + dr * EASE_FACTOR;
      currentG[i] = currentG[i] + dg * EASE_FACTOR;
      currentB[i] = currentB[i] + db * EASE_FACTOR;
      changed = true;
    } else {
      // close enough, snap to target
      currentR[i] = targetR[i];
      currentG[i] = targetG[i];
      currentB[i] = targetB[i];
    }
    strip.setPixelColor(i, strip.Color(currentR[i], currentG[i], currentB[i]));
  }

  // 3) If anything changed, push to LEDs
  if (changed) {
    strip.show();
  }

  // 4) Small delay to control easing rate
  delay(EASE_STEP_DELAY);
}

*/

/* 

// esp working version

#include <Adafruit_NeoPixel.h>

// ── USER CONFIG ───────────────────────────────────────────────────────────
#define LED_PIN         23
#define NUM_LEDS        50
#define NUM_SAMPLES     24
#define PEB_PIN         16
const uint32_t SERIAL_BAUD   = 115200;

// EASING CONFIG
const unsigned long FRAME_INTERVAL  = 17;   // ms between accepting new frames ORIGINALLY 50
const float          EASE_FACTOR     = 0.2; // fraction toward target each step
const unsigned long EASE_STEP_DELAY = 5;   // ms between easing iterations ORIGINALLY 10
// ──────────────────────────────────────────────────────────────────────────

Adafruit_NeoPixel strip(NUM_LEDS, LED_PIN, NEO_GRB + NEO_KHZ800);

// Buffers for easing
uint8_t currentR[NUM_LEDS], currentG[NUM_LEDS], currentB[NUM_LEDS];
uint8_t targetR[NUM_LEDS],  targetG[NUM_LEDS],  targetB[NUM_LEDS];

uint8_t frameBuf[NUM_SAMPLES * 3];
unsigned long lastFrameTime = 0;

void setup() {
  // Serial
  Serial.begin(SERIAL_BAUD);
  while (!Serial) { delay(10); }

  // PEB pin high
  pinMode(PEB_PIN, OUTPUT);
  digitalWrite(PEB_PIN, HIGH);

  // LED strip init
  strip.begin();
  strip.setBrightness(128);
  strip.show();

  // Initialize current and target to off
  for (int i = 0; i < NUM_LEDS; i++) {
    currentR[i] = currentG[i] = currentB[i] = 0;
    targetR[i]  = targetG[i]  = targetB[i]  = 0;
  }
}

void loop() {
  unsigned long now = millis();

  // 1) Read a new frame if interval elapsed and bytes available
  if (now - lastFrameTime >= FRAME_INTERVAL && Serial.available() >= NUM_SAMPLES * 3) {
    lastFrameTime = now;
    Serial.readBytes(frameBuf, NUM_SAMPLES * 3);

    // Map samples into targetR/G/B for each LED
    int ledIndex = 0;
    for (int i = 0; i < NUM_SAMPLES; i++) {
      uint8_t r = frameBuf[i*3 + 0];
      uint8_t g = frameBuf[i*3 + 1];
      uint8_t b = frameBuf[i*3 + 2];
      // two LEDs per sample
      if (ledIndex < NUM_LEDS) {
        targetR[ledIndex] = r;
        targetG[ledIndex] = g;
        targetB[ledIndex] = b;
      }
      if (ledIndex+1 < NUM_LEDS) {
        targetR[ledIndex+1] = r;
        targetG[ledIndex+1] = g;
        targetB[ledIndex+1] = b;
      }
      ledIndex += 2;
    }
    // fill remainder with last sample
    uint8_t lr = frameBuf[(NUM_SAMPLES-1)*3 + 0];
    uint8_t lg = frameBuf[(NUM_SAMPLES-1)*3 + 1];
    uint8_t lb = frameBuf[(NUM_SAMPLES-1)*3 + 2];
    while (ledIndex < NUM_LEDS) {
      targetR[ledIndex] = lr;
      targetG[ledIndex] = lg;
      targetB[ledIndex] = lb;
      ledIndex++;
    }
  }

  // 2) Easing step: move current toward target
  bool changed = false;
  for (int i = 0; i < NUM_LEDS; i++) {
    int dr = int(targetR[i]) - int(currentR[i]);
    int dg = int(targetG[i]) - int(currentG[i]);
    int db = int(targetB[i]) - int(currentB[i]);

    if (abs(dr) > 1 || abs(dg) > 1 || abs(db) > 1) {
      currentR[i] = currentR[i] + dr * EASE_FACTOR;
      currentG[i] = currentG[i] + dg * EASE_FACTOR;
      currentB[i] = currentB[i] + db * EASE_FACTOR;
      changed = true;
    } else {
      // close enough: snap
      currentR[i] = targetR[i];
      currentG[i] = targetG[i];
      currentB[i] = targetB[i];
    }
    strip.setPixelColor(i, strip.Color(currentR[i], currentG[i], currentB[i]));
  }

  // 3) Update LEDs if needed
  if (changed) {
    strip.show();
  }

  // 4) Delay to control easing rate
  delay(EASE_STEP_DELAY);
}

*/

// final color version

#include <Adafruit_NeoPixel.h>

// ── USER CONFIG ───────────────────────────────────────────────────────────
#define LED_PIN         23
#define NUM_LEDS        25      // now 25 LEDs total
#define NUM_SAMPLES     24
#define PEB_PIN         16
const uint32_t SERIAL_BAUD   = 115200;

// EASING CONFIG
const unsigned long FRAME_INTERVAL  = 17;   // ms between accepting new frames
const float          EASE_FACTOR     = 0.2; // fraction toward target each step
const unsigned long EASE_STEP_DELAY = 5;    // ms between easing iterations
// ──────────────────────────────────────────────────────────────────────────

Adafruit_NeoPixel strip(NUM_LEDS, LED_PIN, NEO_GRB + NEO_KHZ800);

// Buffers for easing
uint8_t currentR[NUM_LEDS], currentG[NUM_LEDS], currentB[NUM_LEDS];
uint8_t targetR[NUM_LEDS],  targetG[NUM_LEDS],  targetB[NUM_LEDS];

uint8_t frameBuf[NUM_SAMPLES * 3];
unsigned long lastFrameTime = 0;

void setup() {
  Serial.begin(SERIAL_BAUD);
  while (!Serial) { delay(10); }

  // Keep PEB pin high
  pinMode(PEB_PIN, OUTPUT);
  digitalWrite(PEB_PIN, HIGH);

  // Initialize strip
  strip.begin();
  strip.setBrightness(128);
  strip.show();

  // Initialize buffers to off
  for (int i = 0; i < NUM_LEDS; i++) {
    currentR[i] = currentG[i] = currentB[i] = 0;
    targetR[i]  = targetG[i]  = targetB[i]  = 0;
  }
}

void loop() {
  unsigned long now = millis();

  // 1) Read new frame if due
  if (now - lastFrameTime >= FRAME_INTERVAL && Serial.available() >= NUM_SAMPLES * 3) {
    lastFrameTime = now;
    Serial.readBytes(frameBuf, NUM_SAMPLES * 3);

    // Map each sample to one LED
    for (int i = 0; i < NUM_SAMPLES; i++) {
      uint8_t r = frameBuf[i*3 + 0];
      uint8_t g = frameBuf[i*3 + 1];
      uint8_t b = frameBuf[i*3 + 2];
      targetR[i] = r;
      targetG[i] = g;
      targetB[i] = b;
    }
    // Final LED (index 24) mirrors sample 23
    targetR[NUM_LEDS-1] = frameBuf[(NUM_SAMPLES-1)*3 + 0];
    targetG[NUM_LEDS-1] = frameBuf[(NUM_SAMPLES-1)*3 + 1];
    targetB[NUM_LEDS-1] = frameBuf[(NUM_SAMPLES-1)*3 + 2];
  }

  // 2) Easing step
  bool changed = false;
  for (int i = 0; i < NUM_LEDS; i++) {
    int dr = int(targetR[i]) - int(currentR[i]);
    int dg = int(targetG[i]) - int(currentG[i]);
    int db = int(targetB[i]) - int(currentB[i]);

    if (abs(dr) > 1 || abs(dg) > 1 || abs(db) > 1) {
      currentR[i] = currentR[i] + dr * EASE_FACTOR;
      currentG[i] = currentG[i] + dg * EASE_FACTOR;
      currentB[i] = currentB[i] + db * EASE_FACTOR;
      changed = true;
    } else {
      // Snap if close
      currentR[i] = targetR[i];
      currentG[i] = targetG[i];
      currentB[i] = targetB[i];
    }
    strip.setPixelColor(i, strip.Color(currentR[i], currentG[i], currentB[i]));
  }

  // 3) Show if changed
  if (changed) {
    strip.show();
  }

  // 4) Control easing rate
  delay(EASE_STEP_DELAY);
}