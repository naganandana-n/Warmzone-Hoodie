#include <ArduinoJson.h>
#include <Adafruit_NeoPixel.h>

#define LED_PIN 5
#define NUM_LEDS 30
#define BRIGHTNESS 200

Adafruit_NeoPixel strip(NUM_LEDS, LED_PIN, NEO_GRB + NEO_KHZ800);

struct RGB {
    int R, G, B;
};

RGB colors[6];

void setup() {
    Serial.begin(115200);
    strip.begin();
    strip.setBrightness(BRIGHTNESS);
    strip.show();
}

void loop() {
    if (Serial.available()) {
        StaticJsonDocument<256> doc;
        String input = Serial.readStringUntil('\n');

        DeserializationError error = deserializeJson(doc, input);
        if (error) return;

        for (int i = 0; i < 6; i++) {
            colors[i] = {doc["Colors"][i]["R"], doc["Colors"][i]["G"], doc["Colors"][i]["B"]};
        }

        updateLEDs();
    }
}

void updateLEDs() {
    for (int i = 0; i < NUM_LEDS; i++) {
        int colorIndex = i % 6;
        strip.setPixelColor(i, strip.Color(colors[colorIndex].R, colors[colorIndex].G, colors[colorIndex].B));
    }
    strip.show();
}