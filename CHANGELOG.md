# Changelog

## Unreleased

### Added

- External light per meter (section "External light" / "Externe Beleuchtung"): any `light` or `switch` entity that is switched on for the pictures of a reading or test picture, besides the light of the camera. Options `external_light`, `external_light_mode` (`capture` or `permanent`), `external_light_brightness` (only for `light`, default 100 %), `external_light_lead_time` (0 to 30 s, default 2 s) and `external_light_turn_off` (default on). In the mode `capture` it is switched off again also when taking or reading the pictures fails. An entity that is not available or a failed switch only logs a warning; the meter is read anyway. Without an external light nothing changes; existing meters need no migration.
