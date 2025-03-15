#include <ArduinoJson.h>
#include <Adafruit_NeoPixel.h>

#define LED_PIN 23      // Pin connected to the LED strip
#define NUM_LEDS 50     // Total number of LEDs
#define BRIGHTNESS 200  // LED Brightness (0-255)
#define NUM_COLORS 6    // Number of colors received

Adafruit_NeoPixel strip(NUM_LEDS, LED_PIN, NEO_GRB + NEO_KHZ800);

// Store colors
int colors[NUM_COLORS][3];

void setup() {
    Serial.begin(115200);
    strip.begin();
    strip.setBrightness(BRIGHTNESS);
    strip.show();  // Initialize all LEDs to 'off'
}

void loop() {
    if (Serial.available()) {
        StaticJsonDocument<512> doc;
        String input = Serial.readStringUntil('\n');  // Read JSON Data

        DeserializationError error = deserializeJson(doc, input);
        if (error) {
            Serial.println("JSON Parsing Error");
            return;
        }

        // Parse JSON and update colors
        for (int i = 0; i < NUM_COLORS; i++) {
            colors[i][0] = doc["LEDColors"][i]["G"]; // Swap Green
            colors[i][1] = doc["LEDColors"][i]["R"]; // Swap Red
            colors[i][2] = doc["LEDColors"][i]["B"]; // Keep Blue the same
        }

        Serial.println("Updated Colors");
        updateLEDs();
    }
}

void updateLEDs() {
    int section_size = NUM_LEDS / NUM_COLORS;  // Split into 6 sections

    for (int i = 0; i < NUM_COLORS; i++) {
        for (int j = 0; j < section_size; j++) {
            int index = (i * section_size) + j;
            if (index < NUM_LEDS) {
                strip.setPixelColor(index, strip.Color(colors[i][0], colors[i][1], colors[i][2]));
            }
        }
    }

    strip.show();
}