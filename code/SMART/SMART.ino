#define BLYNK_PRINT Serial
#define BLYNK_TEMPLATE_ID "TMPL6YbocRIVh"
#define BLYNK_TEMPLATE_NAME "Smart Agriculture"

#include <WiFi.h>
#include <BlynkSimpleEsp32.h>
#include <DHT.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include "HX711.h"

char auth[] = "YOUR_BLYNK_AUTH_TOKEN";
char ssid[] = "YOUR_WIFI_SSID";
char pass[] = "YOUR_WIFI_PASSWORD";

#define MQ2_PIN 34
#define SOIL_PIN 35
#define LDR_PIN 32
#define DHTPIN 15
#define DHTTYPE DHT11
#define ONE_WIRE_BUS 4
#define RELAY_PUMP 26
#define RELAY_LIGHT 27
#define DT 18
#define SCK 19

DHT dht(DHTPIN, DHTTYPE);
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature waterTemp(&oneWire);
HX711 scale;
float calibration_factor = 375.5;
WiFiServer server(80);
BlynkTimer timer;
int pumpState = LOW;
int lightState = LOW;
int mq2Threshold = 400;
int soilThreshold = 2500;
int ldrThreshold = 2000;

void sendBlynkData()
{
  float humidity = dht.readHumidity();
  float tempRoom = dht.readTemperature();
  waterTemp.requestTemperatures();
  float waterTempC = waterTemp.getTempCByIndex(0);
  int soil = analogRead(SOIL_PIN);
  int mq2 = analogRead(MQ2_PIN);
  Blynk.virtualWrite(V0, tempRoom);
  Blynk.virtualWrite(V1, humidity);
  Blynk.virtualWrite(V2, waterTempC);
  Blynk.virtualWrite(V9, soil);
  Blynk.virtualWrite(V3, pumpState==HIGH?1:0);
  Blynk.virtualWrite(V4, pumpState==LOW?1:0);
  Blynk.virtualWrite(V5, lightState==HIGH?1:0);
  Blynk.virtualWrite(V6, lightState==LOW?1:0);
  if (mq2 > mq2Threshold) { Blynk.virtualWrite(V7, 0); Blynk.virtualWrite(V8, 1); Blynk.logEvent("danger","Air Quality is Very Bad Ventilation"); }
  else { Blynk.virtualWrite(V7, 1); Blynk.virtualWrite(V8, 0); }
}

void setup()
{
  Serial.begin(115200);
  delay(2000);
  pinMode(RELAY_PUMP, OUTPUT);
  pinMode(RELAY_LIGHT, OUTPUT);
  digitalWrite(RELAY_PUMP, LOW);
  digitalWrite(RELAY_LIGHT, LOW);
  pumpState = LOW;
  lightState = LOW;
  dht.begin();
  waterTemp.begin();
  scale.begin(DT, SCK);
  scale.set_scale();
  scale.tare();
  scale.set_scale(calibration_factor);
  WiFi.begin(ssid, pass);
  while (WiFi.status() != WL_CONNECTED) delay(500);
  Blynk.config(auth);
  Blynk.connect(10000);
  server.begin();
  timer.setInterval(2000L, sendBlynkData);
}

void loop()
{
  Blynk.run();
  timer.run();
  WiFiClient client = server.available();
  float humidity = dht.readHumidity();
  float tempRoom = dht.readTemperature();
  waterTemp.requestTemperatures();
  float waterTempC = waterTemp.getTempCByIndex(0);
  int mq2 = analogRead(MQ2_PIN);
  int soil = analogRead(SOIL_PIN);
  int ldr = analogRead(LDR_PIN);
  float weight = scale.get_units(10);

  Serial.println("========== SENSOR VALUES ==========");
  Serial.print("MQ2 Gas: "); Serial.println(mq2);
  Serial.print("Soil Moisture: "); Serial.println(soil);
  Serial.print("LDR Light: "); Serial.println(ldr);
  Serial.print("Room Temperature: "); Serial.print(tempRoom); Serial.println(" C");
  Serial.print("Humidity: "); Serial.print(humidity); Serial.println(" %");
  Serial.print("Water Temperature: "); Serial.print(waterTempC); Serial.println(" C");
  Serial.print("Weight: "); Serial.print(weight); Serial.println(" g");
  Serial.print("Pump State: "); Serial.println(pumpState == HIGH ? "ON" : "OFF");
  Serial.print("Light State: "); Serial.println(lightState == HIGH ? "ON" : "OFF");
  Serial.println("===================================\n");

  if (client)
  {
    client.println(String(mq2)+","+String(soil)+","+String(ldr)+","+String(tempRoom)+","+String(humidity)+","+String(waterTempC)+","+String(weight));
    while (client.connected())
    {
      while(client.available())
      {
        String command = client.readStringUntil('\n'); command.trim();
        if (command == "PUMP_ON" && soil < soilThreshold) { digitalWrite(RELAY_PUMP,HIGH); pumpState=HIGH; Serial.println("AI Command: PUMP ON"); }
        if (command == "PUMP_OFF") { digitalWrite(RELAY_PUMP,LOW); pumpState=LOW; Serial.println("AI Command: PUMP OFF"); }
        if (command == "LIGHT_ON") { digitalWrite(RELAY_LIGHT,HIGH); lightState=HIGH; Serial.println("AI Command: LIGHT ON"); }
        if (command == "LIGHT_OFF") { digitalWrite(RELAY_LIGHT,LOW); lightState=LOW; Serial.println("AI Command: LIGHT OFF"); }
        if (soil > soilThreshold) { digitalWrite(RELAY_PUMP,LOW); pumpState=LOW; Serial.println("Soil above threshold: Pump OFF"); }
      }
      client.stop();
    }
  }
  delay(2000);
}
