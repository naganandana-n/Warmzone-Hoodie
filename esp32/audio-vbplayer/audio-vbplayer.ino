// working test for audio to purple lights

#include <ArduinoJson.h>
#include <Adafruit_NeoPixel.h>

#define LED_PIN 23      // Pin connected to the LED strip
#define NUM_LEDS 50     // Total number of LEDs
#define DEFAULT_BRIGHTNESS 200  // Default LED brightness

Adafruit_NeoPixel strip(NUM_LEDS, LED_PIN, NEO_GRB + NEO_KHZ800);

// **Fixed LED Color (RGB Swapped for Correct Output)**
int LED_R = 45;   // Swap Red ↔ Green
int LED_G = 226;  
int LED_B = 161;

// Store Audio Brightness
int led_brightness = DEFAULT_BRIGHTNESS;

void setup() {
    Serial.begin(115200);
    strip.begin();
    strip.setBrightness(DEFAULT_BRIGHTNESS);
    strip.show();  // Initialize all LEDs to 'off'
}

void loop() {
    if (Serial.available()) {
        StaticJsonDocument<128> doc;
        String input = Serial.readStringUntil('\n');  // Read JSON Data

        DeserializationError error = deserializeJson(doc, input);
        if (error) {
            Serial.println("JSON Parsing Error");
            return;
        }

        // Parse brightness value from JSON
        led_brightness = doc["AudioIntensity"];

        // Update LED brightness while keeping color fixed
        updateLEDs();
    }
}

void updateLEDs() {
    strip.setBrightness(led_brightness);  // Adjust LED brightness based on audio
    for (int i = 0; i < NUM_LEDS; i++) {
        strip.setPixelColor(i, strip.Color(LED_R, LED_G, LED_B));  // Fixed color
    }
    strip.show();
}