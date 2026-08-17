# syllabus/services/lesson_diagrams.py
"""
Programmatically-drawn illustrative diagrams for the Nukuu za Somo (lesson
notes) document, using reportlab's vector graphics — no image files or
uploads needed. Each function takes a diagram_type key (matching
SpecificLearningActivity.diagram_type) and returns a reportlab Drawing, or
None if there's no diagram for that key.
"""

from reportlab.graphics.shapes import Drawing, Rect, Line, String, Circle, Wedge, Group
from reportlab.lib import colors
from reportlab.lib.units import mm


def _labelled_rectangle() -> Drawing:
    """Rectangle with labelled length/width, for perimeter & area topics."""
    d = Drawing(220, 140)
    x, y, w, h = 40, 30, 130, 70
    d.add(Rect(x, y, w, h, fillColor=colors.HexColor("#EAF2FF"), strokeColor=colors.black, strokeWidth=1.2))
    d.add(String(x + w / 2, y + h + 10, "Urefu", textAnchor="middle", fontSize=9))
    d.add(String(x - 10, y + h / 2, "Upana", textAnchor="end", fontSize=9))
    d.add(String(x + w / 2, y - 15, "Mzingo = 2 x (Urefu + Upana)   Eneo = Urefu x Upana",
                  textAnchor="middle", fontSize=7.5))
    return d


def _fraction_bar() -> Drawing:
    """Two bars split into different numbers of equal parts, for comparing
    fractions (matches the 1/2 vs 1/3-style comparison exercises)."""
    d = Drawing(220, 110)
    bar_w, bar_h = 180, 22
    x0 = 20

    # Bar A: halves, first half shaded
    y = 65
    parts_a = 2
    for i in range(parts_a):
        seg_w = bar_w / parts_a
        fill = colors.HexColor("#8FBFFF") if i == 0 else colors.white
        d.add(Rect(x0 + i * seg_w, y, seg_w, bar_h, fillColor=fill, strokeColor=colors.black))
    d.add(String(x0 - 8, y + bar_h / 2 - 3, "1/2", textAnchor="end", fontSize=9))

    # Bar B: thirds, first third shaded
    y2 = 25
    parts_b = 3
    for i in range(parts_b):
        seg_w = bar_w / parts_b
        fill = colors.HexColor("#8FBFFF") if i == 0 else colors.white
        d.add(Rect(x0 + i * seg_w, y2, seg_w, bar_h, fillColor=fill, strokeColor=colors.black))
    d.add(String(x0 - 8, y2 + bar_h / 2 - 3, "1/3", textAnchor="end", fontSize=9))

    d.add(String(x0 + bar_w / 2, 95, "Sehemu iliyotiwa rangi zaidi ndiyo kubwa zaidi",
                  textAnchor="middle", fontSize=7.5))
    return d


def _clock_face() -> Drawing:
    """Simple analog clock face with hour marks and two hands."""
    d = Drawing(160, 160)
    cx, cy, r = 80, 80, 60
    d.add(Circle(cx, cy, r, fillColor=colors.white, strokeColor=colors.black, strokeWidth=1.5))
    import math
    for hour in range(12):
        angle = math.radians(90 - hour * 30)
        x1 = cx + (r - 8) * math.cos(angle)
        y1 = cy + (r - 8) * math.sin(angle)
        x2 = cx + r * math.cos(angle)
        y2 = cy + r * math.sin(angle)
        d.add(Line(x1, y1, x2, y2, strokeColor=colors.black))
        lx = cx + (r - 18) * math.cos(angle)
        ly = cy + (r - 18) * math.sin(angle) - 3
        label = "12" if hour == 0 else str(hour)
        d.add(String(lx, ly, label, textAnchor="middle", fontSize=7))
    # Hour hand pointing to 2, minute hand pointing to 6 (2:30-ish)
    hour_angle = math.radians(90 - 2 * 30)
    min_angle = math.radians(90 - 6 * 6)
    d.add(Line(cx, cy, cx + (r * 0.5) * math.cos(hour_angle), cy + (r * 0.5) * math.sin(hour_angle),
               strokeColor=colors.black, strokeWidth=2.5))
    d.add(Line(cx, cy, cx + (r * 0.8) * math.cos(min_angle), cy + (r * 0.8) * math.sin(min_angle),
               strokeColor=colors.black, strokeWidth=1.5))
    d.add(Circle(cx, cy, 2.5, fillColor=colors.black))
    return d


def _unit_conversion_ladder() -> Drawing:
    """Boxes km -> m -> cm with the multiplier between each step."""
    d = Drawing(240, 70)
    labels = ["km", "m", "cm"]
    factors = ["x 1000", "x 100"]
    box_w, box_h = 50, 30
    gap = 55
    y = 25
    for i, label in enumerate(labels):
        x = 15 + i * (box_w + gap - box_w)
        x = 15 + i * gap
        d.add(Rect(x, y, box_w, box_h, fillColor=colors.HexColor("#EAF2FF"), strokeColor=colors.black))
        d.add(String(x + box_w / 2, y + box_h / 2 - 4, label, textAnchor="middle", fontSize=10))
        if i < len(factors):
            ax1 = x + box_w
            ax2 = x + gap
            d.add(Line(ax1, y + box_h / 2, ax2, y + box_h / 2, strokeColor=colors.black))
            d.add(String((ax1 + ax2) / 2, y + box_h / 2 + 6, factors[i], textAnchor="middle", fontSize=7.5))
    d.add(String(120, 60, "(gawanya ukienda upande mwingine)", textAnchor="middle", fontSize=7))
    return d


def _place_value_chart() -> Drawing:
    """Simple decimal place-value chart, e.g. for 6.75."""
    d = Drawing(220, 70)
    headers = ["Mia", "Kumi", "Moja", ".", "Sehemu ya 10", "Sehemu ya 100"]
    values = ["", "", "6", ".", "7", "5"]
    col_w = 220 / len(headers)
    for i, (h, v) in enumerate(zip(headers, values)):
        x = i * col_w
        d.add(Rect(x, 25, col_w, 25, fillColor=colors.white, strokeColor=colors.black))
        d.add(String(x + col_w / 2, 40, v, textAnchor="middle", fontSize=10))
        d.add(String(x + col_w / 2, 8, h, textAnchor="middle", fontSize=6))
    return d


def _roman_numerals_chart() -> Drawing:
    """Value chart for the 7 Roman numeral symbols."""
    d = Drawing(240, 55)
    symbols = ["I", "V", "X", "L", "C", "D", "M"]
    values = ["1", "5", "10", "50", "100", "500", "1000"]
    col_w = 240 / len(symbols)
    for i, (s, v) in enumerate(zip(symbols, values)):
        x = i * col_w
        d.add(Rect(x, 20, col_w, 25, fillColor=colors.HexColor("#EAF2FF"), strokeColor=colors.black))
        d.add(String(x + col_w / 2, 27, s, textAnchor="middle", fontSize=12))
        d.add(String(x + col_w / 2, 5, v, textAnchor="middle", fontSize=8))
    return d


_BUILDERS = {
    "roman_numerals_chart": _roman_numerals_chart,
    "unit_conversion_ladder": _unit_conversion_ladder,
    "rectangle_diagram": _labelled_rectangle,
    "fraction_bar": _fraction_bar,
    "clock_face": _clock_face,
    "place_value_chart": _place_value_chart,
}


def build_diagram(diagram_type: str):
    """Return a reportlab Drawing for diagram_type, or None if unknown/blank."""
    builder = _BUILDERS.get((diagram_type or "").strip())
    return builder() if builder else None
