#include <Adafruit_NeoPixel.h>

#define LED_PIN     23
#define NUM_LEDS    50

Adafruit_NeoPixel strip(NUM_LEDS, LED_PIN, NEO_GRB + NEO_KHZ800);

void setup() {
  strip.begin();
  strip.show(); // Initialize all pixels to 'off'
  delay(1000);

  // Step 1: Solid Colors
  showColor(strip.Color(255, 0, 0)); // Red
  delay(1000);
  showColor(strip.Color(0, 255, 0)); // Green
  delay(1000);
  showColor(strip.Color(0, 0, 255)); // Blue
  delay(1000);

  // Step 2: Rainbow animation
  rainbowCycle(5);  // Adjust speed (lower = faster)
}

void loop() {
  // Loop rainbow forever
  rainbowCycle(5);
}

// Set entire strip to one color
void showColor(uint32_t color) {
  for (int i = 0; i < NUM_LEDS; i++) {
    strip.setPixelColor(i, color);
  }
  strip.show();
}

// Rainbow effect across all LEDs
void rainbowCycle(uint8_t wait) {
  uint16_t i, j;
  for (j = 0; j < 256; j++) {
    for (i = 0; i < strip.numPixels(); i++) {
      strip.setPixelColor(i, Wheel(((i * 256 / strip.numPixels()) + j) & 255));
    }
    strip.show();
    delay(wait);
  }
}

// Helper to generate rainbow colors
uint32_t Wheel(byte WheelPos) {
  WheelPos = 255 - WheelPos;
  if (WheelPos < 85) {
    return strip.Color(255 - WheelPos * 3, 0, WheelPos * 3);
  } else if (WheelPos < 170) {
    WheelPos -= 85;
    return strip.Color(0, WheelPos * 3, 255 - WheelPos * 3);
  } else {
    WheelPos -= 170;
    return strip.Color(WheelPos * 3, 255 - WheelPos * 3, 0);
  }
}

/*

#include <Adafruit_NeoPixel.h>

#define LED_PIN    23
#define NUM_LEDS   60
#define MAX_BRIGHTNESS 125

Adafruit_NeoPixel pixels(NUM_LEDS, LED_PIN, NEO_GRB + NEO_KHZ800);

int brightness = 0;
bool increasing = true;
unsigned long lastUpdate = 0;
const int delayMs = 10;

// Fallback color (brand pink: #E22DA1 swapped R/G)
uint8_t fallback_r = 45;
uint8_t fallback_g = 226;
uint8_t fallback_b = 161;

void setup() {
  pixels.begin();
  pixels.clear();
  pixels.show();
}

void loop() {
  if (millis() - lastUpdate > delayMs) {
    for (int i = 0; i < NUM_LEDS; i++) {
      pixels.setPixelColor(i, pixels.Color(
        (fallback_g * brightness * MAX_BRIGHTNESS) / 65025,
        (fallback_r * brightness * MAX_BRIGHTNESS) / 65025,
        (fallback_b * brightness * MAX_BRIGHTNESS) / 65025
      ));
    }
    pixels.show();

    if (increasing) {
      brightness++;
      if (brightness >= 255) increasing = false;
    } else {
      brightness--;
      if (brightness <= 0) increasing = true;
    }
    lastUpdate = millis();
  }
}

*/