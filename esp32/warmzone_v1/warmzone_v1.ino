#include <WiFi.h>
#include <WebServer.h>
#include <Adafruit_NeoPixel.h>

#define PIN 23 // NeoPixel
#define HP1 13
#define HP2 12
#define HP3 14
#define PEB 16
#define INV 4
#define VB1 27
#define VB2 26
#define NUMPIXELS 60

const char* ssid = "warmzone";
const char* password = "12345678";

WebServer server(80);
Adafruit_NeoPixel pixels(NUMPIXELS, PIN, NEO_GRB + NEO_KHZ800);

int heatPadIntensity[3] = {0, 0, 0};
bool pebOn = true, invOn = true, vb1On = false, vb2On = false;

String neoMode = "breathe";
uint8_t colorR = 255, colorG = 0, colorB = 127;
unsigned long lastEffectTime = 0;
int breatheStep = 0;
bool breatheUp = true;
// Removed reduced-step array for smoother breathing


#define MAX_BRIGHTNESS 125

// Brand Colors
const char* brandPurple = "#8e44ad";
const char* brandPink = "#fd79a8";

unsigned long vibLastUpdate = 0;
bool vibPulseState = false;
int vibrationMode = 0; // 0 = manual, 1 = single, 2 = double, 3 = triple
int pulseCount = 0; // false = manual, true = pulsating

void setup() {
  Serial.begin(115200);
  for (int pin : {HP1, HP2, HP3, PEB, INV, VB1, VB2}) {
    pinMode(pin, OUTPUT);
  }

  pixels.begin();
  pixels.clear(); pixels.show();

  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected! IP address: " + WiFi.localIP().toString());

  server.on("/", handleRoot);
  server.on("/set", handleSet);
  server.on("/status", handleStatus);
  server.begin();
}

void loop() {
  server.handleClient();

  // NeoPixel modes
  if (neoMode == "static") {
    for (int i = 0; i < NUMPIXELS; i++) {
      pixels.setPixelColor(i, pixels.Color((colorG * MAX_BRIGHTNESS) / 255, (colorR * MAX_BRIGHTNESS) / 255, (colorB * MAX_BRIGHTNESS) / 255));
    }
    pixels.show();
  } else if (neoMode == "off") {
    pixels.clear();
    pixels.show();
  } else if (neoMode == "cycle") {
    if (millis() - lastEffectTime > 20) {
      static uint16_t j = 0;
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
        pixels.setPixelColor(i, pixels.Color((colorG * brightness * MAX_BRIGHTNESS) / 65025, (colorR * brightness * MAX_BRIGHTNESS) / 65025, (colorB * brightness * MAX_BRIGHTNESS) / 65025));
      }
      pixels.show();

      if (increasing) {
        brightness++;
        if (brightness >= 255) increasing = false;
      } else {
        brightness--;
        if (brightness <= 0) increasing = true;
      }
      lastEffectTime = millis();
    }
  }

  // Outputs
  analogWrite(HP1, heatPadIntensity[0]);
  analogWrite(HP2, heatPadIntensity[1]);
  analogWrite(HP3, heatPadIntensity[2]);
  digitalWrite(PEB, pebOn ? HIGH : LOW);
  analogWrite(INV, invOn ? 255 : 0);

  // Vibration Motor Control
  if (vibrationMode == 0) {
    analogWrite(VB1, vb1On ? 255 : 0);
    analogWrite(VB2, vb2On ? 255 : 0);
  } else {
    unsigned long pulseDelay = 300;
    if (vibrationMode == 2) pulseDelay = 200;
    if (vibrationMode == 3) pulseDelay = 120;

    if (millis() - vibLastUpdate > pulseDelay) {
      vibPulseState = !vibPulseState;
      analogWrite(VB1, vibPulseState ? 255 : 0);
      analogWrite(VB2, vibPulseState ? 255 : 0);
      pulseCount++;

      int limit = (vibrationMode + 1) * 2;
      if (pulseCount >= limit) {
        pulseCount = 0;
        vibPulseState = false;
        analogWrite(VB1, 0);
        analogWrite(VB2, 0);
        vibLastUpdate = millis() + 600; // rest period
      } else {
        vibLastUpdate = millis();
      }
    }
  }
}

  

void handleRoot() {
  server.send(200, "text/html", R"rawliteral(
    <!DOCTYPE html><html><head><meta name='viewport' content='width=device-width, initial-scale=1'>
    <title>Warmzone</title><style>
    body { font-family: Arial; background: #f4f4f4; padding: 20px; display: flex; justify-content: center; }
    .container { max-width: 500px; background: white; padding: 20px; border-radius: 12px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
    h1 { text-align: center; color: #8e44ad; }
    h2 { margin-top: 25px; color: #333; }
    select, button, input[type=color] {
      padding: 8px;
      margin: 5px;
      font-size: 16px;
      border-radius: 10px;
      border: 1px solid #ccc;
    }
    button {
      background-color: #fd79a8;
      color: white;
      border: none;
      cursor: pointer;
    }
    label { display: inline-block; width: 50px; }
    .status { margin-top: 10px; font-size: 14px; color: #333; }
    </style></head><body>
    <div class='container'>
    <h1>Warmzone</h1>

    <h2>Heating Pads</h2>
    HP1: <select onchange="send('hp1', this.value)">
      <option value='0' selected>Off</option><option value='40'>Low</option><option value='100'>Medium</option><option value='175'>High</option>
    </select>
    HP2: <select onchange="send('hp2', this.value)">
      <option value='0' selected>Off</option><option value='40'>Low</option><option value='100'>Medium</option><option value='175'>High</option>
    </select>
    HP3: <select onchange="send('hp3', this.value)">
      <option value='0' selected>Off</option><option value='40'>Low</option><option value='100'>Medium</option><option value='175'>High</option>
    </select>

    <h2>NeoPixels</h2>
    Mode:
    <select onchange="send('mode', this.value)">
      <option value='off'>Off</option>
      <option value='static' selected>Static</option>
      <option value='cycle'>Cycle</option>
      <option value='breathe'>Breathe</option>
    </select><br>
    Color: <input type='color' onchange='setColor(this.value)'>

    <h2>Outputs</h2>
    <label>PEB</label>
    <button onclick="send('peb','1')">ON</button>
    <button onclick="send('peb','0')">OFF</button><br>
    <label>INV</label>
    <button onclick="send('inv','1')">ON</button>
    <button onclick="send('inv','0')">OFF</button><br>

    <h2>Vibration Motors</h2>
    Mode:
    <select onchange="send('vibmode', this.value)">
      <option value='0'>Manual</option>
      <option value='1'>Pulsating - Single</option>
      <option value='2'>Pulsating - Double</option>
      <option value='3'>Pulsating - Triple</option>
    </select><br>
    VB1: <button onclick="send('vb1','1')">ON</button>
    <button onclick="send('vb1','0')">OFF</button><br>
    VB2: <button onclick="send('vb2','1')">ON</button>
    <button onclick="send('vb2','0')">OFF</button><br>

    <div class='status' id='statusBox'></div>
    <script>
      function send(key, val) {
        fetch('/set?' + key + '=' + val).then(() => getStatus());
      }
      function setColor(hex) {
        const r = parseInt(hex.substr(1,2), 16);
        const g = parseInt(hex.substr(3,2), 16);
        const b = parseInt(hex.substr(5,2), 16);
        send('r', r); send('g', g); send('b', b);
      }
      function getStatus() {
        fetch('/status').then(res => res.text()).then(text => {
          document.getElementById('statusBox').innerText = text;
        });
      }
      setInterval(getStatus, 2000);
      getStatus();
    </script>
    </div></body></html>
  )rawliteral");
}

void handleSet() {
  if (server.hasArg("hp1")) heatPadIntensity[0] = server.arg("hp1").toInt();
  if (server.hasArg("hp2")) heatPadIntensity[1] = server.arg("hp2").toInt();
  if (server.hasArg("hp3")) heatPadIntensity[2] = server.arg("hp3").toInt();
  if (server.hasArg("peb")) pebOn = server.arg("peb") == "1";
  if (server.hasArg("inv")) invOn = server.arg("inv") == "1";
  if (server.hasArg("vb1")) vb1On = server.arg("vb1") == "1";
  if (server.hasArg("vb2")) vb2On = server.arg("vb2") == "1";
  if (server.hasArg("mode")) neoMode = server.arg("mode");
  if (server.hasArg("r")) colorR = server.arg("r").toInt();
  if (server.hasArg("g")) colorG = server.arg("g").toInt();
  if (server.hasArg("b")) colorB = server.arg("b").toInt();
  if (server.hasArg("vibmode")) vibrationMode = server.arg("vibmode").toInt();
  Serial.println("[SET] Command received");
  server.send(200, "text/plain", "OK");
}

void handleStatus() {
String status = "HP1: " + String(heatPadIntensity[0]) + ", " +
                "HP2: " + String(heatPadIntensity[1]) + ", " +
                "HP3: " + String(heatPadIntensity[2]) + "\\n" +
                "PEB: " + String(pebOn ? "ON" : "OFF") + ", " +
                "INV: " + String(invOn ? "ON" : "OFF") + ", " +
                "VB1: " + String(vb1On ? "ON" : "OFF") + ", " +
                "VB2: " + String(vb2On ? "ON" : "OFF") + "\\n" +
                "NeoPixel Mode: " + neoMode + ", Color: RGB(" +
                String(colorR) + "," + String(colorG) + "," + String(colorB) + ")" + "\\n" +
                "Vibration Mode: " + String(vibrationMode ? "Pulsating" : "Manual");

  server.send(200, "text/plain", status);
}
