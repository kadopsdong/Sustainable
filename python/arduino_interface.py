import serial
import time


class ArduinoInterface:

    def __init__(self):
        #Konstruktor
        # Einstellung für Com-Port
        self.port = 'COM6'

        # Variable für Serielle Verbindung in Klasse erzeugen
        # --> Verbindung bleibt bestehen
        self.con = 0
        # Variable mit Objekt der Verbindung befüllen
        self.open_con()

        # Umgebungsvariablen setzen:
        # Status des Arduino
        self.arduinoStatus = 0
        # Aktuell ausgewählte Farbe
        self.farbe = 0
        # Liste mit den Sortierstatistiken nach Farben
        self.sortiert = [[0, 0],
                         [0, 0],
                         [0, 0]]

    # Gibt einen String über den Arduino Status zurück
    def get_arduino_status_text(self):
        if self.arduinoStatus == 0:
            return "Aus"
        elif self.arduinoStatus == 1:
            return "An"

    # Gibt den Arduino Status als Zahl zurück
    def get_arduino_status(self):
        return self.arduinoStatus

    # Gibt die aktuelle Farbe zurück
    def get_farbe(self):
        return self.farbe

    # Gibt die Sortierstatistik für eine bestimmte Farbe zurück
    def get_sortiert(self, farbe):
        return self.sortiert[farbe]

    # Sendet ein Byte Seriell an den Arduino
    def write_integer(self, number):
        # 1 = rechts schwenken
        # 2 = links schwenken
        # 3 = Vereinzelner stoppen
        data = 2
        # Sortierstatistik updaten, falls Servomotor geschwenkt wird.
        if number == 1:
            self.sortiert[self.farbe][1] += 1
        elif number == 2:
            self.sortiert[self.farbe][0] += 1

        # Lesen ob Byte vom Arduino gesendet wurde
        # --> Eventuelles Stop Bit muss abfegangen werden
        self.read_and_interpret(1)
        # Falls Arduino bereit ist:
        if self.arduinoStatus == 1:
            # Übergebene nummer zum String casten
            number = str(number)
            # String konvertieren und seriell senden
            self.con.write(bytes(number, 'utf-8'))
            # Auf Arduino warten
            time.sleep(1.5)
            # Empfangene Daten interpretieren
            data = self.read_and_interpret(1)
        return data

    # Gibt die aktuelle Farbe als String zurück wenn Nummer übergeben wird
    # Alternativ gibt Nummer zurück wenn String übergeben wird
    def get_farbe_text(self, farbeID):
        if farbeID == 0:
            return 'gelb'
        elif farbeID == 1:
            return 'rot'
        elif farbeID == 2:
            return 'blau'
        elif farbeID == 'gelb':
            return 0
        elif farbeID == 'rot':
            return 1
        elif farbeID == 'blau':
            return 2

    # Liest ein Byte Seriell ein
    def read_line(self):
        data = self.con.readline()
        data = data.strip()
        data = data.decode()
        return data

    # Serielle Verbindung beenden
    def close_con(self):
        self.con.close()

    # Serielle Verbindung starten
    def open_con(self):
        # Baudrate = 9600, timeout = 0,2 Sekunden
        # Com-Port des Kosntruktors wird genutzt
        self.con = serial.Serial(port=self.port, baudrate=9600, timeout=0.2)
        time.sleep(3.0)

    def read_and_interpret(self, mode):
        #mode 1 = read once
        #mode 2 = read until answer

        #Umgebungsvariablen setzen
        code = 0
        counter = 0
        # Prüfen bis Byte von Arduino erhalten wird
        while code == 0:
            # Probiere ein Byte Seriell zu lesen
            data = self.con.readline()
            # Steuerzeichen entfernen und normalisieren
            data = data.strip()
            data = data.decode()

            # IF Verzweigung um Codes auszuwerten:
            # 99 = Alles in Ordnung
            # 100 = Fehler
            # 2 = Stop Bit
            # 1 = Start Bit
            # 10 = Farbe auf gelb setzen
            # 11 = Farbe auf rot setzen
            # 12 = Farbe auf blau setzen
            if data == "99":
                code = "99"
            elif data == "100":
                code = "100"
            elif data == "2":
                # Arduino Status auf aus setzen
                self.arduinoStatus = 0
                code = "2"
            elif data == "1":
                # Arduino Status auf ein setzen
                self.arduinoStatus = 1
                code = "1"
            elif data == "10":
                # Farbe auf gelb setzen
                self.farbe = 0
            elif data == "11":
                # Farbe auf rot setzen
                self.farbe = 1
            elif data == "12":
                # Farbe auf gelb setzen
                self.farbe = 2

            # Schleife beim ersten durchlauf durchbrechen, wenn Mode = 1 ist
            if mode == 1:
                break
        return code

