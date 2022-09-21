import numpy as np
import cv2
import os
import matplotlib.pyplot as plt
from tensorflow.keras.models import load_model
import time
from PIL import Image, ImageOps

from arduino_interface import ArduinoInterface

# erzeuge Objekte aus Klassen
arduino_interface = ArduinoInterface()


def most_frequent(list):
    return max(set(list), key = list.count)

def pfeilAenderung(imageToPrint, check):
   """
   Funktion zur Änderung der Richtung des Pfeils
   :param imageToPrint: Aktueller Frame
   :param check: wird geprüft
   :return: imageToPrint
   """

   if check == 1:
        #Rechter Pfeil an
        imageToPrint = cv2.arrowedLine(image, STARTLINKS, ENDLINKS, COLORARROWBLACK, THICKNESSArrow)
        imageToPrint = cv2.arrowedLine(image, STARTRECHTS, ENDRECHTS, COLORARROW, THICKNESSArrow)
   elif check == 0:
       #Ausgangsstatus
       imageToPrint = cv2.arrowedLine(image, STARTLINKS, ENDLINKS, COLORARROWBLACK, THICKNESSArrow)
       imageToPrint = cv2.arrowedLine(image, STARTRECHTS, ENDRECHTS, COLORARROWBLACK, THICKNESSArrow)
   else:
       #Linker Pfeil an
       imageToPrint = cv2.arrowedLine(image, STARTLINKS, ENDLINKS, COLORARROW, THICKNESSArrow)
       imageToPrint = cv2.arrowedLine(image, STARTRECHTS, ENDRECHTS, COLORARROWBLACK, THICKNESSArrow)


   return imageToPrint


# Window name in which image is displayed
WINDOW_IMAGE = 'Image'
# font
FONT = cv2.FONT_HERSHEY_SIMPLEX
# FONTSCALE
FONTSCALE = 1
# Blue color in BGR
FONTCOLOR = (0, 0, 0)
# Line THICKNESS of 2 px
THICKNESS = 2
# 0 - gerade, 1 - nach rechts fallen, 2 - nach links fallen
richtung = 2

# Statische Variablen
STARTRECHTS = (730, 300)
ENDRECHTS = (930, 500)
STARTLINKS = (670, 300)
ENDLINKS = (470, 500)
COLORARROW = (0, 255, 0)
COLORARROWBLACK = (0, 0, 0)
THICKNESSArrow = 10

anzahlSteine = 0
sortierteSteine = 0
unsortierteSteine = 0
# 0 - Gelb, 1 - Blau, 2 - Nichts, 3 - Rot
farbe = 1


# Model und Labels laden
model = load_model("Model\keras_model.h5", compile=False)
labels = []
with open('Model\labels.txt') as datei:
    for line in datei:
        zeile, label = line.split()
        labels.append(label)

# print(labels)
size_normalisiert = (224, 224)
# webcam
cap = cv2.VideoCapture(1)  # falls kamera träge -> (0, cv2.CAP_DSHOW)
# Framebreite einstellen
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
# Framehöhe einstellen
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
cap.set(cv2.CAP_PROP_GAIN, 0)

# Benötigt dynamische Variablen setzen
framecounter = 1
predictionhistory = []
decision = -1
letzeRichtung = 0
decisioncounter = -1
while True:
    # Webcamframe auslesen und flippen
    ret, frame = cap.read()
    frame = cv2.flip(frame, 1)
    margin = int(((1920 - 1080) / 2))

    if framecounter == 30:
        arduino_interface.read_and_interpret(1)
        framecounter = 1

    # Frame zuschneiden
    square_frame = frame[0:1080, margin:margin + 1080]
    # Image resizen
    resized_img = cv2.resize(square_frame, (224, 224))
    # Farbwerte anpassen
    model_img = cv2.cvtColor(resized_img, cv2.COLOR_BGR2RGB)
    image_array = np.asarray(model_img)
    # Image normalisieren
    normalized_image_array = (image_array.astype(np.float32) / 127.0) - 1
    # image in array laden
    data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)
    data[0] = normalized_image_array
    # Vergleich mit den in den Model enthaltenen Labels -> Größter Wert = bester
    prediction = model.predict(data)
    maxwahr = str(int(100 * prediction.max()))
    # print(labels[prediction.argmax()] + " " + maxwahr)

   # print(prediction.argmax())
    # Wenn Fall außer "Nichts"
    if prediction.argmax() != 0 or decisioncounter == 0:

        if decisioncounter != 0:
            decisioncounter = 15

            # Erkennungswahrscheinlichkeit prüfen
            if int(100 * prediction.max()) >= 80:
                predictionhistory.append(prediction.argmax())
            # Falls zu schlecht "Nichts" hinzufügen
            else:
                predictionhistory.append(0)

            # Wenn Prediction --> Vereinzeler anhalten
            if len(predictionhistory) == 1:
                arduino_interface.write_integer(3)

        # Wenn mehr als 10 Frames predictet wurden
        if len(predictionhistory) > 10 or decisioncounter == 0:
            # Am häufigsten zugetroffene Prediction holen
            decision = most_frequent(predictionhistory)

            decisioncounter = -1

            # History clearen
            predictionhistory.clear()
            if arduino_interface.arduinoStatus == 1:
                # Eingestellte Farbe: Gelb
                if arduino_interface.get_farbe() == 0:
                    # Model Prediction Farbe gelb
                    if decision == 3:
                        arduino_interface.write_integer(1)
                        letzeRichtung = 1
                    else:
                        # Nicht eingestellte Farbe erkannt
                        arduino_interface.write_integer(2)
                        letzeRichtung = 2
                # Eingestellte Farbe: Rot
                elif arduino_interface.get_farbe() == 1:
                    # Model Prediction Farbe rot
                    if decision == 2:
                        arduino_interface.write_integer(1)
                        letzeRichtung = 1
                    else:
                        # Nicht eingestellte Farbe erkannt
                        arduino_interface.write_integer(2)
                        letzeRichtung = 2
                # Eingestellte Farbe: Blau
                elif arduino_interface.get_farbe() == 2:
                    # Model Prediction Farbe blau
                    if decision == 1:
                        arduino_interface.write_integer(1)
                        letzeRichtung = 1
                    else:
                        # Nicht eingestellte Farbe erkannt
                        arduino_interface.write_integer(2)
                        letzeRichtung = 2
                # Erkennung zu schlecht --> aussortieren
                elif decision == 0:
                    arduino_interface.write_integer(2)
                    letzeRichtung = 1
            time.sleep(1)
            decision = -1
    # Neuen Frame zum anzeigen anlegen
    image = np.zeros((920, 1500, 3), dtype="uint8")
    image.fill(180)

    # sortierte und unsortierte Steine auslesen
    sortierteSteine = arduino_interface.get_sortiert(arduino_interface.get_farbe())[1]
    unsortierteSteine = arduino_interface.get_sortiert(arduino_interface.get_farbe())[0]
    anzahlSteine = sortierteSteine + unsortierteSteine

    # Webcamframe anzeigen
    image[50:274, 1200:1424] = resized_img

    # Funktion zur Pfeiländerung aufrufen
    image = pfeilAenderung(image, letzeRichtung)

    # Allgemeine Texte setzen
    image = cv2.putText(image, "System: " + arduino_interface.get_arduino_status_text(), (50, 50), FONT, FONTSCALE,
                        FONTCOLOR, THICKNESS, cv2.LINE_AA)
    image = cv2.putText(image, 'andere Farben: ' + str(unsortierteSteine), (250, 600), FONT, FONTSCALE,
                        FONTCOLOR, THICKNESS, cv2.LINE_AA)
    image = cv2.putText(image, "Gesetzte Farbe " + arduino_interface.get_farbe_text(arduino_interface.get_farbe()) +
                        ": " + str(sortierteSteine), (750, 600), FONT, FONTSCALE, FONTCOLOR, THICKNESS, cv2.LINE_AA)
    image = cv2.putText(image, labels[prediction.argmax()] + " " + maxwahr + "%", (1200, 350), FONT, FONTSCALE,
                        FONTCOLOR, THICKNESS, cv2.LINE_AA)
    image = cv2.putText(image, 'Steinanzahl: ' + str(anzahlSteine), (50, 100), FONT, FONTSCALE,
                        FONTCOLOR, THICKNESS, cv2.LINE_AA)
    image = cv2.putText(image, 'Aktueller Stein', (600, 50), FONT, FONTSCALE, FONTCOLOR, THICKNESS, cv2.LINE_AA)
    image = cv2.putText(image, 'Statistik', (300, 700), FONT, FONTSCALE, FONTCOLOR, THICKNESS, cv2.LINE_AA)
    image = cv2.rectangle(image, (250, 650), (1150, 900), (0, 0, 0), 10)

    # Texte für Statistik setzen
    image = cv2.putText(image, 'Blau', (600, 700), FONT, FONTSCALE, FONTCOLOR, THICKNESS, cv2.LINE_AA)
    image = cv2.putText(image, 'Rot', (800, 700), FONT, FONTSCALE, FONTCOLOR, THICKNESS, cv2.LINE_AA)
    image = cv2.putText(image, 'Gelb', (1000, 700), FONT, FONTSCALE, FONTCOLOR, THICKNESS, cv2.LINE_AA)
    image = cv2.putText(image, 'Erkennung', (300, 750), FONT, FONTSCALE, FONTCOLOR, THICKNESS, cv2.LINE_AA)
    image = cv2.putText(image, 'Aussortiert', (300, 800), FONT, FONTSCALE, FONTCOLOR, THICKNESS, cv2.LINE_AA)
    image = cv2.putText(image, 'Summe', (300, 850), FONT, FONTSCALE, FONTCOLOR, THICKNESS, cv2.LINE_AA)

    # Werte auslesen
    blauArray = arduino_interface.get_sortiert(arduino_interface.get_farbe_text('blau'))
    rotArray = arduino_interface.get_sortiert(arduino_interface.get_farbe_text('rot'))
    gelbArray = arduino_interface.get_sortiert(arduino_interface.get_farbe_text('gelb'))

    # Für die Statistik enstprechende Texte setzen
    image = cv2.putText(image, str(blauArray[1]), (600, 750), FONT, FONTSCALE, FONTCOLOR, THICKNESS, cv2.LINE_AA)
    image = cv2.putText(image, str(blauArray[0]), (600, 800), FONT, FONTSCALE, FONTCOLOR, THICKNESS, cv2.LINE_AA)
    image = cv2.putText(image, str(blauArray[1] + blauArray[0]), (600, 850), FONT, FONTSCALE, FONTCOLOR, THICKNESS,
                        cv2.LINE_AA)
    image = cv2.putText(image, str(rotArray[1]), (800, 750), FONT, FONTSCALE, FONTCOLOR, THICKNESS, cv2.LINE_AA)
    image = cv2.putText(image, str(rotArray[0]), (800, 800), FONT, FONTSCALE, FONTCOLOR, THICKNESS, cv2.LINE_AA)
    image = cv2.putText(image, str(rotArray[1] + rotArray[0]), (800, 850), FONT, FONTSCALE, FONTCOLOR, THICKNESS,
                        cv2.LINE_AA)
    image = cv2.putText(image, str(gelbArray[1]), (1000, 750), FONT, FONTSCALE, FONTCOLOR, THICKNESS, cv2.LINE_AA)
    image = cv2.putText(image, str(gelbArray[0]), (1000, 800), FONT, FONTSCALE, FONTCOLOR, THICKNESS, cv2.LINE_AA)
    image = cv2.putText(image, str(gelbArray[1] + gelbArray[0]), (1000, 850), FONT, FONTSCALE, FONTCOLOR, THICKNESS,
                        cv2.LINE_AA)

    # Beispielbild anzeigen
    if arduino_interface.get_farbe() == 0:
        img = cv2.imread('images\Gelb.png')
    elif arduino_interface.get_farbe() == 2:
        img = cv2.imread('images\Blau.png')
    elif arduino_interface.get_farbe() == 1:
        img = cv2.imread('images\Rot.png')

    # Bild anzeigen
    if farbe != 2:
        size = (300, 225)
        bild = cv2.resize(img, size)

        image[75:300, 565:865] = bild

        cv2.imshow(WINDOW_IMAGE, image)

    framecounter += 1
    if cv2.waitKey(1) & 0xFF == ord(' '):
        break

    # Decisioncounter auf default-Wert setzen
    if decisioncounter != -1:
        decisioncounter = decisioncounter - 1