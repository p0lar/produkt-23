const int CRD_PIN = 2;
const int CLK_PIN = 3;
const int DAT_PIN = 4;
String bitstring = ""; // contains the raw read bits

void setup() {
  pinMode(CRD_PIN, INPUT_PULLUP);
  pinMode(CLK_PIN, INPUT_PULLUP);
  pinMode(DAT_PIN, INPUT_PULLUP);

  // Display via LED if a card is read by the reader
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);
  Serial.begin(9600);
  while(!Serial){};
}

int cardIn = 0;
int lastCardIn = 0;

int clock = 0;
int lastClock = -1;

void loop() {
  cardIn = !digitalRead(CRD_PIN);  // negative logic
  if (cardIn & !lastCardIn) {
    digitalWrite(LED_BUILTIN, HIGH);
    Serial.println("info: card inserted");
  } else if (!cardIn & lastCardIn) {
    digitalWrite(LED_BUILTIN, LOW);
    Serial.println("info: card removed");
    Serial.print("info: bits: ");
    Serial.println(bitstring);
    Serial.print("debug: bitcount: ");
    Serial.println(bitstring.length());
    Serial.println("info: read end"); // End marker
    Serial.flush();
    // Reset the variables for next reading
    bitstring = "";
    lastClock = -1;  // Reset clockstate
    delay(1000);     // Debounce
  }
  lastCardIn = cardIn;

  if (!cardIn) {
    return;
  }

  clock = digitalRead(CLK_PIN);
  if (lastClock == -1) {
    Serial.println("debug: clockinit");
    lastClock = clock;
    return;
  } else if (!(lastClock == HIGH & clock == LOW)) { // all but negative edge
    lastClock = clock;
    return;
  }
  bitstring += !digitalRead(DAT_PIN); // Read the (inverted) bit on negative clock edge
  lastClock = clock;
}
