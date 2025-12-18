// =========================
//      LIBRERÍAS
// =========================
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <ArduinoJson.h> 
#include <PubSubClient.h>
#include <LiquidCrystal_I2C.h>
#include <Wire.h>
#include "DHT.h"

// =========================
//      DEFINICIONES
// =========================
#define DHTPIN 4
#define DHTTYPE DHT11
#define indicador 16

// =========================
//      OBJETOS GLOBALES
// =========================
LiquidCrystal_I2C lcd(0x27, 16, 2);
WiFiClientSecure net;
PubSubClient mqttClient(net);
DHT dht(DHTPIN, DHTTYPE);

// =========================
//      CREDENCIALES WiFi
// =========================
const char* ssid = "nombre_red";
const char* password = "contaseña_red";

// =========================
//   ENDPOINT AWS IoT Core
// =========================
const char* endpoint = "a1i6yj1rmglkfn-ats.iot.us-east-2.amazonaws.com";
const int port = 8883;
const char* topic = "sensor/datos";
// =========================
//      CERTIFICADOS
// =========================
static const char root_ca[] PROGMEM = R"EOF(
-----BEGIN CERTIFICATE-----

-----END CERTIFICATE-----
)EOF";

static const char certificate[] PROGMEM = R"EOF(
-----BEGIN CERTIFICATE-----

-----END CERTIFICATE-----
)EOF";

static const char private_key[] PROGMEM = R"EOF(
-----BEGIN RSA PRIVATE KEY-----

-----END RSA PRIVATE KEY-----
)EOF";

// =========================
//     FUNCIONES
// =========================

// ---- WiFi ----
void wifiInit() {
  Serial.println("Conectándose a WiFi...");
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    delay(500);
  }

  Serial.println("\nWiFi conectado!");
  Serial.println(WiFi.localIP());
}

// ---- AWS ----
void connectAWS() {
  net.setCACert(root_ca);
  net.setCertificate(certificate);
  net.setPrivateKey(private_key);
  mqttClient.setServer(endpoint, port);

  Serial.print("Conectando a AWS IoT...");
  while (!mqttClient.connect("SensorDHT22")) {
    Serial.print(".");
    delay(1000);
  }
  Serial.println("\nConectado a AWS IoT Core!");
}

// ---- LCD ----
void mostrarEnLCD(float t, float h) {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("T:");
  lcd.print(t);
  lcd.print(" C");

  lcd.setCursor(0, 1);
  lcd.print("H:");
  lcd.print(h);
  lcd.print(" %");
}

// ---- Sensor ----
bool leerSensor(float &t, float &h) {
  h = dht.readHumidity();
  t = dht.readTemperature();

  if (isnan(h) || isnan(t)) {
    Serial.println("Error leyendo el sensor DHT.");
    return false;
  }

  return true;
}

// ---- AWS Publish ----
void enviarAWS(float t, float h) {
  StaticJsonDocument<200> doc;
  doc["temperatura"] = t;
  doc["humedad"] = h;

  char jsonData[200];
  serializeJson(doc, jsonData);

  mqttClient.publish(topic, jsonData);

  Serial.println("Datos enviados a AWS:");
  Serial.println(jsonData);
}

// ---- LED indicador ----
void parpadearIndicador() {
  digitalWrite(indicador, HIGH);
  delay(200);
  digitalWrite(indicador, LOW);
}

// ---- LCD Init ----
void encender_lcd() {
  lcd.init();
  lcd.backlight();
}

// =========================
//         SETUP
// =========================
void setup() {
  Serial.begin(9600); // Comunicación serial para debugging
  Wire.begin(21, 22); // Establece la comunicacion I2C para el contorl del LCD
  pinMode(indicador, OUTPUT); // Indicador de envio de datos

  encender_lcd(); // Funcion que enciende el lcd
  dht.begin(); // Inicialización del sensor DHT11
  wifiInit(); // Inicialización wifi
  connectAWS(); 
}

// =========================
//         LOOP
// =========================
void loop() {

  if (!mqttClient.connected())
    connectAWS();

  float t, h;

  if (!leerSensor(t, h)) {
    Serial.println("Reintentando en 2 segundos...");
    delay(2000);
    return;
  }

  mostrarEnLCD(t, h);
  enviarAWS(t, h);
  parpadearIndicador();

  delay(5000);
}