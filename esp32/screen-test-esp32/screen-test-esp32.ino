#include <ArduinoJson.h>
#include <Adafruit_NeoPixel.h>

#define LED_PIN 5       // Pin connected to the LED strip
#define NUM_LEDS 30     // Total number of LEDs
#define BRIGHTNESS 200  // LED Brightness (0-255)

Adafruit_NeoPixel strip(NUM_LEDS, LED_PIN, NEO_GRB + NEO_KHZ800);

// Quadrant colors
int tl_r = 0, tl_g = 0, tl_b = 0;
int tr_r = 0, tr_g = 0, tr_b = 0;
int bl_r = 0, bl_g = 0, bl_b = 0;
int br_r = 0, br_g = 0, br_b = 0;

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
        tl_r = doc["TL"]["R"];
        tl_g = doc["TL"]["G"];
        tl_b = doc["TL"]["B"];

        tr_r = doc["TR"]["R"];
        tr_g = doc["TR"]["G"];
        tr_b = doc["TR"]["B"];

        bl_r = doc["BL"]["R"];
        bl_g = doc["BL"]["G"];
        bl_b = doc["BL"]["B"];

        br_r = doc["BR"]["R"];
        br_g = doc["BR"]["G"];
        br_b = doc["BR"]["B"];

        Serial.println(" Updated Colors");
        updateLEDs();
    }
}

void updateLEDs() {
    int section_size = NUM_LEDS / 4;  // Split into 4 equal sections

    for (int i = 0; i < section_size; i++) {
        strip.setPixelColor(i, strip.Color(tl_r, tl_g, tl_b));  // Top-Left LEDs
        strip.setPixelColor(i + section_size, strip.Color(tr_r, tr_g, tr_b));  // Top-Right LEDs
        strip.setPixelColor(i + (2 * section_size), strip.Color(bl_r, bl_g, bl_b));  // Bottom-Left LEDs
        strip.setPixelColor(i + (3 * section_size), strip.Color(br_r, br_g, br_b));  // Bottom-Right LEDs
    }

    strip.show();
}