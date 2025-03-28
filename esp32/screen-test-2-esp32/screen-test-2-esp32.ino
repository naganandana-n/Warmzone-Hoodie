#include <ArduinoJson.h>
#include <Adafruit_NeoPixel.h>

#define LED_PIN 23      // Pin connected to the LED strip
#define NUM_LEDS 50     // Total number of LEDs
#define BRIGHTNESS 200  // LED Brightness (0-255)
#define FADE_STEPS 30   // Steps for smooth transition
#define FADE_DELAY 15   // Delay per step

Adafruit_NeoPixel strip(NUM_LEDS, LED_PIN, NEO_GRB + NEO_KHZ800);

struct RGB {
    int R = 0, G = 0, B = 0;
};

// **Current and Target Colors**
RGB currentColor1, currentColor2;
RGB targetColor1, targetColor2;

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

        // **Parse JSON for top 2 colors**
        targetColor1 = {doc[0]["R"], doc[0]["G"], doc[0]["B"]};
        targetColor2 = {doc[1]["R"], doc[1]["G"], doc[1]["B"]};

        Serial.println(" Updated Colors");
        fadeToNewColors();
    }
}

// **Smoothly transition colors**
void fadeToNewColors() {
    for (int step = 0; step <= FADE_STEPS; step++) {
        int r1 = map(step, 0, FADE_STEPS, currentColor1.R, targetColor1.R);
        int g1 = map(step, 0, FADE_STEPS, currentColor1.G, targetColor1.G);
        int b1 = map(step, 0, FADE_STEPS, currentColor1.B, targetColor1.B);

        int r2 = map(step, 0, FADE_STEPS, currentColor2.R, targetColor2.R);
        int g2 = map(step, 0, FADE_STEPS, currentColor2.G, targetColor2.G);
        int b2 = map(step, 0, FADE_STEPS, currentColor2.B, targetColor2.B);

        applyGradient(r1, g1, b1, r2, g2, b2);
        strip.show();
        delay(FADE_DELAY);  // Controls fade speed
    }

    // **Update current colors**
    currentColor1 = targetColor1;
    currentColor2 = targetColor2;
}

// **Apply a gradient between the two colors**
void applyGradient(int r1, int g1, int b1, int r2, int g2, int b2) {
    for (int i = 0; i < NUM_LEDS; i++) {
        float ratio = float(i) / (NUM_LEDS - 1);  // 0 → 1
        int rBlend = r1 * (1 - ratio) + r2 * ratio;
        int gBlend = g1 * (1 - ratio) + g2 * ratio;
        int bBlend = b1 * (1 - ratio) + b2 * ratio;

        strip.setPixelColor(i, strip.Color(rBlend, gBlend, bBlend));
    }
}