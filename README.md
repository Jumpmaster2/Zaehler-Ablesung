# Zähler-Ablesung

[English version](README.en.md)

Custom Integration für Home Assistant, die Zähler (Wärme, Wasser, Gas, Strom) mit einer Kamera abliest. Eine günstige ESP32-CAM mit ESPHome fotografiert die Anzeige, eine KI-Aufgabe von Home Assistant (`ai_task`, z. B. Anthropic Claude, OpenAI, Google oder ein lokales Modell mit Bildunterstützung) liest den Zählerstand. Ein Mehrheitsentscheid über mehrere Bilder und eine Plausibilitätsprüfung sorgen dafür, dass Fehllesungen nicht in der Statistik landen.

Alles wird im Dashboard **Zähler-Ablesung** in der Seitenleiste eingerichtet: Zähler anlegen, Kamera und Licht wählen, mit einem Testbild die Helligkeit ausprobieren, Intervall und Prüfungen einstellen. Automationen, Skripte und Helfer sind nicht nötig.

> Status: Version 0.3.0.

## Funktionsweise

### Ein Bild aufnehmen

1. Das Licht (z. B. die Blitz-LED der ESP32-CAM) wird mit der eingestellten Helligkeit eingeschaltet, einmal für alle Bilder einer Ablesung.
2. Nach der Vorlaufzeit werden einige Bilder verworfen. Die ESP32-CAM liefert nach einer Pause sonst noch ein altes Bild ohne Licht aus ihrem Puffer.
3. Die Bilder werden aufgenommen, danach geht das Licht aus. War es vorher schon an (z. B. für das Livebild), bleibt es an.
4. Optional wird das Bild um einen beliebigen Winkel (bis ±180°) gedreht, auf den **Bildausschnitt** zugeschnitten und in der **Belichtung** angepasst. Das ist bei Weitwinkel-Kameras wichtig, auf denen die Anzeige sonst nur ein kleiner Streifen ist. Im Dashboard dreht man das letzte Bild gerade und zieht den Ausschnitt mit Maus oder Finger darüber auf. Beim Einrichten der Kamera hilft das **Livebild** dort (auf Wunsch mit eingeschaltetem Licht), ohne jedes Mal ein Testbild aufzunehmen.
5. Das Bild, das die KI bekommt, liegt danach unter `/media/zaehler_ablesung/<Zähler-ID>/letztes.jpg` (das unbeschnittene als `original.jpg`) und ist als Kamera-Entität **Letztes Bild** sichtbar.

### Ablesen mit Mehrheitsentscheid

* Die KI bekommt das Bild und eine Anweisung, die sich aus Zählerart, Einheit, Nachkommastellen und deinen **Hinweisen** zusammensetzt (im Editor unter "Anweisung an die KI" einsehbar). Sie antwortet nur mit der Zahl oder mit "unlesbar".
* Mit **Bearbeiten** lässt sich die ganze Anweisung frei ändern; die automatisch erzeugte dient als Vorlage. Eine eigene Anweisung ersetzt dann die erzeugte vollständig, Einheit, Nachkommastellen und Hinweise werden nicht mehr eingesetzt. **Standard wiederherstellen** kehrt zur erzeugten Anweisung zurück.
* Es werden so lange Bilder gelesen, bis ein Wert **zweimal gleich** gelesen wurde, höchstens die eingestellte Zahl an Bildern (Standard 4). Gibt es keinen solchen Wert, ist die Ablesung "unlesbar".
* Der allererste Wert eines Zählers wird zusätzlich durch weitere Bilder (Standard 2) bestätigt, weil es noch nichts gibt, womit er sich vergleichen ließe. Ein falsch gelesener Erstwert (z. B. ohne Komma) würde sonst alle späteren richtigen Werte als "kleiner" verwerfen lassen.
* Steht in der Antwort der KI außer der Zahl nur eine Einheit oder eine Bezeichnung ("1234,5 m³", "Zählerstand: 1234.5"), zählt die Zahl.

### Plausibilitätsprüfung

* **Anstieg zu groß:** Steigt der Wert seit der letzten gültigen Ablesung um mehr als *größter Anstieg pro Stunde × Stunden* (mindestens eine halbe Stunde, ohne vorherigen Wert zwei Stunden), wird er verworfen.
* **Kleiner als zuvor:** Ein kleinerer Wert wird nur übernommen, wenn er höchstens um die *größte Korrektur* kleiner ist und weitere Bilder (Standard 2) ihn alle bestätigen. Dann gilt er als "korrigiert" (eine frühere Fehllesung wird damit berichtigt).
* Verworfene und korrigierte Ablesungen erzeugen eine Benachrichtigung in Home Assistant (abschaltbar). Bei "unlesbar" oder nicht erreichbarer Kamera/KI erst ab dem dritten Fehlschlag in Folge. Im Dashboard lässt sich ein verworfener, aber richtig gelesener Wert mit einem Klick übernehmen. Das Bild wird unter `verworfen/` aufbewahrt (die letzten 20) und ist im Dashboard auf der Zählerkarte unter **Verworfene Bilder** zu sehen.
* Der Zählerstand-Sensor hat die Zustandsklasse `total` (nicht `total_increasing`), damit eine Korrektur nach unten in der Statistik nicht als Zählertausch zählt.

### Zeitplan

* Jeder Zähler wird automatisch im eingestellten **Intervall** abgelesen (Prüfung alle 5 Minuten). Nach einer unlesbaren oder fehlgeschlagenen Ablesung kommt der nächste Versuch schon nach 15 Minuten.
* Optional eine **Bedingung**: Solange diese Entität `off` ist, gilt ein zweites Intervall. Beispiel: ein Heiztag-Sensor, an Heiztagen alle 30 Minuten, sonst alle 6 Stunden.
* Der Schalter **Automatik** stoppt die automatischen Ablesungen, die Schaltfläche **Jetzt ablesen** liest sofort ab.

## Entitäten je Zähler

| Entität | Bedeutung |
| --- | --- |
| Zählerstand | Letzter gültiger Wert (Energie, Wasser oder Gas, für das Energie-Dashboard geeignet). Attribut `last_valid_reading`. |
| Mittlere Leistung / Mittlerer Durchfluss | Verbrauch seit der vorherigen gültigen Ablesung (kW bei Energie, L/h bei Volumen). Wird bei einer Korrektur zurückgesetzt. |
| Status | Ergebnis der letzten Ablesung: gültig, korrigiert, unlesbar, kleiner als zuvor, Anstieg zu groß, Kamera- oder KI-Fehler, von Hand gesetzt. Attribut `readings` mit allen Einzellesungen. |
| Letzte Ablesung / Nächste Ablesung | Zeitpunkte (Diagnose). |
| Letztes Bild | Kamera-Entität mit dem zuletzt aufgenommenen Bild. |
| Jetzt ablesen / Testbild | Schaltflächen. Das Testbild wird nur aufgenommen, nicht gelesen (zum Ausprobieren von Ausrichtung, Schärfe und Helligkeit). |
| Automatik | Automatische Ablesungen an oder aus. |

## Aktionen und Ereignisse

* `zaehler_ablesung.read`: Zähler der angegebenen Entitäten jetzt ablesen.
* `zaehler_ablesung.set_reading`: Zählerstand von Hand setzen (z. B. nach einer Fehllesung oder beim Start). Die nächsten Ablesungen werden gegen diesen Wert geprüft. Auch im Dashboard unter "Zählerstand von Hand setzen".
* Ereignis `zaehler_ablesung_reading` nach jeder Ablesung mit `meter`, `valid`, `status`, `value`, `previous`, `readings`, `unit`.

## Installation

1. HACS, Benutzerdefinierte Repositories, `https://github.com/Jumpmaster2/Zaehler-Ablesung` als Integration hinzufügen und installieren, Home Assistant neu starten.
2. Einstellungen, Geräte & Dienste, Integration hinzufügen, **Zähler-Ablesung**. Dabei die KI-Aufgabe wählen.
3. In der Seitenleiste **Zähler-Ablesung** öffnen, unter **Zähler** einen Zähler hinzufügen: Name, Zählerart, Kamera, Licht. Speichern, dann mit **Testbild** Ausrichtung und Helligkeit prüfen.
4. Einmal **Jetzt ablesen** und das Ergebnis prüfen. Stimmt etwas nicht, in den **Hinweisen** beschreiben, was die KI falsch liest (z. B. "Die Linie über den Ziffern ist der Rahmen, kein Segment").

Voraussetzungen: Home Assistant 2026.10 oder neuer, eine KI-Aufgaben-Entität mit Bildunterstützung (Anhänge), eine Kamera-Entität.

### Kamera: ESP32-CAM mit ESPHome

Ein Beispiel liegt in [docs/esphome-esp32-cam.yaml](docs/esphome-esp32-cam.yaml). Erfahrungen aus dem Betrieb:

* **Kameratakt 8 MHz** statt 20 MHz. Der höhere Takt stört die WLAN-Antenne der ESP32-CAM; Bilder dauern dann über 10 Sekunden oder brechen ab, OTA-Updates hängen.
* **Zwei Bildpuffer** und kein Dauer-Streaming (`idle_framerate: 0 fps`). Die Integration verwirft die ersten Bilder nach dem Einschalten des Lichts.
* **Blitz-LED** über `ledc` auf Kanal 2 (die Kamera belegt den Timer der Kanäle 0 und 1) und mit begrenzter Leistung, sonst spiegelt das Display. Meist reichen 10 bis 60 %.
* Bei LCD-Anzeigen den Winkel so wählen, dass die LED nicht direkt reflektiert.

### Kosten

Pro Bild eine KI-Abfrage, pro Ablesung meist 2 Bilder. Mit einem kleinen Modell (z. B. Claude Haiku) und 1024×768 Pixeln sind das Bruchteile eines Cents je Ablesung. Das Intervall bestimmt die Kosten: alle 30 Minuten sind rund 100 Bilder am Tag.

## Datenschutz

Die Bilder gehen an den Anbieter der gewählten KI-Aufgabe. Sie zeigen nur die Zähleranzeige, sofern die Kamera passend ausgerichtet ist.

## Lizenz

MIT
