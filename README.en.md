# Zähler-Ablesung (meter reading)

[Deutsche Version](README.md)

Custom integration for Home Assistant that reads meters (heat, water, gas, electricity) with a camera. A cheap ESP32-CAM with ESPHome takes a picture of the display, a Home Assistant AI task (`ai_task`, e.g. Anthropic Claude, OpenAI, Google or a local model with image support) reads the value. A majority vote over several pictures and a plausibility check keep wrong readings out of your statistics.

Everything is set up in the **Zähler-Ablesung** dashboard in the sidebar: add a meter, choose camera and light, try the brightness with a test picture, set interval and checks. No automations, scripts or helpers needed.

> Status: version 0.4.0.

## How it works

### Taking a picture

1. The light (e.g. the flash LED of the ESP32-CAM) is switched on with the configured brightness, once for all pictures of a reading.
2. After the warm-up time a few pictures are thrown away. Otherwise the ESP32-CAM still delivers an old picture without light from its buffer after a pause.
3. The pictures are taken, then the light goes off. If it was already on before (e.g. for the live picture), it stays on.
4. Optionally the picture is rotated by any angle (up to ±180°), cropped to the **picture crop** and its **exposure** adjusted. This matters for wide-angle cameras where the display is otherwise only a small strip. In the dashboard the last picture is turned straight and the crop drawn over it with mouse or finger. When mounting the camera the **live picture** there helps (with the light on if wanted), without taking a test picture each time.
5. The picture the AI gets is stored as `/media/zaehler_ablesung/<meter id>/letztes.jpg` (the uncropped one as `original.jpg`) and shown by the camera entity **Last picture**.

### Reading with a majority vote

* The AI gets the picture and instructions built from meter type, unit, decimals and your **hints** (see "Instructions for the AI" in the editor). It answers only with the number or with "unreadable".
* **Edit** lets you change the whole instructions freely, starting from the generated ones. Own instructions then replace the generated ones completely; unit, decimals and hints are no longer inserted. **Restore standard** goes back to the generated instructions.
* Pictures are read until one value was read **twice**, at most the configured number of pictures (default 4). Without such a value the reading is "unreadable".
* The very first value of a meter is also confirmed by further pictures (default 2), as there is nothing yet to compare it with. A wrong first value (e.g. without the decimal point) would otherwise make every later correct value be rejected as "smaller".
* If the answer of the AI holds only a unit or a label besides the number ("1234,5 m³", "Reading: 1234.5"), the number counts.

### Plausibility check

* **Increase too large:** if the value rose by more than *largest increase per hour × hours* since the last valid reading (at least half an hour, two hours without a previous value), it is rejected.
* **Smaller than before:** a smaller value is only taken when it is at most the *largest correction* lower and further pictures (default 2) all confirm it. It then counts as "corrected" (this fixes an earlier wrong reading).
* In the dashboard a rejected but correctly read value can be taken with one click. The picture is kept in `verworfen/` (the latest 20) and shown in the dashboard on the meter card under **Rejected pictures**.
* The meter reading sensor uses state class `total` (not `total_increasing`), so a correction downwards is not counted as a meter reset in the statistics.

### Notifications

Rejected, corrected and failed readings can create a notification in Home Assistant. For each meter the section **Notifications** sets from the how-many-th time in a row it appears (0 = never, 1 = at once):

| Case | Default |
| --- | --- |
| Smaller than before | 1 |
| Increase too large | 1 |
| Corrected | 1 |
| Unreadable or error (camera/AI not reachable) | 3 |

* A valid reading starts the count again and removes the notification.
* Another case starts the count anew (e.g. "increase too large" after "smaller than before" twice). Unreadable readings show no value and do not interrupt the count of the other cases; they are counted on their own.
* Example: "Smaller than before" set to 3 for the water meter reports only the third smaller value in a row, the heat meter stays at 1.
* The switch in the settings of the integration turns all notifications off.

### Schedule

* Every meter is read automatically at its **interval** (checked every 5 minutes). After an unreadable or failed reading the next try comes after 15 minutes.
* Optional **condition**: while this entity is `off`, a second interval applies. Example: a heating day sensor, every 30 minutes on heating days, otherwise every 6 hours.
* The **Automatic** switch stops the automatic readings, the **Read now** button reads immediately.

## Entities per meter

| Entity | Meaning |
| --- | --- |
| Meter reading | Last valid value (energy, water or gas, suitable for the energy dashboard). Attribute `last_valid_reading`. |
| Mean power / Mean flow | Consumption since the previous valid reading (kW for energy, L/h for volume). Reset by a correction. |
| Status | Result of the last reading: valid, corrected, unreadable, smaller than before, increase too large, camera or AI error, set by hand. Attribute `readings` with every single reading. |
| Last reading / Next reading | Timestamps (diagnostic). |
| Last picture | Camera entity with the latest picture. |
| Read now / Test picture | Buttons. The test picture is only taken, not read (to check alignment, focus and brightness). |
| Automatic | Automatic readings on or off. |

## Actions and events

* `zaehler_ablesung.read`: read the meters of the given entities now.
* `zaehler_ablesung.set_reading`: set the meter reading by hand (e.g. after a wrong reading or at the start). The next readings are checked against this value. Also in the dashboard under "Set the meter reading by hand".
* Event `zaehler_ablesung_reading` after every reading with `meter`, `valid`, `status`, `value`, `previous`, `readings`, `unit`.

## Installation

1. HACS, custom repositories, add `https://github.com/Jumpmaster2/Zaehler-Ablesung` as integration, install, restart Home Assistant.
2. Settings, Devices & services, add integration, **Zähler-Ablesung**. Choose the AI task.
3. Open **Zähler-Ablesung** in the sidebar, add a meter under **Meters**: name, type, camera, light. Save, then check alignment and brightness with **Test picture**.
4. Press **Read now** once and check the result. If something is wrong, describe in the **hints** what the AI misreads (e.g. "The line above the digits is the frame, not a segment").

Requirements: Home Assistant 2026.10 or newer, an AI task entity with image (attachment) support, a camera entity.

### Camera: ESP32-CAM with ESPHome

An example is in [docs/esphome-esp32-cam.yaml](docs/esphome-esp32-cam.yaml). Lessons learned:

* **Camera clock 8 MHz** instead of 20 MHz. The higher clock disturbs the WiFi antenna of the ESP32-CAM; pictures then take more than 10 seconds or fail, OTA updates hang.
* **Two frame buffers** and no continuous streaming (`idle_framerate: 0 fps`). The integration throws away the first pictures after switching the light on.
* **Flash LED** via `ledc` on channel 2 (the camera uses the timer of channels 0 and 1) with limited power, otherwise the display reflects. 10 to 60 % is usually enough.
* For LCD displays choose an angle where the LED does not reflect directly.

### Costs

One AI request per picture, usually 2 pictures per reading. With a small model (e.g. Claude Haiku) and 1024×768 pixels that is a fraction of a cent per reading. The interval sets the costs: every 30 minutes is about 100 pictures a day.

## Privacy

The pictures are sent to the provider of the chosen AI task. They only show the meter display if the camera is aligned accordingly.

## License

MIT
