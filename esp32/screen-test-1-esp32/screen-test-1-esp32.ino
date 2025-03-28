#include <ArduinoJson.h>
#include <Adafruit_NeoPixel.h>

#define LED_PIN 5       // Pin connected to the LED strip
#define NUM_LEDS 30     // Total number of LEDs
#define BRIGHTNESS 200  // LED Brightness (0-255)
#define FADE_STEPS 30   // Number of steps for smooth transition
#define FADE_DELAY 15   // Delay (ms) per step

Adafruit_NeoPixel strip(NUM_LEDS, LED_PIN, NEO_GRB + NEO_KHZ800);

struct RGB {
    int R = 0, G = 0, B = 0;
};

// Store current and target colors
RGB currentColors[4];  // TL, TR, BL, BR
RGB targetColors[4];   // Updated colors from the screen

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

        // Parse JSON and update target colors
        targetColors[0] = {doc["TL"]["R"], doc["TL"]["G"], doc["TL"]["B"]};
        targetColors[1] = {doc["TR"]["R"], doc["TR"]["G"], doc["TR"]["B"]};
        targetColors[2] = {doc["BL"]["R"], doc["BL"]["G"], doc["BL"]["B"]};
        targetColors[3] = {doc["BR"]["R"], doc["BR"]["G"], doc["BR"]["B"]};

        Serial.println(" Updated Colors");
        fadeToNewColors();
    }
}

void fadeToNewColors() {
    for (int step = 0; step <= FADE_STEPS; step++) {
        for (int i = 0; i < 4; i++) {  // Loop through quadrants
            int r = map(step, 0, FADE_STEPS, currentColors[i].R, targetColors[i].R);
            int g = map(step, 0, FADE_STEPS, currentColors[i].G, targetColors[i].G);
            int b = map(step, 0, FADE_STEPS, currentColors[i].B, targetColors[i].B);

            applyGradient(i, r, g, b);
        }
        strip.show();
        delay(FADE_DELAY);  // Control fade speed
    }

    // Update current colors
    for (int i = 0; i < 4; i++) {
        currentColors[i] = targetColors[i];
    }
}

// **Apply gradient effect between quadrants**
void applyGradient(int quadrant, int r, int g, int b) {
    int section_size = NUM_LEDS / 4;
    int startIndex = quadrant * section_size;
    int endIndex = startIndex + section_size;

    // Find next quadrant's color for blending
    int nextQuadrant = (quadrant + 1) % 4;  // Wrap around at last quadrant
    int rNext = targetColors[nextQuadrant].R;
    int gNext = targetColors[nextQuadrant].G;
    int bNext = targetColors[nextQuadrant].B;

    for (int i = 0; i < section_size; i++) {
        float ratio = float(i) / section_size;  // 0 → 1
        int rBlend = r * (1 - ratio) + rNext * ratio;
        int gBlend = g * (1 - ratio) + gNext * ratio;
        int bBlend = b * (1 - ratio) + bNext * ratio;

        strip.setPixelColor(startIndex + i, strip.Color(rBlend, gBlend, bBlend));
    }
}