/*

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
#define DEFAULT_BRIGHTNESS 200   // Max brightness when audio is loudest
#define MOUSE_SPEED_THRESHOLD 2.0  // Below this, the heater turns off [CHANGE TO CUSTOMIZE]

Adafruit_NeoPixel strip(NUM_LEDS, LED_PIN, NEO_GRB + NEO_KHZ800);

int colors[NUM_COLORS][3];
int last_colors[NUM_COLORS][3];
int led_brightness = DEFAULT_BRIGHTNESS;
int last_brightness = -1;
float mouse_speed = 0.0;
bool use_mouse_control = false;
int heater_values[3] = {0, 0, 0};
bool vibration_on = false;
bool screen_enabled = true;
bool audio_enabled = true;
int audio_brightness = 0;
unsigned long last_audio_nonzero_time = 0;
const unsigned long AUDIO_TIMEOUT = 15000;  // 15s timeout for audio (so that if audio is out for 15s, colors can still show)
bool received_colors = false;

// Breathing effect 
const int BREATHE_STEP = 3;          // How much brightness changes per step (lower = smoother)
const int BREATHE_INTERVAL = 15;     // Delay (ms) between brightness changes
const unsigned long FALLBACK_TIMEOUT = 10000; // 10 seconds of inactivity triggers fallback (in ms)
unsigned long last_breathe_update = 0;
int breathe_brightness = 0;
bool breathe_increasing = true;

// Nana Purple #E22DA1
// SWITCHED RED WITH GREEN 
int fallback_r = 45;
int fallback_g = 226;
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
last_audio_nonzero_time = millis();
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
  last_audio_nonzero_time = millis();
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
        colors[i][0] = doc["LEDColors"][i]["R"];
        colors[i][1] = doc["LEDColors"][i]["G"];
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

  // 1: Update LED brightness based on audio (if enabled)
  if (audio_enabled) {
    int min_brightness = 0; // Change to 50 if you want minimum brightness
    led_brightness = map(audio_brightness, 0, 255, min_brightness, DEFAULT_BRIGHTNESS);
  }

  // 2: Evaluate time since last non-zero audio
  bool audio_timed_out = (audio_enabled && audio_brightness == 0 &&
                          (now - last_audio_nonzero_time > AUDIO_TIMEOUT));


  // Case 1: If both audio AND screen are OFF → start breathing immediately
  if (!audio_enabled && !screen_enabled) {
    use_breathe = true;
  }

  // Case 2: Audio is ON but timed out
  else if (audio_timed_out) {
    if (screen_enabled && received_colors) {
      // Show screen colors instead of audio (fallback to screen)
      use_breathe = false;
      use_fallback_color = false;
    } else {
      // No screen or invalid → breathe
      use_breathe = true;
    }
  }

  // Case 3: Screen is ON but no valid colors → fallback color
  else if (screen_enabled && !received_colors) {
    use_fallback_color = true;
  }

  // Case 4: Screen is OFF → fallback color (even if audio is on)
  else if (!screen_enabled) {
    use_fallback_color = true;
  }

  // MODE: Breathing
  if (use_breathe) {
    if (now - last_breathe_update > BREATHE_INTERVAL) {
      strip.clear();
      strip.setBrightness(led_brightness);
      for (int i = 0; i < NUM_LEDS; i++) {
        strip.setPixelColor(i, strip.Color((fallback_g * breathe_brightness) / 255,
                                           (fallback_r * breathe_brightness) / 255,
                                           (fallback_b * breathe_brightness) / 255));
      }
      strip.show();
      breathe_brightness += breathe_increasing ? BREATHE_STEP : -BREATHE_STEP;
      breathe_brightness = constrain(breathe_brightness, 0, 255);
      if (breathe_brightness == 255) breathe_increasing = false;
      if (breathe_brightness == 0) breathe_increasing = true;
      last_breathe_update = now;
    }
    return;
  }

  // MODE: Fallback color
  if (use_fallback_color) {
    strip.setBrightness(led_brightness);
    for (int i = 0; i < NUM_LEDS; i++) {
      strip.setPixelColor(i, strip.Color(fallback_r, fallback_g, fallback_b));
    }
    strip.show();
    return;
  }

  // MODE: Show screen colors
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

*/

/*
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
#define DEFAULT_BRIGHTNESS 200   // Max brightness when audio is loudest

Adafruit_NeoPixel strip(NUM_LEDS, LED_PIN, NEO_GRB + NEO_KHZ800);

int colors[NUM_COLORS][3];
int last_colors[NUM_COLORS][3];
int led_brightness = DEFAULT_BRIGHTNESS;
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
const int BREATHE_STEP = 3;          // How much brightness changes per step
const int BREATHE_INTERVAL = 15;     // Delay (ms) between brightness changes
const unsigned long FALLBACK_TIMEOUT = 10000; // 10 seconds of inactivity triggers fallback
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

  // Dynamically update LED brightness based on audio
if (audio_enabled) {
  // Scale between 50 and DEFAULT_BRIGHTNESS (min brightness to avoid full black)
  int min_brightness = 0;
  led_brightness = map(audio_brightness, 0, 255, min_brightness, DEFAULT_BRIGHTNESS);
}

  // Determine fallback mode
  if (!screen_enabled || !received_colors) {
    use_fallback_color = true;
  }

    // Trigger breathing mode after 10s of no audio and no screen colors
  if ((!audio_enabled || audio_brightness == 0) &&
      (!screen_enabled || !received_colors) &&
      (now - last_audio_time > FALLBACK_TIMEOUT)) {
    use_breathe = true;
  }

  if (use_breathe) {
    // breathing color (fallback)
    if (now - last_breathe_update > BREATHE_INTERVAL) {
      strip.clear();
      for (int i = 0; i < NUM_LEDS; i++) {
        strip.setPixelColor(i, strip.Color((fallback_g * breathe_brightness) / 255,
                                           (fallback_r * breathe_brightness) / 255,
                                           (fallback_b * breathe_brightness) / 255));
      }
      strip.show();
      breathe_brightness += breathe_increasing ? BREATHE_STEP : -BREATHE_STEP;
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


#include <ArduinoJson.h>
#include <Adafruit_NeoPixel.h>

#define LED_PIN      23
#define HEATER1_PIN  14
#define HEATER2_PIN  13
#define HEATER3_PIN  12
#define VIBE1_PIN    26
#define VIBE2_PIN    27
#define NUM_LEDS     60
#define NUM_COLORS   6
#define MAX_PWM      175
#define DEFAULT_BRIGHTNESS 200 // maximum brightness when audio intensity is at 255
#define MOUSE_SPEED_THRESHOLD 2.0 // mouse threshold

Adafruit_NeoPixel strip(NUM_LEDS, LED_PIN, NEO_GRB + NEO_KHZ800);

int colors[NUM_COLORS][3];
int led_brightness = DEFAULT_BRIGHTNESS;
float mouse_speed = 0.0;
int heater_values[3] = {0, 0, 0};
bool use_mouse_control = false;
bool vibration_on = false;
bool screen_enabled = false;
bool audio_enabled = false;
bool received_colors = false;
int audio_brightness = 0;
unsigned long last_audio_time = 0;

bool sync_with_audio = false;

// Breathing effect control
const int MIN_BREATHE = 20;       // Minimum brightness
int breathe_brightness = MIN_BREATHE;
bool breathe_increasing = true;
const int BREATHE_STEP = 3;       // Smaller = slower breathing
const int MAX_BREATHE = 200;      // Maximum brightness
unsigned long last_breathe_update = 0;
const int BREATHE_DELAY = 15;     // ms between breathe steps

// Default fallback color (#E22DA1)
// switched up r ang g
int fallback_r = 45;
int fallback_g = 226;
int fallback_b = 161;

void setup() {
  Serial.begin(115200);

  pinMode(HEATER1_PIN, OUTPUT);
  pinMode(HEATER2_PIN, OUTPUT);
  pinMode(HEATER3_PIN, OUTPUT);
  pinMode(VIBE1_PIN, OUTPUT);
  pinMode(VIBE2_PIN, OUTPUT);

  strip.begin();
  strip.setBrightness(DEFAULT_BRIGHTNESS);
  strip.show();

  last_audio_time = millis();
}

void loop() {
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    Serial.print("[Received JSON]: ");
    Serial.println(input);  // 👈 This shows raw input

    StaticJsonDocument<768> doc;
    DeserializationError error = deserializeJson(doc, input);
    if (error) {
      Serial.print("[Parse Error]: ");
      Serial.println(error.c_str());
      return;
    }

    audio_enabled = doc["audio"] | false;
    screen_enabled = doc["screen"] | false;
    use_mouse_control = doc["mouse"] | false;
    vibration_on = doc["vibration"] | false;
    sync_with_audio = doc["sync_with_audio"] | false;

    Serial.print("[Flags] audio: ");
    Serial.print(audio_enabled);
    Serial.print(" | screen: ");
    Serial.print(screen_enabled);
    Serial.print(" | mouse: ");
    Serial.print(use_mouse_control);
    Serial.print(" | vibration: ");
    Serial.println(vibration_on);

    if (doc.containsKey("heaters")) {
      heater_values[0] = doc["heaters"][0];
      heater_values[1] = doc["heaters"][1];
      heater_values[2] = doc["heaters"][2];
      Serial.printf("Heaters: %d %d %d\n", heater_values[0], heater_values[1], heater_values[2]);
    }

    if (doc.containsKey("MouseSpeed")) {
      mouse_speed = doc["MouseSpeed"];
      Serial.print("Mouse speed: ");
      Serial.println(mouse_speed);
    }

    if (doc.containsKey("Brightness")) {
      audio_brightness = doc["Brightness"];
      Serial.print("Audio Brightness: ");
      Serial.println(audio_brightness);
      if (audio_brightness > 0) {
        last_audio_time = millis();
      }
    }

    received_colors = false;
    if (doc.containsKey("LEDColors") && doc["LEDColors"].size() > 0) {
      for (int i = 0; i < NUM_COLORS; i++) {
        colors[i][0] = doc["LEDColors"][i]["G"];
        colors[i][1] = doc["LEDColors"][i]["R"];
        colors[i][2] = doc["LEDColors"][i]["B"];
      }
      received_colors = true;
      Serial.println("Received LED Colors.");
    }

    updateLEDStrip();
    updateActuators();
  } else {
    updateLEDStrip();  // Show fallback or breathing if no input
  }
}

void updateLEDStrip() {
  unsigned long now = millis();
  bool audio_timeout = audio_enabled && (audio_brightness == 0) && (now - last_audio_time > 10000); // 10,000 ms (10 sec) is the time after which audio is considered time out.
  bool use_screen_colors = screen_enabled && received_colors;
  bool use_audio_only = audio_enabled && !screen_enabled;

  int brightness = DEFAULT_BRIGHTNESS;
  if (audio_enabled && audio_brightness > 0) {
    brightness = map(audio_brightness, 0, 255, 0, DEFAULT_BRIGHTNESS);
  }

  strip.setBrightness(brightness);

  if (!audio_enabled && !screen_enabled) {
    // Case 1: No audio or screen
    fillWithFallbackColor();
  } else if (use_screen_colors && (!audio_enabled || audio_timeout)) {
    // Case 2 or Case 5: screen on and either no audio or audio timed out
    fillWithScreenColors();
  } else if (use_audio_only) {
    // Case 3: Only audio
    fillWithFallbackColor();
  } else if (screen_enabled && audio_enabled && received_colors) {
    // Case 4: Both
    fillWithScreenColors();
  } else {
    fillWithFallbackColor();
  }
}

/*
void fillWithFallbackColor() {
  Serial.println("Fallback breathing mode active");
  unsigned long now = millis();

  // If we are in breathing mode (no audio or screen enabled)
  if (!audio_enabled && !screen_enabled) {
    if (now - last_breathe_update > BREATHE_DELAY) {
      breathe_brightness += breathe_increasing ? BREATHE_STEP : -BREATHE_STEP;
      if (breathe_brightness >= MAX_BREATHE) breathe_increasing = false;
      if (breathe_brightness <= MIN_BREATHE) breathe_increasing = true;
      last_breathe_update = now;
    }

    strip.setBrightness(breathe_brightness);
  } else {
    strip.setBrightness(led_brightness);
  }

  for (int i = 0; i < NUM_LEDS; i++) {
    strip.setPixelColor(i, strip.Color(fallback_g, fallback_r, fallback_b));
  }
  strip.show();
}


void fillWithFallbackColor() {
  static int brightness = 0;
  static bool increasing = true;
  unsigned long now = millis();

  Serial.println("Fallback breathing mode active");

  if (now - last_breathe_update > 10) {
    for (int i = 0; i < NUM_LEDS; i++) {
      strip.setPixelColor(i, strip.Color(
        (fallback_g * brightness * 125) / 65025,
        (fallback_r * brightness * 125) / 65025,
        (fallback_b * brightness * 125) / 65025
      ));
    }
    strip.show();

    if (increasing) {
      brightness++;
      if (brightness >= 255) increasing = false;
    } else {
      brightness--;
      if (brightness <= 0) increasing = true;
    }
    last_breathe_update = now;
  }
}

void fillWithScreenColors() {
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

void updateActuators() {
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

  int vib_pwm = 0;
  if (vibration_on) {
    vib_pwm = sync_with_audio ? audio_brightness : 255;  // 0–255 intensity if syncing - this is the vibration strength
    // vib_pwm = sync_with_audio ? max(audio_brightness, 30) : 255; // adds minimum vibration - even if the audio is 0
  }

  analogWrite(VIBE1_PIN, vib_pwm);
  analogWrite(VIBE2_PIN, vib_pwm);
}

*/

/*

// WORKING VIBRATION

#include <ArduinoJson.h>
#include <Adafruit_NeoPixel.h>

#define LED_PIN      23
#define HEATER1_PIN  14
#define HEATER2_PIN  13
#define HEATER3_PIN  12
#define VIBE1_PIN    26
#define VIBE2_PIN    27
#define NUM_LEDS     60
#define NUM_COLORS   6
#define MAX_PWM      175
#define MAX_BRIGHTNESS 125
#define MOUSE_SPEED_THRESHOLD 2.0

Adafruit_NeoPixel strip(NUM_LEDS, LED_PIN, NEO_GRB + NEO_KHZ800);

int colors[NUM_COLORS][3];
int audio_brightness = 0;
bool use_mouse_control = false;
bool vibration_on = false;
bool sync_with_audio = false;
int heater_values[3] = {0, 0, 0};
float mouse_speed = 0.0;
bool screen_enabled = false, audio_enabled = false;
bool received_colors = false;

// Fallback color
int fallback_r = 45, fallback_g = 226, fallback_b = 161;

// Breathing control
unsigned long last_breathe_update = 0;
int fallback_brightness = 0;
bool breathe_increasing = true;

void setup() {
  Serial.begin(115200);
  for (int pin : {HEATER1_PIN, HEATER2_PIN, HEATER3_PIN, VIBE1_PIN, VIBE2_PIN}) {
    pinMode(pin, OUTPUT);
  }
  strip.begin();
  strip.clear();
  strip.show();
}

void loop() {
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    StaticJsonDocument<768> doc;
    DeserializationError error = deserializeJson(doc, input);
    if (error) return;

    audio_enabled = doc["audio"] | false;
    screen_enabled = doc["screen"] | false;
    use_mouse_control = doc["mouse"] | false;
    vibration_on = doc["vibration"] | false;
    sync_with_audio = doc["sync_with_audio"] | false;

    if (doc.containsKey("heaters")) {
      heater_values[0] = doc["heaters"][0];
      heater_values[1] = doc["heaters"][1];
      heater_values[2] = doc["heaters"][2];
    }

    if (doc.containsKey("MouseSpeed")) {
      mouse_speed = doc["MouseSpeed"];
    }

    if (doc.containsKey("Brightness")) {
      audio_brightness = doc["Brightness"];
    }

    if (doc.containsKey("LEDColors") && doc["LEDColors"].size() > 0) {
      for (int i = 0; i < NUM_COLORS; i++) {
        colors[i][0] = doc["LEDColors"][i]["G"];
        colors[i][1] = doc["LEDColors"][i]["R"];
        colors[i][2] = doc["LEDColors"][i]["B"];
      }
      received_colors = true;
    }
  }

  updateLEDStrip();
  updateActuators();
}

void updateLEDStrip() {
  if (!audio_enabled && !screen_enabled) {
    // Fallback breathing mode
    unsigned long now = millis();
    if (now - last_breathe_update > 10) {
      for (int i = 0; i < NUM_LEDS; i++) {
        strip.setPixelColor(i, strip.Color(
          (fallback_g * fallback_brightness * MAX_BRIGHTNESS) / 65025,
          (fallback_r * fallback_brightness * MAX_BRIGHTNESS) / 65025,
          (fallback_b * fallback_brightness * MAX_BRIGHTNESS) / 65025));
      }
      strip.show();
      fallback_brightness += (breathe_increasing ? 1 : -1);
      if (fallback_brightness >= 255) breathe_increasing = false;
      if (fallback_brightness <= 0) breathe_increasing = true;
      last_breathe_update = now;
    }
  } else if (screen_enabled && received_colors) {
    int section = NUM_LEDS / NUM_COLORS;
    for (int i = 0; i < NUM_COLORS; i++) {
      for (int j = 0; j < section; j++) {
        int index = i * section + j;
        if (index < NUM_LEDS) {
          strip.setPixelColor(index, strip.Color(colors[i][0], colors[i][1], colors[i][2]));
        }
      }
    }
    strip.show();
  } else {
    // Audio fallback if audio enabled
    for (int i = 0; i < NUM_LEDS; i++) {
      int scaled = map(audio_brightness, 0, 255, 0, MAX_BRIGHTNESS);
      strip.setPixelColor(i, strip.Color((fallback_g * scaled) / 255, (fallback_r * scaled) / 255, (fallback_b * scaled) / 255));
    }
    strip.show();
  }
}

void updateActuators() {
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

  int vib_pwm = (vibration_on ? (sync_with_audio ? audio_brightness : 255) : 0);
  analogWrite(VIBE1_PIN, vib_pwm);
  analogWrite(VIBE2_PIN, vib_pwm);
}

*/
#include <ArduinoJson.h>
#include <Adafruit_NeoPixel.h>

#define LED_PIN      23
#define HEATER1_PIN  14
#define HEATER2_PIN  13
#define HEATER3_PIN  12
#define VIBE1_PIN    26
#define VIBE2_PIN    27
#define NUMPIXELS    60
#define MAX_PWM      175
#define MAX_BRIGHTNESS 125
#define MOUSE_SPEED_THRESHOLD 2.0

Adafruit_NeoPixel pixels(NUMPIXELS, LED_PIN, NEO_GRB + NEO_KHZ800);

// State
float mouse_speed = 0.0;
int heater_values[3] = {0, 0, 0};
bool use_mouse_control = false;
bool vibration_on = false;
bool sync_with_audio = false;

String neoMode = "static";
uint8_t colorR = 255, colorG = 0, colorB = 0;
unsigned long lastEffectTime = 0;

void setup() {
  Serial.begin(115200);
  for (int pin : {HEATER1_PIN, HEATER2_PIN, HEATER3_PIN, VIBE1_PIN, VIBE2_PIN}) {
    pinMode(pin, OUTPUT);
  }
  pixels.begin();
  pixels.clear();
  pixels.show();
}

void loop() {
  // Receive JSON
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    StaticJsonDocument<768> doc;
    if (deserializeJson(doc, input)) return;

    use_mouse_control = doc["mouse"] | false;
    vibration_on = doc["vibration"] | false;
    sync_with_audio = doc["sync_with_audio"] | false;

    if (doc.containsKey("heaters")) {
      heater_values[0] = doc["heaters"][0];
      heater_values[1] = doc["heaters"][1];
      heater_values[2] = doc["heaters"][2];
    }

    if (doc.containsKey("MouseSpeed")) {
      mouse_speed = doc["MouseSpeed"];
    }

    if (doc.containsKey("mode")) neoMode = doc["mode"].as<String>();
    if (doc.containsKey("r")) colorR = doc["r"];
    if (doc.containsKey("g")) colorG = doc["g"];
    if (doc.containsKey("b")) colorB = doc["b"];
  }

  updateNeoPixels();
  updateActuators();
}

void updateNeoPixels() {
  if (neoMode == "static") {
    for (int i = 0; i < NUMPIXELS; i++) {
      pixels.setPixelColor(i, pixels.Color(
        (colorG * MAX_BRIGHTNESS) / 255,
        (colorR * MAX_BRIGHTNESS) / 255,
        (colorB * MAX_BRIGHTNESS) / 255));
    }
    pixels.show();

  } else if (neoMode == "off") {
    pixels.clear();
    pixels.show();

  } else if (neoMode == "cycle") {
    static uint16_t j = 0;
    if (millis() - lastEffectTime > 20) {
      for (int i = 0; i < NUMPIXELS; i++) {
        pixels.setPixelColor(i, pixels.gamma32(pixels.ColorHSV((i * 256 + j) & 65535)));
      }
      pixels.show();
      j++;
      lastEffectTime = millis();
    }

  } else if (neoMode == "breathe") {
    static int brightness = 0;
    static bool increasing = true;
    if (millis() - lastEffectTime > 10) {
      for (int i = 0; i < NUMPIXELS; i++) {
        pixels.setPixelColor(i, pixels.Color(
          (colorG * brightness * MAX_BRIGHTNESS) / 65025,
          (colorR * brightness * MAX_BRIGHTNESS) / 65025,
          (colorB * brightness * MAX_BRIGHTNESS) / 65025));
      }
      pixels.show();

      brightness += increasing ? 1 : -1;
      if (brightness >= 255) increasing = false;
      if (brightness <= 0) increasing = true;

      lastEffectTime = millis();
    }
  }
}

void updateActuators() {
  int heater_pwm = 0;
  if (use_mouse_control) {
    heater_pwm = (mouse_speed < MOUSE_SPEED_THRESHOLD) ? 0 : int((mouse_speed / 5.0) * MAX_PWM);
    analogWrite(HEATER1_PIN, heater_pwm);
    analogWrite(HEATER2_PIN, heater_pwm);
    analogWrite(HEATER3_PIN, heater_pwm);
  } else {
    analogWrite(HEATER1_PIN, heater_values[0]);
    analogWrite(HEATER2_PIN, heater_values[1]);
    analogWrite(HEATER3_PIN, heater_values[2]);
  }

  int vib_pwm = vibration_on ? (sync_with_audio ? 100 : 255) : 0;
  analogWrite(VIBE1_PIN, vib_pwm);
  analogWrite(VIBE2_PIN, vib_pwm);
}

/*

#include <ArduinoJson.h>
#include <Adafruit_NeoPixel.h>

#define LED_PIN      23
#define HEATER1_PIN  14
#define HEATER2_PIN  13
#define HEATER3_PIN  12
#define VIBE1_PIN    26
#define VIBE2_PIN    27
#define PEB_PIN      16  // LED strip power enable pin

#define NUM_LEDS     50
#define NUM_COLORS   6
#define MAX_PWM      175
#define DEFAULT_BRIGHTNESS 200
#define MOUSE_SPEED_THRESHOLD 2.0

Adafruit_NeoPixel strip(NUM_LEDS, LED_PIN, NEO_GRB + NEO_KHZ800);

int colors[NUM_COLORS][3];
int led_brightness = DEFAULT_BRIGHTNESS;
float mouse_speed = 0.0;
int heater_values[3] = {0, 0, 0};
bool use_mouse_control = false;
bool vibration_on = false;
bool screen_enabled = false;
bool audio_enabled = false;
bool received_colors = false;
int audio_brightness = 0;
unsigned long last_audio_time = 0;

// Breathing effect control
int breathe_brightness = 0;
bool breathe_increasing = true;
const int BREATHE_STEP = 3;
const int MIN_BREATHE = 20;
const int MAX_BREATHE = 200;
unsigned long last_breathe_update = 0;
const int BREATHE_DELAY = 15;

// Default fallback color (#E22DA1)
int fallback_r = 45;
int fallback_g = 226;
int fallback_b = 161;

void setup() {
  Serial.begin(115200);

  pinMode(HEATER1_PIN, OUTPUT);
  pinMode(HEATER2_PIN, OUTPUT);
  pinMode(HEATER3_PIN, OUTPUT);
  pinMode(VIBE1_PIN, OUTPUT);
  pinMode(VIBE2_PIN, OUTPUT);
  pinMode(PEB_PIN, OUTPUT);
  digitalWrite(PEB_PIN, HIGH);  // Power on the LED strip

  strip.begin();
  strip.setBrightness(DEFAULT_BRIGHTNESS);
  strip.show();

  last_audio_time = millis();
}

void loop() {
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    StaticJsonDocument<768> doc;
    DeserializationError error = deserializeJson(doc, input);
    if (error) return;

    audio_enabled = doc["audio"] | false;
    screen_enabled = doc["screen"] | false;
    use_mouse_control = doc["mouse"] | false;
    vibration_on = doc["vibration"] | false;

    if (doc.containsKey("heaters")) {
      heater_values[0] = doc["heaters"][0];
      heater_values[1] = doc["heaters"][1];
      heater_values[2] = doc["heaters"][2];
    }

    if (doc.containsKey("MouseSpeed")) {
      mouse_speed = doc["MouseSpeed"];
    }

    if (doc.containsKey("Brightness")) {
      audio_brightness = doc["Brightness"];
      if (audio_brightness > 0) {
        last_audio_time = millis();
      }
    }

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
    updateActuators();
  } else {
    updateLEDStrip();
  }
}

void updateLEDStrip() {
  unsigned long now = millis();
  bool audio_timeout = audio_enabled && (audio_brightness == 0) && (now - last_audio_time > 10000);
  bool use_screen_colors = screen_enabled && received_colors;
  bool use_audio_only = audio_enabled && !screen_enabled;

  int brightness = DEFAULT_BRIGHTNESS;
  if (audio_enabled && audio_brightness > 0) {
    brightness = map(audio_brightness, 0, 255, 0, DEFAULT_BRIGHTNESS);
  }
  strip.setBrightness(brightness);

  if (!audio_enabled && !screen_enabled) {
    fillWithFallbackColor();
  } else if (use_screen_colors && (!audio_enabled || audio_timeout)) {
    fillWithScreenColors();
  } else if (use_audio_only) {
    fillWithFallbackColor();
  } else if (screen_enabled && audio_enabled && received_colors) {
    fillWithScreenColors();
  } else {
    fillWithFallbackColor();
  }
}

void fillWithFallbackColor() {
  unsigned long now = millis();
  if (!audio_enabled && !screen_enabled) {
    if (now - last_breathe_update > BREATHE_DELAY) {
      breathe_brightness += breathe_increasing ? BREATHE_STEP : -BREATHE_STEP;
      if (breathe_brightness >= MAX_BREATHE) breathe_increasing = false;
      if (breathe_brightness <= MIN_BREATHE) breathe_increasing = true;
      last_breathe_update = now;
    }
    strip.setBrightness(breathe_brightness);
  } else {
    strip.setBrightness(led_brightness);
  }

  for (int i = 0; i < NUM_LEDS; i++) {
    strip.setPixelColor(i, strip.Color(fallback_g, fallback_r, fallback_b));
  }
  strip.show();
}

void fillWithScreenColors() {
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

void updateActuators() {
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

  int vib_pwm = vibration_on ? 255 : 0;
  analogWrite(VIBE1_PIN, vib_pwm);
  analogWrite(VIBE2_PIN, vib_pwm);
}


*/