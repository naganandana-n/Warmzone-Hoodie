#include <FastLED.h>

// ── USER CONFIG ───────────────────────────────────────────────────────────
#define LED_PIN      23
#define NUM_LEDS     24
#define LED_TYPE     WS2812B
#define COLOR_ORDER  GRB

// Baud rate for Serial
const uint32_t SERIAL_BAUD = 115200;
// ──────────────────────────────────────────────────────────────────────────

CRGB leds[NUM_LEDS];

void setup() {
  // Initialize Serial over USB
  Serial.begin(SERIAL_BAUD);
  while(!Serial) {
    // wait for Serial port to be ready
    delay(10);
  }
  Serial.println("ESP32 LED Serial Bridge Starting...");

  // Initialize FastLED
  FastLED.addLeds<LED_TYPE, LED_PIN, COLOR_ORDER>(leds, NUM_LEDS)
         .setCorrection(TypicalLEDStrip);
  FastLED.setBrightness(128);
}

void loop() {
  // Check if we have at least 24*3 = 72 bytes available
  if (Serial.available() >= NUM_LEDS * 3) {
    uint8_t buf[NUM_LEDS * 3];
    // Read exactly 72 bytes
    Serial.readBytes(buf, NUM_LEDS * 3);

    // Copy into LED array
    for (int i = 0; i < NUM_LEDS; i++) {
      int idx = i * 3;
      leds[i] = CRGB(buf[idx], buf[idx + 1], buf[idx + 2]);
    }

    // Push to strip
    FastLED.show();
  }

  // (Optional) small delay to yield
  // delay(1);
}