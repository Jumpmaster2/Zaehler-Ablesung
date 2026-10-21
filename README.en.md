# Zähler-Ablesung (meter reading)

[Deutsche Version](README.md)

Custom integration for Home Assistant that reads meters (heat, water, gas, electricity) with a camera. A cheap ESP32-CAM with ESPHome takes a picture of the display, a Home Assistant AI task (`ai_task`, e.g. Anthropic Claude, OpenAI, Google or a local model with image support) reads the value. A majority vote over several pictures and a plausibility check keep wrong readings out of your statistics.

Everything is set up in the **Zähler-Ablesung** dashboard in the sidebar: add a meter, choose camera and light, try the brightness with a test picture, set interval and checks. No automations, scripts or helpers needed.

> Status: version 0.2.1.

## How it works

### Taking a picture

1. The light (e.g. the flash LED of the ESP32-CAM) is switched on with the configured brightness.
2. After the warm-up time a few pictures are thrown away. Otherwise the ESP32-CAM still delivers an old picture without light from its buffer after a pause.
3. The real picture is taken, the light goes off.
4. Optionally the picture is rotated by any angle (up to ±180°), cropped to the **picture crop** and its **exposure** adjusted. This matters for wide-angle cameras where the display is otherwise only a small strip. In the dashboard the last picture is turned straight and the crop drawn over it with mouse or finger. When mounting the camera the **live picture** there helps (with the light on if wanted), without taking a test picture each time.
5. The picture the AI gets is stored as `/media/zaehler_ablesung/<meter id>/letztes.jpg` (the uncropped one as `original.jpg`) and shown by the camera entity **Last picture**.

### Reading with a majority vote

* The AI gets the picture and instructions built from meter type, unit, decimals and your **hints** (see "Show the instructions for the AI" in the editor). It answers only with the number or with "unreadable".
* Pictures are read until one value was read **twice**, at most the configured number of pictures (default 4). Without such a value the reading is "unreadable".

### Plausibility check

* **Increase too large:** if the value rose by more than *largest increase per hour × hours* since the last valid reading (at least half an hour, two hours without a previous value), it is rejected.
* **Smaller than before:** a smaller value is only taken when it is at most the *largest correction* lower and further pictures (default 2) all confirm it. It then counts as "corrected" (this fixes an earlier wrong reading).
* Rejected and corrected readings create a notification in Home Assistant (can be turned off). The picture is kept in `verworfen/` (the latest 20).
* The meter reading sensor uses state class `total` (not `total_increasing`), so a correction downwards is not counted as a meter reset in the statistics.

### Schedule

* Every meter is read automatically at its **interval** (checked every 5 minutes).
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
