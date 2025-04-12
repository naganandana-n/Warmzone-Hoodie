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