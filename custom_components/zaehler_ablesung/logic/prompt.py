"""Instructions for the AI task that reads the meter picture."""

from __future__ import annotations

from .units import TYPE_ELECTRICITY, TYPE_GAS, TYPE_HEAT, TYPE_OTHER, TYPE_WATER

METER_NAMES = {
    "de": {
        TYPE_HEAT: "Wärmezählers",
        TYPE_WATER: "Wasserzählers",
        TYPE_GAS: "Gaszählers",
        TYPE_ELECTRICITY: "Stromzählers",
        TYPE_OTHER: "Zählers",
    },
    "en": {
        TYPE_HEAT: "heat meter",
        TYPE_WATER: "water meter",
        TYPE_GAS: "gas meter",
        TYPE_ELECTRICITY: "electricity meter",
        TYPE_OTHER: "meter",
    },
}

# Suggested hints for a new meter; the user can change or delete them.
DEFAULT_HINTS = {
    "de": {
        TYPE_HEAT: "Die Anzeige ist ein LCD mit Sieben-Segment-Ziffern.",
        TYPE_WATER: (
            "Mechanisches Rollenzählwerk: schwarze Ziffern sind ganze m³, rote Ziffern die "
            "Nachkommastellen. Steht eine Rolle zwischen zwei Ziffern, nimm die kleinere "
            "(zwischen 9 und 0 die 9). Kleine runde Zeigerskalen nicht mitlesen."
        ),
        TYPE_GAS: (
            "Mechanisches Rollenzählwerk: schwarze Ziffern sind ganze m³, rote Ziffern die "
            "Nachkommastellen. Steht eine Rolle zwischen zwei Ziffern, nimm die kleinere "
            "(zwischen 9 und 0 die 9)."
        ),
        TYPE_ELECTRICITY: "Nur den Zählerstand für den Bezug (1.8.0) lesen.",
        TYPE_OTHER: "",
    },
    "en": {
        TYPE_HEAT: "The display is an LCD with seven-segment digits.",
        TYPE_WATER: (
            "Mechanical roller counter: black digits are whole m³, red digits are the "
            "decimals. If a roller is between two digits, take the lower one (between 9 "
            "and 0 take 9). Do not read the small round dials."
        ),
        TYPE_GAS: (
            "Mechanical roller counter: black digits are whole m³, red digits are the "
            "decimals. If a roller is between two digits, take the lower one (between 9 "
            "and 0 take 9)."
        ),
        TYPE_ELECTRICITY: "Only read the reading for consumption (1.8.0).",
        TYPE_OTHER: "",
    },
}

TEMPLATES = {
    "de": (
        "Das Bild zeigt die Anzeige eines {meter}. Der Zählerstand wird in {unit} "
        "{decimals_text} angezeigt (Beispiel: {example}).\n"
        "{point}"
        "{hints}"
        "Prüfe jede Ziffer einzeln.\n"
        "Gib ausschließlich den angezeigten Zahlenwert {all_decimals}zurück, mit Punkt als "
        "Dezimaltrennzeichen, ohne Einheit und ohne weiteren Text.\n"
        "Wenn die Zahl nicht vollständig und sicher lesbar ist, antworte nur: unlesbar"
    ),
    "en": (
        "The picture shows the display of a {meter}. The reading is shown in {unit} "
        "{decimals_text} (example: {example}).\n"
        "{point}"
        "{hints}"
        "Check every digit on its own.\n"
        "Return only the displayed number {all_decimals}with a dot as decimal separator, "
        "without unit and without any other text.\n"
        "If the number is not completely and reliably readable, answer only: unreadable"
    ),
}


TWO_PICTURES = {
    "de": (
        "Du bekommst zwei Bilder derselben Anzeige mit unterschiedlich heller Beleuchtung. "
        "Lies jede Ziffer auf dem Bild, auf dem sie besser zu erkennen ist.\n"
    ),
    "en": (
        "You get two pictures of the same display with lighting of different brightness. "
        "Read every digit in the picture where it is easier to see.\n"
    ),
}

HISTORY = {
    "de": (
        "Zur Plausibilitätsprüfung die letzten Zählerstände: {values}. Der Zählerstand "
        "steigt nur und ändert sich meist wenig. Nutze diese Werte nur, um bei einer "
        "unklaren Ziffer zu entscheiden. Lies trotzdem nur, was auf dem Bild steht, und "
        "übernimm keinen dieser Werte, wenn die Anzeige nicht lesbar ist.\n"
    ),
    "en": (
        "For a plausibility check the last readings: {values}. The reading only goes up "
        "and mostly changes little. Use these values only to decide about an unclear "
        "digit. Still read only what the picture shows, and do not take any of these "
        "values when the display is not readable.\n"
    ),
}


def context_notes(
    lang: str | None,
    pictures: int = 1,
    history: list[tuple[str, float]] | None = None,
    unit: str = "",
    decimals: int = 0,
) -> str:
    """Notes for this run in front of the instructions: two pictures, last readings
    (oldest first, with the local time as text)."""
    lang = language(lang)
    notes = TWO_PICTURES[lang] if pictures > 1 else ""
    if history:
        suffix = f" {unit}" if unit else ""
        places = max(0, int(decimals))
        values = ", ".join(f"{value:.{places}f}{suffix} ({when})" for when, value in history)
        notes += HISTORY[lang].format(values=values)
    return notes


def language(lang: str | None) -> str:
    return "de" if (lang or "").lower().startswith("de") else "en"


def example(decimals: int) -> str:
    whole = "1234"
    if decimals <= 0:
        return whole
    return f"{whole}.{('567890' * 2)[:decimals]}"


def default_hints(meter_type: str, lang: str | None) -> str:
    return DEFAULT_HINTS[language(lang)].get(meter_type, "")


def effective_instructions(
    custom: str | None,
    meter_type: str,
    unit: str,
    decimals: int,
    hints: str | None,
    lang: str | None,
) -> str:
    """The own instructions of a meter when set, otherwise the generated ones."""
    if custom and custom.strip():
        return custom.strip()
    return build_instructions(meter_type, unit, decimals, hints, lang)


def build_instructions(
    meter_type: str, unit: str, decimals: int, hints: str | None, lang: str | None
) -> str:
    """Instructions for one picture."""
    lang = language(lang)
    decimals = max(0, int(decimals))
    if lang == "de":
        decimals_text = (
            "ohne Nachkommastellen"
            if decimals == 0
            else "mit einer Nachkommastelle"
            if decimals == 1
            else f"mit {decimals} Nachkommastellen"
        )
        all_decimals = "mit allen Nachkommastellen " if decimals else ""
        point = (
            "Ist das Komma bzw. der Dezimalpunkt auf dem Bild nicht zu erkennen, gehören die "
            f"letzten {decimals} Ziffern hinter das Komma.\n"
            if decimals
            else ""
        )
    else:
        decimals_text = (
            "without decimals"
            if decimals == 0
            else "with one decimal"
            if decimals == 1
            else f"with {decimals} decimals"
        )
        all_decimals = "with all decimals " if decimals else ""
        point = (
            f"If the decimal point is not visible in the picture, the last {decimals} digits "
            "are the decimals.\n"
            if decimals
            else ""
        )
    hints = (hints or "").strip()
    return TEMPLATES[lang].format(
        meter=METER_NAMES[lang].get(meter_type, METER_NAMES[lang][TYPE_OTHER]),
        unit=unit or "-",
        decimals_text=decimals_text,
        example=example(decimals),
        hints=f"{hints}\n" if hints else "",
        all_decimals=all_decimals,
        point=point,
    )
