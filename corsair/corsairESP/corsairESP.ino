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

// Achieved smoothing:

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