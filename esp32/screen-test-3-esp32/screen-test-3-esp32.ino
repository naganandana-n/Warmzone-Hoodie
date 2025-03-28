#include <ArduinoJson.h>
#include <Adafruit_NeoPixel.h>

#define LED_PIN 23       // Pin connected to the LED strip
#define NUM_LEDS 50     // Total number of LEDs
#define BRIGHTNESS 200  // LED Brightness (0-255)

Adafruit_NeoPixel strip(NUM_LEDS, LED_PIN, NEO_GRB + NEO_KHZ800);

// Two dominant colors
int color1_r = 0, color1_g = 0, color1_b = 0;
int color2_r = 0, color2_g = 0, color2_b = 0;

void setup() {
    Serial.begin(115200);
    strip.begin();
    strip.setBrightness(BRIGHTNESS);
    strip.show();  // Initialize all LEDs to 'off'
}

void loop() {
    if (Serial.available()) {
        StaticJsonDocument<256> doc;
        String input = Serial.readStringUntil('\n');  // Read JSON Data

        DeserializationError error = deserializeJson(doc, input);
        if (error) {
            Serial.println(" JSON Parsing Error");
            return;
        }

        // Parse JSON and update colors
        color1_r = doc["Color1"][0];
        color1_g = doc["Color1"][1];
        color1_b = doc["Color1"][2];

        color2_r = doc["Color2"][0];
        color2_g = doc["Color2"][1];
        color2_b = doc["Color2"][2];

        Serial.println(" Updated Colors");
        updateLEDs();
    }
}

void updateLEDs() {
    int half_size = NUM_LEDS / 2;  // Split LEDs into 2 equal sections

    for (int i = 0; i < half_size; i++) {
        strip.setPixelColor(i, strip.Color(color1_r, color1_g, color1_b));  // First half LEDs
        strip.setPixelColor(i + half_size, strip.Color(color2_r, color2_g, color2_b));  // Second half LEDs
    }

    strip.show();
}