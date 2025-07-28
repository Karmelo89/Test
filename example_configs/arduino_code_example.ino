/*
 * Solar Monitor Arduino Example
 * This code reads solar panel data and sends it via serial as JSON
 */

#include <ArduinoJson.h>

// Pin definitions
const int VOLTAGE_PIN = A0;
const int CURRENT_PIN = A1;
const int TEMP_PIN = A2;

// Calibration constants
const float VOLTAGE_SCALE = 0.0244;  // Adjust based on your voltage divider
const float CURRENT_SCALE = 0.1;     // Adjust based on your current sensor
const float TEMP_SCALE = 0.48828125; // For LM35 temperature sensor

void setup() {
  Serial.begin(9600);
  pinMode(VOLTAGE_PIN, INPUT);
  pinMode(CURRENT_PIN, INPUT);
  pinMode(TEMP_PIN, INPUT);
}

void loop() {
  // Read sensor values
  int voltageRaw = analogRead(VOLTAGE_PIN);
  int currentRaw = analogRead(CURRENT_PIN);
  int tempRaw = analogRead(TEMP_PIN);
  
  // Convert to actual values
  float voltage = voltageRaw * VOLTAGE_SCALE;
  float current = currentRaw * CURRENT_SCALE;
  float temperature = tempRaw * TEMP_SCALE;
  float power = voltage * current;
  
  // Calculate efficiency (simplified)
  float efficiency = (power / 1000.0) * 100; // Assuming 1kW reference
  if (efficiency > 100) efficiency = 100;
  
  // Create JSON object
  StaticJsonDocument<200> doc;
  doc["power"] = power;
  doc["voltage"] = voltage;
  doc["current"] = current;
  doc["temperature"] = temperature;
  doc["efficiency"] = efficiency;
  doc["timestamp"] = millis();
  
  // Send JSON via serial
  serializeJson(doc, Serial);
  Serial.println();
  
  delay(2000); // Send data every 2 seconds
}