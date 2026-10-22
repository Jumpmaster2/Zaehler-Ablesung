// Generated from the translation files by scripts/build_labels.py, do not edit by hand.
export const LABELS = {
 "de": {
  "fields": {
   "ai_task_entity": [
    "KI-Aufgabe",
    "KI-Aufgaben-Entität, die die Bilder liest (z. B. Anthropic, OpenAI, Google oder Ollama mit Bildunterstützung). Ein Zähler kann eine eigene nutzen."
   ],
   "notify_rejected": [
    "Benachrichtigungen",
    "Hauptschalter für die Benachrichtigungen in Home Assistant. Ab wann sie bei welchem Zähler kommen, steht beim Zähler unter „Benachrichtigungen“."
   ],
   "name": [
    "Name",
    ""
   ],
   "meter_type": [
    "Zählerart",
    ""
   ],
   "camera": [
    "Kamera",
    "Kamera-Entität, die auf die Anzeige zeigt (z. B. ESP32-CAM mit ESPHome)."
   ],
   "light": [
    "Licht",
    "Optional. Wird für das Bild ein- und danach wieder ausgeschaltet (z. B. die Blitz-LED)."
   ],
   "light_brightness": [
    "Helligkeit",
    "Helligkeit des Lichts für das Bild. Am besten mit einem Testbild ausprobieren: Spiegelungen machen die Anzeige unlesbar."
   ],
   "warmup": [
    "Vorlaufzeit",
    "Wartezeit nach dem Einschalten des Lichts, damit die Kamera die Belichtung anpasst."
   ],
   "discard_frames": [
    "Verworfene Bilder",
    "Bilder, die vor dem eigentlichen Bild weggeworfen werden. Kameras mit Puffer (ESP32-CAM) liefern sonst ein altes Bild ohne Licht."
   ],
   "crop_left": [
    "Links",
    "Linker Rand des Ausschnitts in Prozent der Breite des gedrehten Bildes."
   ],
   "crop_top": [
    "Oben",
    "Oberer Rand des Ausschnitts in Prozent der Höhe des gedrehten Bildes."
   ],
   "crop_right": [
    "Rechts",
    "Rechter Rand des Ausschnitts in Prozent der Breite des gedrehten Bildes."
   ],
   "crop_bottom": [
    "Unten",
    "Unterer Rand des Ausschnitts in Prozent der Höhe des gedrehten Bildes."
   ],
   "rotate": [
    "Drehen",
    "Dreht das Bild im Uhrzeigersinn um diesen Winkel (negativ: gegen den Uhrzeigersinn), z. B. 90 für eine seitlich montierte Kamera oder ein paar Grad für eine schief sitzende Anzeige. Gedreht wird vor dem Zuschneiden, der Ausschnitt bezieht sich auf das gedrehte Bild."
   ],
   "exposure": [
    "Belichtung",
    "Helligkeit des Bildes für die KI: 100 % lässt es unverändert, darunter dunkler (gegen Spiegelungen und Überbelichtung), darüber heller."
   ],
   "enhance": [
    "Bild aufbereiten",
    "Macht das Bild grau, gleicht die Ausleuchtung aus und hebt den Kontrast an, bevor die KI es liest. Hilft, wenn das Licht einen hellen Fleck auf dem Displayglas und dunkle Ecken hinterlässt, oder bei blassen LCD-Segmenten. Im Live-Bild nicht zu sehen, dafür ein Testbild machen."
   ],
   "unit": [
    "Einheit",
    "Einheit auf der Anzeige (z. B. MWh, kWh oder m³)."
   ],
   "decimals": [
    "Nachkommastellen",
    "Anzahl der Nachkommastellen auf der Anzeige."
   ],
   "hints": [
    "Hinweise für die KI",
    "Optional. Was an dieser Anzeige besonders ist, z. B. Linien, die zu keiner Ziffer gehören, oder welche Ziffern nicht mitgelesen werden."
   ],
   "prompt": [
    "Eigene Anweisung an die KI",
    "Ersetzt die ganze automatisch erzeugte Anweisung (leer lassen für den Standard). Einheit, Nachkommastellen und Hinweise werden dann nicht mehr eingesetzt. Die KI soll weiterhin nur die Zahl oder „unlesbar“ antworten."
   ],
   "interval": [
    "Intervall",
    "Zeit zwischen zwei automatischen Ablesungen."
   ],
   "condition_entity": [
    "Bedingung",
    "Optional. Solange diese Entität 'aus' ist, gilt das zweite Intervall (z. B. ein Heiztag-Sensor)."
   ],
   "interval_off": [
    "Intervall, wenn die Bedingung aus ist",
    "Nur zusammen mit einer Bedingung."
   ],
   "max_rate": [
    "Größter Anstieg pro Stunde",
    "In der Einheit des Zählers. Ein größerer Anstieg seit der letzten gültigen Ablesung wird verworfen (z. B. 0,05 MWh = 50 kW)."
   ],
   "max_correction": [
    "Größte Korrektur",
    "In der Einheit des Zählers. Ein kleinerer Wert als zuvor wird nur übernommen, wenn er höchstens so viel kleiner ist und von weiteren Bildern bestätigt wird."
   ],
   "max_attempts": [
    "Bilder pro Ablesung",
    "Höchstens so viele Bilder, bis ein Wert zweimal gelesen wurde."
   ],
   "confirmations": [
    "Bestätigungsbilder",
    "Weitere Bilder, die alle den kleineren Wert zeigen müssen, bevor er als Korrektur übernommen wird."
   ],
   "meter_ai_task_entity": [
    "Eigene KI-Aufgabe",
    "Optional. Statt der KI-Aufgabe der Integration."
   ],
   "notify_smaller": [
    "Kleiner als zuvor",
    "Wert kleiner als der letzte gültige und nicht als Korrektur bestätigt (verworfen)."
   ],
   "notify_too_large": [
    "Anstieg zu groß",
    "Wert stärker gestiegen als der größte Anstieg pro Stunde erlaubt (verworfen)."
   ],
   "notify_corrected": [
    "Korrigiert",
    "Kleinerer Wert von weiteren Bildern bestätigt und übernommen."
   ],
   "notify_failed": [
    "Unlesbar oder Fehler",
    "KI liest nichts Eindeutiges, oder Kamera bzw. KI nicht erreichbar. Unlesbare Ablesungen unterbrechen die Zählung der anderen Fälle nicht."
   ]
  },
  "sections": {
   "camera_section": [
    "Kamera und Licht",
    "Kamera am Zähler und das Licht, das für das Bild eingeschaltet wird."
   ],
   "image_section": [
    "Bildausschnitt",
    "Nur dieser Teil des Bildes geht an die KI. Bei Weitwinkel-Kameras auf die Anzeige zuschneiden; im Dashboard lässt sich der Ausschnitt mit der Maus aufziehen."
   ],
   "display_section": [
    "Anzeige",
    "Was die Anzeige zeigt. Die Hinweise bekommt die KI mit."
   ],
   "schedule_section": [
    "Zeitplan",
    "Wie oft der Zähler automatisch abgelesen wird."
   ],
   "checks_section": [
    "Prüfungen",
    "Mehrheitsentscheid und Plausibilitätsprüfung einer Ablesung."
   ],
   "notify_section": [
    "Benachrichtigungen",
    "Ab dem wievielten Mal in Folge eine Benachrichtigung in Home Assistant erscheint (0 = nie, 1 = sofort). Eine gültige Ablesung setzt die Zählung zurück. Gilt nur, solange in den Einstellungen der Integration Benachrichtigungen eingeschaltet sind."
   ]
  },
  "errors": {
   "name_required": "Bitte einen Namen eingeben.",
   "camera_required": "Bitte eine Kamera auswählen."
  },
  "status": {
   "ok": "Gültig",
   "corrected": "Korrigiert",
   "unreadable": "Unlesbar",
   "error": "Kamera- oder KI-Fehler",
   "smaller": "Kleiner als zuvor",
   "too_large": "Anstieg zu groß",
   "manual": "Von Hand gesetzt"
  },
  "types": {
   "heat": "Wärmezähler",
   "water": "Wasserzähler",
   "gas": "Gaszähler",
   "electricity": "Stromzähler",
   "other": "Anderer Zähler"
  },
  "entities": {
   "reading": "Zählerstand",
   "rate": "Mittlerer Verbrauch",
   "rate_power": "Mittlere Leistung",
   "rate_flow": "Mittlerer Durchfluss",
   "last_check": "Letzte Ablesung",
   "next_check": "Nächste Ablesung",
   "status": "Status",
   "last_image": "Letztes Bild",
   "read_now": "Jetzt ablesen",
   "test_picture": "Testbild",
   "automatic": "Automatik"
  }
 },
 "en": {
  "fields": {
   "ai_task_entity": [
    "AI task",
    "AI task entity that reads the pictures (e.g. Anthropic, OpenAI, Google or Ollama with image support). A meter can use its own one."
   ],
   "notify_rejected": [
    "Notifications",
    "Main switch for the notifications in Home Assistant. When they come for which meter is set at the meter under \"Notifications\"."
   ],
   "name": [
    "Name",
    ""
   ],
   "meter_type": [
    "Meter type",
    ""
   ],
   "camera": [
    "Camera",
    "Camera entity pointed at the display (e.g. an ESP32-CAM with ESPHome)."
   ],
   "light": [
    "Light",
    "Optional. Switched on for the picture and off again afterwards (e.g. the flash LED)."
   ],
   "light_brightness": [
    "Light brightness",
    "Brightness of the light for the picture. Try it with a test picture: reflections make the display unreadable."
   ],
   "warmup": [
    "Warm-up time",
    "Wait after switching the light on, so the camera adjusts its exposure."
   ],
   "discard_frames": [
    "Discarded pictures",
    "Pictures thrown away before the real one. Cameras with a buffer (ESP32-CAM) otherwise deliver an old picture without light."
   ],
   "crop_left": [
    "Left",
    "Left edge of the crop in percent of the width of the turned picture."
   ],
   "crop_top": [
    "Top",
    "Top edge of the crop in percent of the height of the turned picture."
   ],
   "crop_right": [
    "Right",
    "Right edge of the crop in percent of the width of the turned picture."
   ],
   "crop_bottom": [
    "Bottom",
    "Bottom edge of the crop in percent of the height of the turned picture."
   ],
   "rotate": [
    "Rotate",
    "Turns the picture clockwise by this angle (negative: counterclockwise), e.g. 90 for a camera mounted sideways or a few degrees for a display that sits askew. Turned before cropping, the crop refers to the turned picture."
   ],
   "exposure": [
    "Exposure",
    "Brightness of the picture for the AI: 100 % leaves it unchanged, below is darker (against reflections and overexposure), above is brighter."
   ],
   "enhance": [
    "Enhance picture",
    "Turns the picture grey, evens out the lighting and stretches the contrast before the AI reads it. Helps when the light leaves a bright spot on the display glass and dark corners, or with pale LCD segments. Not shown in the live picture; take a test picture to see it."
   ],
   "unit": [
    "Unit",
    "Unit shown on the display (e.g. MWh, kWh or m³)."
   ],
   "decimals": [
    "Decimals",
    "Number of decimals shown on the display."
   ],
   "hints": [
    "Hints for the AI",
    "Optional. What is special about this display, e.g. lines that are not part of a digit, or which digits to ignore."
   ],
   "prompt": [
    "Own instructions for the AI",
    "Replace the whole generated instructions (leave empty for the standard). Unit, decimals and hints are then no longer inserted. The AI should still answer only with the number or “unreadable”."
   ],
   "interval": [
    "Interval",
    "Time between two automatic readings."
   ],
   "condition_entity": [
    "Condition",
    "Optional. While this entity is 'off', the second interval applies (e.g. a heating day sensor)."
   ],
   "interval_off": [
    "Interval while the condition is off",
    "Only used together with a condition."
   ],
   "max_rate": [
    "Largest increase per hour",
    "In the meter unit. A larger increase since the last valid reading is rejected (e.g. 0.05 MWh = 50 kW)."
   ],
   "max_correction": [
    "Largest correction",
    "In the meter unit. A smaller value than before is only taken when it is at most this much lower and confirmed by further pictures."
   ],
   "max_attempts": [
    "Pictures per reading",
    "Most pictures until a value has been read twice."
   ],
   "confirmations": [
    "Confirmation pictures",
    "Further pictures that must all show a smaller value before it is taken as a correction."
   ],
   "meter_ai_task_entity": [
    "Own AI task",
    "Optional. Instead of the AI task of the integration."
   ],
   "notify_smaller": [
    "Smaller than before",
    "Value below the last valid one and not confirmed as a correction (rejected)."
   ],
   "notify_too_large": [
    "Increase too large",
    "Value rose more than the largest increase per hour allows (rejected)."
   ],
   "notify_corrected": [
    "Corrected",
    "Smaller value confirmed by more pictures and taken."
   ],
   "notify_failed": [
    "Unreadable or error",
    "The AI reads nothing clear, or the camera or AI is not reachable. Unreadable readings do not interrupt the count of the other cases."
   ]
  },
  "sections": {
   "camera_section": [
    "Camera and light",
    "Camera of the meter and the light that is switched on for the picture."
   ],
   "image_section": [
    "Picture crop",
    "Only this part of the picture is sent to the AI. Crop wide-angle cameras to the display; in the dashboard the crop can be drawn with the mouse."
   ],
   "display_section": [
    "Display",
    "What the display shows. The hints are passed on to the AI."
   ],
   "schedule_section": [
    "Schedule",
    "How often the meter is read automatically."
   ],
   "checks_section": [
    "Checks",
    "Majority vote and plausibility check of a reading."
   ],
   "notify_section": [
    "Notifications",
    "From the how-many-th time in a row a notification appears in Home Assistant (0 = never, 1 = at once). A valid reading starts the count again. Only while notifications are switched on in the settings of the integration."
   ]
  },
  "errors": {
   "name_required": "Please enter a name.",
   "camera_required": "Please select a camera."
  },
  "status": {
   "ok": "Valid",
   "corrected": "Corrected",
   "unreadable": "Unreadable",
   "error": "Camera or AI error",
   "smaller": "Smaller than before",
   "too_large": "Increase too large",
   "manual": "Set by hand"
  },
  "types": {
   "heat": "Heat meter",
   "water": "Water meter",
   "gas": "Gas meter",
   "electricity": "Electricity meter",
   "other": "Other meter"
  },
  "entities": {
   "reading": "Meter reading",
   "rate": "Mean consumption",
   "rate_power": "Mean power",
   "rate_flow": "Mean flow",
   "last_check": "Last reading",
   "next_check": "Next reading",
   "status": "Status",
   "last_image": "Last picture",
   "read_now": "Read now",
   "test_picture": "Test picture",
   "automatic": "Automatic"
  }
 }
};
