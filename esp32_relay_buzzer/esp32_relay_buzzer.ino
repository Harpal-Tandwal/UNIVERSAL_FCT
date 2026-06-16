/*
  ESP32 DevKit V1 - 8 Relay + Buzzer + Power Supply Controller
  Serial: 115200 baud, any line ending (\r, \n, or \r\n)
  Commands:
    8-bit binary       -> set relays (e.g. "11000000")
    BZR-C-ON-OFF      -> buzzer (e.g. "BZR-05-02-01")
    PSV <voltage>     -> set power supply voltage (PSV 05.00)
    PSC <current>     -> set power supply current (PSC 01.00)
    PSON              -> power supply output ON
    PSOFF             -> power supply output OFF
    PSMODE CV         -> constant voltage mode
    PSMODE CC         -> constant current mode
    PSMEAS            -> read measured voltage & current
    PSSTATUS          -> power supply status
    PING              -> PONG
    *IDN?             -> ESP32-TECH-TANDHWAL
    ? or HELP         -> help
*/

#define RELAY1   4
#define RELAY2   5
#define RELAY3   33
#define RELAY4   32
#define RELAY5   23
#define RELAY6   27
#define RELAY7   14
#define RELAY8   13
#define BUZZER   19

#define PS_VOLT_PIN   25    // DAC1 - voltage setpoint
#define PS_CURR_PIN   26    // DAC2 - current setpoint
#define PS_ENABLE     12    // GPIO to enable/disable PS output
#define PS_VOLT_MEAS  34    // ADC - read output voltage
#define PS_CURR_MEAS  35    // ADC - read output current

const uint8_t RELAY_PINS[8] = {RELAY1, RELAY2, RELAY3, RELAY4,
                               RELAY5, RELAY6, RELAY7, RELAY8};

String serialBuffer = "";
bool psOutputOn = false;
String psMode = "CV";
float psSetVoltage = 0;
float psSetCurrent = 0;

void setup() {
  Serial.begin(115200);
  delay(200);

  for (int i = 0; i < 8; i++) {
    pinMode(RELAY_PINS[i], OUTPUT);
    digitalWrite(RELAY_PINS[i], HIGH);
  }

  pinMode(BUZZER, OUTPUT);
  digitalWrite(BUZZER, LOW);

  pinMode(PS_ENABLE, OUTPUT);
  digitalWrite(PS_ENABLE, LOW);

  analogReadResolution(12);

  Serial.println();
  Serial.println("ESP32 PS ready. Type ? for help.");
  Serial.print("> ");
}

void loop() {
  while (Serial.available()) {
    char c = Serial.read();
    Serial.print(c);

    if (c == '\n' || c == '\r') {
      if (serialBuffer.length() > 0) {
        processCommand(serialBuffer);
        serialBuffer = "";
      }
      Serial.print("> ");
    } else {
      serialBuffer += c;
    }
  }
}

void processCommand(String cmd) {
  cmd.trim();
  if (cmd.length() == 0) return;

  if (cmd.equalsIgnoreCase("PING")) {
    Serial.println(); Serial.println("PONG"); return;
  }

  if (cmd.equalsIgnoreCase("*IDN?")) {
    Serial.println(); Serial.println("ESP32-TECH-TANDHWAL"); return;
  }

  if (cmd.equals("?") || cmd.equalsIgnoreCase("HELP")) {
    Serial.println();
    Serial.println("Commands:");
    Serial.println("  8-bit binary     -> relays (e.g. 11000000)");
    Serial.println("  BZR-C-ON-OFF    -> buzzer (e.g. BZR-03-01-01)");
    Serial.println("  PSV <voltage>   -> set voltage (PSV 05.00)");
    Serial.println("  PSC <current>   -> set current (PSC 01.00)");
    Serial.println("  PSON / PSOFF    -> output on/off");
    Serial.println("  PSMODE CV / CC  -> mode");
    Serial.println("  PSMEAS          -> read V & I");
    Serial.println("  PSSTATUS        -> status");
    Serial.println("  PING / *IDN?    -> identification");
    return;
  }

  if (cmd.startsWith("BZR-") || cmd.startsWith("bzr-")) {
    handleBuzzer(cmd);
  } else if (cmd.length() == 8 && isBinaryString(cmd)) {
    handleRelays(cmd);
  } else if (cmd.equalsIgnoreCase("PSON")) {
    handlePSOn();
  } else if (cmd.equalsIgnoreCase("PSOFF")) {
    handlePSOff();
  } else if (cmd.equalsIgnoreCase("PSMEAS")) {
    handlePSMeas();
  } else if (cmd.equalsIgnoreCase("PSSTATUS")) {
    handlePSStatus();
  } else if (cmd.toUpperCase().startsWith("PSV ")) {
    handlePSVolt(cmd.substring(4));
  } else if (cmd.toUpperCase().startsWith("PSC ")) {
    handlePSCurr(cmd.substring(4));
  } else if (cmd.toUpperCase().startsWith("PSMODE ")) {
    handlePSMode(cmd.substring(7));
  } else {
    Serial.println();
    Serial.print("?? Unknown: \""); Serial.print(cmd); Serial.println("\"");
  }
}

bool isBinaryString(String s) {
  for (int i = 0; i < s.length(); i++) {
    if (s[i] != '0' && s[i] != '1') return false;
  }
  return true;
}

void handleRelays(String pattern) {
  Serial.println();
  for (int i = 0; i < 8; i++) {
    digitalWrite(RELAY_PINS[i], (pattern[i] == '0') ? HIGH : LOW);
  }
  Serial.print("OK:Relays -> "); Serial.println(pattern);
}

void handleBuzzer(String cmd) {
  int d1 = cmd.indexOf('-');
  int d2 = cmd.indexOf('-', d1 + 1);
  int d3 = cmd.indexOf('-', d2 + 1);
  if (d1 == -1 || d2 == -1 || d3 == -1) {
    Serial.println(); Serial.println("ERR:Use BZR-<C>-<ON>-<OFF>"); return;
  }
  int cycles = cmd.substring(d1 + 1, d2).toInt();
  int onTime = cmd.substring(d2 + 1, d3).toInt();
  int offTime = cmd.substring(d3 + 1).toInt();
  if (cycles <= 0 || onTime <= 0 || offTime <= 0) {
    Serial.println(); Serial.println("ERR:Values must be > 0"); return;
  }
  Serial.println();
  Serial.print("OK:Buzzer "); Serial.print(cycles); Serial.print("x ");
  Serial.print(onTime); Serial.print("s on, "); Serial.print(offTime); Serial.println("s off");
  for (int i = 0; i < cycles; i++) {
    digitalWrite(BUZZER, HIGH); delay(onTime);
    digitalWrite(BUZZER, LOW);
    if (i < cycles - 1) delay(offTime);
  }
}

// --- Power Supply ---

void setDACVoltage(int pin, float value, float maxRef) {
  int dacVal = (int)((value / maxRef) * 255);
  if (dacVal < 0) dacVal = 0;
  if (dacVal > 255) dacVal = 255;
  dacWrite(pin, dacVal);
}

float readADCVoltage(int pin, float dividerRatio) {
  int raw = analogRead(pin);
  float vol = (raw / 4095.0) * 3.3 * dividerRatio;
  return vol;
}

void handlePSOn() {
  psOutputOn = true;
  digitalWrite(PS_ENABLE, HIGH);
  Serial.println(); Serial.println("OK:PS ON");
}

void handlePSOff() {
  psOutputOn = false;
  digitalWrite(PS_ENABLE, LOW);
  Serial.println(); Serial.println("OK:PS OFF");
}

void handlePSVolt(String valStr) {
  valStr.trim();
  float v = valStr.toFloat();
  if (v < 0 || v > 30) {
    Serial.println(); Serial.println("ERR:Voltage 0-30V"); return;
  }
  psSetVoltage = v;
  setDACVoltage(PS_VOLT_PIN, v, 30.0);
  Serial.println();
  Serial.print("OK:V="); Serial.print(v, 2); Serial.println("V");
}

void handlePSCurr(String valStr) {
  valStr.trim();
  float c = valStr.toFloat();
  if (c < 0 || c > 5) {
    Serial.println(); Serial.println("ERR:Current 0-5A"); return;
  }
  psSetCurrent = c;
  setDACVoltage(PS_CURR_PIN, c, 5.0);
  Serial.println();
  Serial.print("OK:I="); Serial.print(c, 2); Serial.println("A");
}

void handlePSMode(String mode) {
  mode.trim();
  mode.toUpperCase();
  if (mode == "CV" || mode == "CONSTANT_VOLTAGE") {
    psMode = "CV";
    Serial.println(); Serial.println("OK:Mode CV");
  } else if (mode == "CC" || mode == "CONSTANT_CURRENT") {
    psMode = "CC";
    Serial.println(); Serial.println("OK:Mode CC");
  } else {
    Serial.println(); Serial.println("ERR:Mode CV or CC");
  }
}

void handlePSMeas() {
  float vMeas = readADCVoltage(PS_VOLT_MEAS, 6.0);
  float cMeas = readADCVoltage(PS_CURR_MEAS, 6.0);
  Serial.println();
  Serial.print("OK:V="); Serial.print(vMeas, 3);
  Serial.print(",I="); Serial.print(cMeas, 3);
  Serial.println();
}

void handlePSStatus() {
  Serial.println();
  Serial.print("OK:Output="); Serial.print(psOutputOn ? "ON" : "OFF");
  Serial.print(",Mode="); Serial.print(psMode);
  Serial.print(",Vset="); Serial.print(psSetVoltage, 2);
  Serial.print(",Iset="); Serial.print(psSetCurrent, 2);
  Serial.println();
}
