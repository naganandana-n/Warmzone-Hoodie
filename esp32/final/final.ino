#include <ArduinoJson.h>
#include <Adafruit_NeoPixel.h>

#define LED_PIN      23
#define HEATER1_PIN  14
#define HEATER2_PIN  13
#define HEATER3_PIN  12
#define VIBE1_PIN    26
#define VIBE2_PIN    27
#define NUM_LEDS     50
#define NUM_COLORS   6
#define MAX_PWM      175
#define MOUSE_SPEED_THRESHOLD 2.0  // Below this, the heater turns off [CHANGE TO CUSTOMIZE]

Adafruit_NeoPixel strip(NUM_LEDS, LED_PIN, NEO_GRB + NEO_KHZ800);

int colors[NUM_COLORS][3];
int last_colors[NUM_COLORS][3];
int led_brightness = 200;
int last_brightness = -1;
float mouse_speed = 0.0;
bool use_mouse_control = false;
int heater_values[3] = {0, 0, 0};
bool vibration_on = false;
bool screen_enabled = true;
bool audio_enabled = true;
int audio_brightness = 0;
unsigned long last_audio_time = 0;
bool received_colors = false;

// Breathing effect 
unsigned long last_breathe_update = 0;
int breathe_brightness = 0;
bool breathe_increasing = true;

// Nana Purple #E22DA1
int fallback_r = 226;
int fallback_g = 45;
int fallback_b = 161;

void setup() {
  Serial.begin(115200);

  pinMode(HEATER1_PIN, OUTPUT);
  pinMode(HEATER2_PIN, OUTPUT);
  pinMode(HEATER3_PIN, OUTPUT);
  pinMode(VIBE1_PIN, OUTPUT);
  pinMode(VIBE2_PIN, OUTPUT);

  strip.begin();
  strip.setBrightness(led_brightness);
  strip.show();
  last_audio_time = millis();
}

void loop() {
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    StaticJsonDocument<768> doc;
    DeserializationError error = deserializeJson(doc, input);

    if (error) {
      Serial.println("JSON Parse Error");
      return;
    }

    // === Brightness ===
    if (doc.containsKey("Brightness")) {
      audio_brightness = doc["Brightness"];
      if (audio_brightness > 0) {
        last_audio_time = millis();
      }
    }

    // Control Flags
    screen_enabled = doc["screen"] | true;
    audio_enabled = doc["audio"] | true;
    use_mouse_control = doc["mouse"] | false;
    vibration_on = doc["vibration"] | false;

    // Heater Values
    if (doc.containsKey("heaters")) {
      heater_values[0] = doc["heaters"][0];
      heater_values[1] = doc["heaters"][1];
      heater_values[2] = doc["heaters"][2];
    }

    // Mouse Speed
    if (doc.containsKey("MouseSpeed")) {
      mouse_speed = doc["MouseSpeed"];
    }

    // LED Colors 
    received_colors = false;
    if (doc.containsKey("LEDColors") && doc["LEDColors"].size() > 0) {
      for (int i = 0; i < NUM_COLORS; i++) {
        colors[i][0] = doc["LEDColors"][i]["G"];
        colors[i][1] = doc["LEDColors"][i]["R"];
        colors[i][2] = doc["LEDColors"][i]["B"];
      }
      received_colors = true;
    }

    updateLEDStrip();

    // Heater Logic 
    if (use_mouse_control) {
      int pwm_val = (mouse_speed < MOUSE_SPEED_THRESHOLD) ? 0 : int((mouse_speed / 5.0) * MAX_PWM);
      analogWrite(HEATER1_PIN, pwm_val);
      analogWrite(HEATER2_PIN, pwm_val);
      analogWrite(HEATER3_PIN, pwm_val);
    } else {
      analogWrite(HEATER1_PIN, heater_values[0]);
      analogWrite(HEATER2_PIN, heater_values[1]);
      analogWrite(HEATER3_PIN, heater_values[2]);
    }

    // Vibration Control
    int vib_pwm = vibration_on ? 255 : 0;
    analogWrite(VIBE1_PIN, vib_pwm);
    analogWrite(VIBE2_PIN, vib_pwm);
  } else {
    // If no data received, maintain breathing or fallback if needed
    updateLEDStrip();
  }
}

void updateLEDStrip() {
  unsigned long now = millis();
  bool use_fallback_color = false;
  bool use_breathe = false;

  // Determine fallback mode
  if (!screen_enabled || !received_colors) {
    use_fallback_color = true;
  }

  if (!audio_enabled && !screen_enabled) {
    use_breathe = true;
  } else if (audio_enabled && audio_brightness == 0 && (now - last_audio_time > 30000)) {
    // 30 sec silence, fallback to screen only
    use_fallback_color = false;
  }

  if (use_breathe) {
    // breathing color (fallback)
    if (now - last_breathe_update > 15) {
      strip.clear();
      for (int i = 0; i < NUM_LEDS; i++) {
        strip.setPixelColor(i, strip.Color((fallback_g * breathe_brightness) / 255,
                                           (fallback_r * breathe_brightness) / 255,
                                           (fallback_b * breathe_brightness) / 255));
      }
      strip.show();
      breathe_brightness += breathe_increasing ? 3 : -3;
      if (breathe_brightness >= 255) breathe_increasing = false;
      if (breathe_brightness <= 0) breathe_increasing = true;
      last_breathe_update = now;
    }
    return;
  }

  if (use_fallback_color) {
    strip.setBrightness(led_brightness);
    for (int i = 0; i < NUM_LEDS; i++) {
      strip.setPixelColor(i, strip.Color(fallback_g, fallback_r, fallback_b));
    }
    strip.show();
    return;
  }

  // Otherwise, show actual screen colors
  strip.setBrightness(led_brightness);
  int section = NUM_LEDS / NUM_COLORS;
  int extra = NUM_LEDS % NUM_COLORS;

  for (int i = 0; i < NUM_COLORS; i++) {
    for (int j = 0; j < section; j++) {
      int index = i * section + j;
      if (index < NUM_LEDS) {
        strip.setPixelColor(index, strip.Color(colors[i][0], colors[i][1], colors[i][2]));
      }
    }
  }

  for (int i = 0; i < extra; i++) {
    int index = NUM_COLORS * section + i;
    strip.setPixelColor(index, strip.Color(colors[NUM_COLORS - 1][0], colors[NUM_COLORS - 1][1], colors[NUM_COLORS - 1][2]));
  }

  strip.show();
}
