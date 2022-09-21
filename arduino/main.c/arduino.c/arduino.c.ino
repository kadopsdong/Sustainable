//Bibiliotheken einbinden
#include <avr/io.h> // für Port und Register Definitionen
#include <util/delay.h> // fuer funktion _delay_ms()
#include <avr/interrupt.h> // Für Interrupts
#include <Servo.h> // Für Servomotor
#include <SPI.h> // Für OLED Display
#include <Wire.h> // Für OLED Display
#include <Adafruit_GFX.h> // Für OLED Display
#include <Adafruit_SSD1306.h> // Für OLED Display

//Pin Konstanten setzen
//Button zum Systemzustand ändern
#define onOffButton PD3
//LED Ausgang blau
#define blueLed PD5
//LED Ausgang rot
#define redLed PD6
// LED Systemzustand
#define onOffLed PD4
// Taster Farbe ändern
#define switchColorButton PD2
// Servo für Sortierer
#define servo 9
// Servo für Vereinzelner
#define servo2 11

//Weite des OLED Displays angeben
#define SCREEN_WIDTH 128
//Höhe des OLED Displays angeben
#define SCREEN_HEIGHT 64 // OLED display height, in pixels

//Initialisierung des Adafruit OLED Displays
#define OLED_RESET     -1 // Reset pin # (or -1 if sharing Arduino reset pin)
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

//Variable für den aktuellen Betriebszustand
volatile bool onOffButtonState = 0;
//Variable für aktuell ausgewählte Farbe
volatile int currentColor = 0;
//Variable um Displayänderungen durchzuführen
volatile bool ChangeDisplay = 1;
//Zeitstempel der letzten Interrupt Ausführung PD2
volatile unsigned long letzterInterrupt_PD2 = 0;
//Variable ob Interrupt PD2 aktiviert oder deaktiviert ist
volatile bool Interrupt_PD2_Active = 1;
//Zeitstempel der letzten Interrupt Ausführung PD3
volatile unsigned long letzterInterrupt_PD3 = 0;
//Variable ob Interrupt PD3 aktiviert oder deaktiviert ist
volatile bool Interrupt_PD3_Active = 1;
//Zähler für Servomotorbewegungen "Links"
volatile int sortiertLinks = 0;
//Zähler für Servomotorbewegungen "Rechts"
volatile int sortiertRechts = 0;
// Zustandsvariable ob Vereinzelner aktiv ist
volatile bool servo2_aktiv = 0;
// Zustandvariable über Servoposition
volatile int servo2_position = 90;
// Zeitstempel der letzten Servomotor bewegung
volatile unsigned long servo2_zeit = millis();
// Zustandvariablen ob ISR Code in dem Loop ausgeführt werden soll
volatile bool Interrupt_PD2_ausfuehren = 0;
volatile bool Interrupt_PD3_ausfuehren = 0;
volatile int ISR2_counter = 0;
volatile int ISR3_counter = 0;

//Objekt zum ansteuern der Servomotoren
Servo Sortierer;
Servo Vereinzelner;


void setup() {
  // Serielle Verbindung initialisieren
  Serial.begin(9600);
  Serial.setTimeout(1);

  // Ein und Ausgänge festlegen
  pinMode(blueLed, OUTPUT);
  pinMode(redLed, OUTPUT);
  pinMode(onOffLed, OUTPUT);
  pinMode(onOffButton, INPUT_PULLUP);
  pinMode(switchColorButton, INPUT_PULLUP);

  // Interrupts setzen
  attachInterrupt(digitalPinToInterrupt(onOffButton), changeOnOffState, RISING);
  attachInterrupt(digitalPinToInterrupt(switchColorButton), changeColor, RISING);

  // Display initialisieren
  if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) { // Address 0x3D for 128x64
    for(;;);
  }
  delay(2000);
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(WHITE);

  // Plattform auf Grundposition setzen
  Sortierer.attach(servo);
  Sortierer.write(95);
  // Vereinzelner auf Grundposition setzen
  Vereinzelner.attach(servo2);
  Vereinzelner.write(10);
}

void loop() {
  // Interrupts aktivieren
  sei(); 
  int serialbyte = 0;
  
  //ISR Counter dekrimieren
  if(ISR2_counter > 1) {
    ISR2_counter--;
  }
  if(ISR3_coutner > 1) {
    ISR3_counter--;
  }
  
  //Taster Entprellen, Interrupt wird nach dem ersten Ausführen gesperrt!
  //Freigeben erfolgt über Loop, wenn eine geeignete Zeit vergangen ist
  if(ISR2_counter < 0) {
    Interrupt_PD2_Active = 1;
  }
  if(ISR3_counter < 0) {
    Interrupt_PD3_Active = 1;
  }

  // Interrupt PD2 zum Farb-Wechsel
  if(Interrupt_PD2_ausfuehren == 1) {
    //Interrupt ausschalten
    Interrupt_PD2_ausfuehren = 0;
    
    //Vereinzelner heben
    Vereinzelner.write(10);
    servo2_position = 10;
    
    //Ausführungs Zeitstempel setzen
    letzterInterrupt_PD2 = millis();
    
    //Laufvariablen zurücksetzen
    sortiertLinks = 0;
    sortiertRechts = 0;

    //Farbe ändern
    currentColor++;
    if(currentColor == 3) {
     currentColor = 0;
    }
    //Aktuelle Farbe an Python senden
    Serial.println(10+currentColor);
    ChangeDisplay = 1;
  }

  if(Interrupt_PD3_ausfuehren == 1) {
    Interrupt_PD3_ausfuehren = 0;
    //Ausführungs Zeitstempel setzen
    letzterInterrupt_PD3 = millis();

    //Variable invertieren
    onOffButtonState = !onOffButtonState;
    //LED invertieren
    PORTD ^= (1 << onOffLed);
    //Display Änderung triggern
    ChangeDisplay = 1;
    //Rückgabe Code an Python bestimmen
    //1 == AN
    //2 == AUS
    if(onOffButtonState == 1) {
      Serial.println(1);
      servo2_aktiv = 1;  
    }
    else if(onOffButtonState == 0) {
      Serial.println(2);
      servo2_aktiv = 0;
    }

    Vereinzelner.write(10);
    servo2_position = 90;
  }

  // Prüfen ob Vereinzelner aktiv ist
  if(servo2_aktiv == 1) {
    // Prüfen auf welcher Position der Servo steht
    // Wenn Vereinzelner gesenkt ist, 220ms warten dann heben
    if(servo2_position == 90) {
      // Prüfen ob genug Zeit vergangen ist
      if(millis() - servo2_zeit > 220) {
        // Servomotor ansteuern
        Vereinzelner.write(10);
        servo2_position = 10;
        servo2_zeit = millis();
      }
    }
    // Wenn Vereinzelner nicht gesenkt ist, 450ms warten dann senken
    else {
        // Prüfen ob genug Zeit vergangen ist
        if(millis() - servo2_zeit > 450) {
        // Servomotor ansteuern
        Vereinzelner.write(90);
        servo2_position = 90;
        servo2_zeit = millis();
      }
    }   
  }
  
  //Überarbeite Displayausgabe wenn Änderungen erfolgt sind.
  //ChangeDisplay muss auf 1 stehen
  if(ChangeDisplay == 1) {
    ChangeDisplay = 0;
    // Display Einstellungen treffen
    display.clearDisplay();
    display.setTextSize(1);
    display.setTextColor(WHITE);
    display.setCursor(0, 10);

    // Aktuelle Farbe ausgeben
    if (currentColor == 0){
      display.print("Farbe: Gelb");
      }
    else if (currentColor == 1){
      display.print("Farbe: Rot");
    }
    else if (currentColor == 2){
      display.print("Farbe: Blau");
    }

    // Systemzustand ausgeben
    display.setCursor(0, 0);
    if (onOffButtonState == 0){
      display.print("System: Aus");
    }
    else if (onOffButtonState == 1){
      display.print("System: An");
    }

    // Sortier Statistiken ausgeben
    display.setCursor(0,20);
    display.print("Sonstiges sortiert: " + String(sortiertLinks));
    display.setCursor(0,30);
    display.print("Farbe sortiert: " + String(sortiertRechts));
    //Ausgabe auf Display
    display.display();
    delay(1000);  
  }

  //Prüfen ob System ein ist
  if(onOffButtonState == 1) {
    //Prüfen ob Befehl von Python angekommen ist
    if(Serial.available()) {
      //Eingehendes Byte in Integer konvertieren
      serialbyte = Serial.readString().toInt();
      // Servomotor nach links schwenken
      if(serialbyte == 1) {
        moveServo(1);
      }
      // Servomotor nach rechts schwenken
      else if(serialbyte == 2) {
        moveServo(0); 
      }
      // Vereinzelner stoppen
      else if(serialbyte == 3) {
        servo2_aktiv = 0;
        Vereinzelner.write(10);
        servo2_position = 10;
      }
      //Falls kein valides Byte empfangen wurde, nichts machen
      else if(serialbyte == 0) {
        serialbyte = 0;
      }
      //Wenn undefiniertes Byte empfangen wurde mit Fehlercode antworten
      else {
        Serial.println(100);
      }
    }   
  }
}

void write_erfolg() {
  // 99 senden wenn erfolgreich
  Serial.println(99); 
}

void changeOnOffState(){
  //ISR entprellen --> beim ersten ausführen sperren
  // Entsperrung erfolgt Zeitabhänig im Loop
  if (Interrupt_PD3_Active == 1) {
    //ISR Sperren
    Interrupt_PD3_Active = 0;
    //ISR ausführung triggern
    Interrupt_PD3_ausfuehren = 1;
    //Counter setzen
    ISR3_counter = 2500;
  }
}

void changeColor(){
  //ISR entprellen --> beim ersten ausführen sperren
  // Entsperrung erfolgt Zeitabhänig im Loop
  if(onOffButtonState == 1) {
      if(Interrupt_PD2_Active == 1) {
        //ISR sperren
        Interrupt_PD2_Active = 0;
        //ISR ausführung triggern
        Interrupt_PD2_ausfuehren = 1;
        //Counter setzen
        ISR2_counter = 2500; 
    }
  }
}

void moveServo(int richtung){
  //0 = nach links
  //1 = nach rechts

  //Vereinzelner explizit anheben
  Vereinzelner.write(10);
  servo2_position = 90;

  //Richtung bestimmen
  //Servo wird Stückweise bewegt --> Sanftere Bewegung

  //Je nach Richtung wird die Blaue oder Rote LED angeschaltet
  //Am Ende werden die LEDS ausgeschaltet
  
  if (richtung == 0){
    sortiertLinks++;
    digitalWrite(blueLed, HIGH);
    Sortierer.write(115);
    delay(150);
    Sortierer.write(155);
    delay(150);
    Sortierer.write(175);
    delay(1200);
    Sortierer.write(155);
    delay(150);
    Sortierer.write(115);
    delay(150);
    Sortierer.write(95);
  }

    if (richtung == 1){
    sortiertRechts++;
    digitalWrite(redLed, HIGH);
    Sortierer.write(65);
    delay(150);
    Sortierer.write(40);
    delay(150);
    Sortierer.write(5);
    delay(1200);
    Sortierer.write(40);
    delay(150);
    Sortierer.write(65);
    delay(150);
    Sortierer.write(95);
  }

  //Vereinzelner starten
  servo2_aktiv = 1;

  //LED's deaktivieren
  digitalWrite(redLed, LOW);
  digitalWrite(blueLed, LOW);
  //Displayänderung triggern
  ChangeDisplay = 1;
  write_erfolg();
}
