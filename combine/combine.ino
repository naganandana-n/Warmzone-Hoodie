#include <ArduinoJson.h>
#include <Adafruit_NeoPixel.h>

#define LED_PIN 23      // Pin connected to the LED strip
#define NUM_LEDS 50     // Total number of LEDs
#define BRIGHTNESS 200  // LED Brightness (0-255)
#define NUM_COLORS 6    // Number of colors received
#define MOUSE_PIN 5     // GPIO pin to control (set this as needed)
#define MOUSE_THRESHOLD 2.5  // Mouse speed threshold to turn ON the pin

Adafruit_NeoPixel strip(NUM_LEDS, LED_PIN, NEO_GRB + NEO_KHZ800);

// Store LED colors for screen-based lighting
int colors[NUM_COLORS][3];

// Store brightness from audio intensity
int led_brightness = BRIGHTNESS;

// Store last received mouse speed
float mouse_speed = 0.0;

void setup() {
    Serial.begin(115200);
    strip.begin();
    strip.setBrightness(BRIGHTNESS);
    strip.show();  // Initialize all LEDs to 'off'

    pinMode(MOUSE_PIN, OUTPUT);  // Set up the mouse control pin
    digitalWrite(MOUSE_PIN, LOW);  // Ensure it starts off
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

        // **Process Audio Intensity**
        if (doc.containsKey("AudioIntensity")) {
            led_brightness = doc["AudioIntensity"];
            Serial.print("Updated Audio Intensity: ");
            Serial.println(led_brightness);
            updateAudioLEDs();
        }

        // **Process Screen Colors**
        if (doc.containsKey("LEDColors")) {
            for (int i = 0; i < NUM_COLORS; i++) {
                colors[i][0] = doc["LEDColors"][i]["G"]; // Swap Green
                colors[i][1] = doc["LEDColors"][i]["R"]; // Swap Red
                colors[i][2] = doc["LEDColors"][i]["B"]; // Keep Blue the same
            }
            Serial.println("Updated LED Colors");
            updateScreenLEDs();
        }

        // **Process Mouse Speed**
        if (doc.containsKey("MouseSpeed")) {
            mouse_speed = doc["MouseSpeed"];
            Serial.print("Mouse Speed: ");
            Serial.println(mouse_speed);
            updateMouseControl();
        }
    }
}

/** Updates LED brightness based on audio intensity */
void updateAudioLEDs() {
    strip.setBrightness(led_brightness);
    for (int i = 0; i < NUM_LEDS; i++) {
        strip.setPixelColor(i, strip.Color(45, 226, 161));  // Fixed purple color
    }
    strip.show();
}

/** Updates LEDs based on screen colors */
void updateScreenLEDs() {
    int section_size = NUM_LEDS / NUM_COLORS;
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

/** Controls a GPIO pin based on mouse speed */
void updateMouseControl() {
    if (mouse_speed > MOUSE_THRESHOLD) {
        digitalWrite(MOUSE_PIN, HIGH);  // Turn ON pin if above threshold
        Serial.println("Mouse Speed HIGH: GPIO ON");
    } else {
        digitalWrite(MOUSE_PIN, LOW);  // Turn OFF pin if below threshold
        Serial.println("Mouse Speed LOW: GPIO OFF");
    }
}