#include <WiFi.h>
#include <WebServer.h>
#include <Adafruit_NeoPixel.h>
#include <ArduinoJson.h>

#define LED_PIN 23
#define HEATER1_PIN 14
#define HEATER2_PIN 13
#define HEATER3_PIN 12
#define VIBE1_PIN 26
#define VIBE2_PIN 27
#define INV 4
#define PEB_PIN 16
#define NUM_LEDS 25
#define NUM_COLORS 6
#define MAX_PWM 175
#define MAX_BRIGHTNESS 125
#define MAX_VIB 175
#define MOUSE_SPEED_THRESHOLD 2.0

Adafruit_NeoPixel pixels(NUM_LEDS, LED_PIN, NEO_GRB + NEO_KHZ800);

const char* ssid = "warmzone";
const char* password = "12345678";

WebServer server(80);

StaticJsonDocument<3072> parsedDoc;
String rawInput = "No data yet";
String serialBuffer = "";

int colors[NUM_COLORS][3];
int audio_brightness = 0;
bool use_mouse_control = false;
bool vibration_on = false;
bool sync_with_audio = false;
int heater_values[3] = {0, 0, 0};
float mouse_speed = 0.0;
bool received_colors = false;
bool received_brightness = false;
uint8_t vibint=0;
bool lights_enabled = true;

uint8_t fallback_r = 255, fallback_g = 0, fallback_b = 127;

unsigned long last_breathe_update = 0;
int fallback_brightness = 0;
bool breathe_increasing = true;

void setup() {
  Serial.begin(115200);

  for (int pin : { HEATER1_PIN, HEATER2_PIN, HEATER3_PIN, VIBE1_PIN, VIBE2_PIN }) {
    pinMode(pin, OUTPUT);
  }
  pinMode(PEB_PIN, OUTPUT);
  digitalWrite(PEB_PIN, HIGH);
  pinMode(INV, OUTPUT);
  digitalWrite(INV, HIGH);


  pixels.begin();
  pixels.clear();
  pixels.show();

  WiFi.begin(ssid, password);
  // while (WiFi.status() != WL_CONNECTED) {
  //   delay(500);
  // }

  server.on("/", handleRoot);
  server.begin();
}

void loop() {
  readSerialJSON();
  updateLEDpixels();
  updateActuators();
  server.handleClient();
}

void readSerialJSON() {
  while (Serial.available()) {
    char ch = Serial.read();
    if (ch == '\n') {
      DeserializationError error = deserializeJson(parsedDoc, serialBuffer);
      if (!error) {
        rawInput = serialBuffer;

        audio_brightness = parsedDoc["Brightness"] | 0;
        received_brightness = parsedDoc.containsKey("Brightness");

        vibration_on = parsedDoc["vibration"] | false;
        sync_with_audio = parsedDoc["sync_with_audio"] | false;

        use_mouse_control = parsedDoc["mouse"] | false;
        mouse_speed = parsedDoc["MouseSpeed"] | 0.0;

        heater_values[0] = parsedDoc["heaters"][0] | 0;
        heater_values[1] = parsedDoc["heaters"][1] | 0;
        heater_values[2] = parsedDoc["heaters"][2] | 0;
        lights_enabled = parsedDoc["lights_enabled"] | true;

        received_colors = parsedDoc.containsKey("LEDColors");

        if (received_colors) {
          for (int i = 0; i < NUM_COLORS; i++) {
            colors[i][0] = parsedDoc["LEDColors"][i]["G"];
            colors[i][1] = parsedDoc["LEDColors"][i]["R"];
            colors[i][2] = parsedDoc["LEDColors"][i]["B"];
          }
        }
      }
      serialBuffer = "";
    } else if (ch != '\r') {
      serialBuffer += ch;
    }
  }
}

void updateLEDpixels() {
  if (!lights_enabled) {
    pixels.clear();
    pixels.show();
    return;
  }
  if (!received_colors && !received_brightness) {
    unsigned long now = millis();
    if (millis()-last_breathe_update>10)
    {
      for (int i = 0; i < NUM_LEDS; i++) {
        pixels.setPixelColor(i, pixels.Color((fallback_g * fallback_brightness * MAX_BRIGHTNESS) / 65025, (fallback_r * fallback_brightness * MAX_BRIGHTNESS) / 65025, (fallback_b * fallback_brightness * MAX_BRIGHTNESS) / 65025));
      }
      // Serial.print("R: ");
      // Serial.print((fallback_g * fallback_brightness * MAX_BRIGHTNESS) / 65025);
      // Serial.print(", G: ");
      // Serial.print((fallback_r * fallback_brightness * MAX_BRIGHTNESS) / 65025);
      // Serial.print(", B: ");
      // Serial.println((fallback_b * fallback_brightness * MAX_BRIGHTNESS) / 65025);
      
      pixels.show();
      fallback_brightness += (breathe_increasing ? 1 : -1);
      if (fallback_brightness >= 255) {breathe_increasing = false;}
      if (fallback_brightness <= 0) {breathe_increasing = true;}
      last_breathe_update = millis();
    }
  }
    else if (received_colors) {
    int section = NUM_LEDS / NUM_COLORS;
    for (int i = 0; i < NUM_COLORS; i++) {
      for (int j = 0; j < section; j++) {
        int index = i * section + j;
        if (index < NUM_LEDS) {
          pixels.setPixelColor(index, pixels.Color((colors[i][0]*0.300), (colors[i][1]*0.300), (colors[i][2]*0.300)));
        }
      }
    }
    pixels.show();
  } else if (received_brightness) {
    int scaled = map(audio_brightness, 0, 255, 15, MAX_BRIGHTNESS);
    for (int i = 0; i < NUM_LEDS; i++) {
      pixels.setPixelColor(i, pixels.Color(
        (fallback_g * scaled) / 255,
        (fallback_r * scaled) / 255,
        (fallback_b * scaled) / 255));
    }
    pixels.show();
  }
}

void updateActuators() {
  if (use_mouse_control) {
    int pwm_val = (mouse_speed < MOUSE_SPEED_THRESHOLD) ? 0 : int((mouse_speed / 5.0) * MAX_PWM);
    analogWrite(HEATER1_PIN, pwm_val);
    analogWrite(HEATER2_PIN, pwm_val);
    analogWrite(HEATER3_PIN, pwm_val);
  } else {
    for (int i = 0; i < 3; i++) {
      int mapped_pwm = 0;
      if (heater_values[i] == 1) mapped_pwm = 40;
      else if (heater_values[i] == 2) mapped_pwm = 100;
      else if (heater_values[i] == 3) mapped_pwm = 175;
      analogWrite((i == 0 ? HEATER1_PIN : (i == 1 ? HEATER2_PIN : HEATER3_PIN)), mapped_pwm);
    }
  }

  float audio_gain = 1;  // 5 * 50 = 250

//int raw = int(audio_brightness * audio_gain);
int raw = map(audio_brightness, 0, 255, 95, 255);
//raw = constrain(raw, 0, 255);

uint8_t vib_pwm = vibration_on
  ? (sync_with_audio ? raw : MAX_VIB)
  : 0;

analogWrite(VIBE1_PIN, vib_pwm);
analogWrite(VIBE2_PIN, vib_pwm);

}

void handleRoot() {
  String html = "<!DOCTYPE html><html><head><meta http-equiv='refresh' content='2'>";
  html += "<style>body{font-family:Arial;margin:20px;} pre{background:#f4f4f4;padding:10px;border-radius:10px;}</style>";
  html += "<h2>ESP32 Serial JSON Viewer</h2>";
  html += "<h3>Raw Input:</h3><pre>" + rawInput + "</pre>";
  html += "<h3>Parsed Values:</h3><pre>";

  for (JsonPair kv : parsedDoc.as<JsonObject>()) {
    html += kv.key().c_str();
    html += ": ";
    html += kv.value().as<String>();
    html += "\n";
  }

  html += "</pre></body></html>";
  server.send(200, "text/html", html);
}