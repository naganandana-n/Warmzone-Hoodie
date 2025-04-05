#define HEATER1_PIN  14
#define HEATER2_PIN  13
#define HEATER3_PIN  12

void setup() {
  // Initialize serial for debug (optional)
  Serial.begin(115200);
  Serial.println("Heater Test: Setting all to full power (255)");

  // Set heater pins as output
  pinMode(HEATER1_PIN, OUTPUT);
  pinMode(HEATER2_PIN, OUTPUT);
  pinMode(HEATER3_PIN, OUTPUT);

  // Apply full PWM
  analogWrite(HEATER1_PIN, 255);
  analogWrite(HEATER2_PIN, 255);
  analogWrite(HEATER3_PIN, 255);
}

void loop() {
  // Nothing to do in loop — it's a static test
}