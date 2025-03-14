#define LED_BUILTIN 2  // Onboard LED is usually on GPIO2

void setup() {
    pinMode(LED_BUILTIN, OUTPUT);  // Set LED as output
    Serial.begin(115200);
    Serial.println("✅ ESP32 LED Blink Test Starting...");
}

void loop() {
    Serial.println("LED ON");
    digitalWrite(LED_BUILTIN, HIGH);  // Turn LED ON
    delay(500);  // Wait 500ms

    Serial.println("LED OFF");
    digitalWrite(LED_BUILTIN, LOW);  // Turn LED OFF
    delay(500);  // Wait 500ms
}