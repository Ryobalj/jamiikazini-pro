# syllabus/services/institution_helpers.py
"""
Derives the full, professional school display name (e.g. "Shule ya Msingi
Mzingi" / "Mzingi Primary School") from the bare name a teacher registers
(e.g. "Mzingi") plus the curriculum family of the muhtasari being used — so
teachers only ever type their school's bare name once, and the correct
Awali/Msingi/Sekondari (or Pre-Primary/Primary/Secondary) naming is applied
consistently everywhere documents are generated. Also derives the correct
ClassLevel display name (Kiswahili vs English) for the same reason.
"""

from syllabus.i18n import sw as sw_i18n, en as en_i18n


def get_curriculum_level(is_awali: bool, is_sekondari: bool) -> str:
    """Map SubjectVersion.is_awali/is_sekondari to a curriculum-level key."""
    if is_awali:
        return "awali"
    if is_sekondari:
        return "sekondari"
    return "msingi"


def get_school_display_name(
    bare_name: str,
    *,
    is_awali: bool = False,
    is_sekondari: bool = False,
    language: str = "sw",
) -> str:
    """
    Combine a bare school name with the institution-type wording implied by
    the curriculum family (Awali/Msingi/Sekondari) in use.

    Kiswahili and English put this the opposite way round, so the ordering
    is language-dependent, not just the words:
    - Kiswahili prefixes it: get_school_display_name("Mzingi", language="sw")
      -> "Shule ya Msingi Mzingi".
    - English suffixes it: get_school_display_name("Mzingi", language="en")
      -> "Mzingi Primary School" (never "Primary School Mzingi").
    """
    bare_name = (bare_name or "").strip()
    if not bare_name:
        return ""

    i18n = sw_i18n if language == "sw" else en_i18n
    level = get_curriculum_level(is_awali, is_sekondari)
    prefix = i18n.SCHOOL_TYPE_PREFIX.get(level, i18n.SCHOOL_TYPE_PREFIX["msingi"])
    order = getattr(i18n, "SCHOOL_TYPE_ORDER", "prefix")

    if order == "suffix":
        # Avoid double-naming if a legacy record already has the full
        # English name stored (e.g. "Mzingi Primary School" entered by
        # hand before the frontend started stripping institution-type
        # words from the input).
        if bare_name.lower().endswith(prefix.lower()):
            return bare_name
        return f"{bare_name} {prefix}"

    # Avoid double-prefixing if a legacy record still has the full name
    # stored (e.g. seeded/entered before the frontend started stripping
    # institution-type words from the input).
    if bare_name.lower().startswith(prefix.lower()):
        return bare_name

    return f"{prefix} {bare_name}"


def get_class_level_display_name(class_level_name: str, language: str = "sw") -> str:
    """
    Translate a ClassLevel.name (stored in Kiswahili, e.g. "Kidato V",
    "DRS III", "Awali") into the form a document in the given language
    should show: unchanged for Kiswahili ("Kidato V"), or the English
    equivalent for English ("Form V"). Falls back to the stored name
    unchanged if it isn't in the lookup (e.g. a class level added later
    that hasn't been added to CLASS_LEVEL_NAMES yet), so display never
    breaks - it just stays Kiswahili until the mapping is updated.

    Only ever use this for DISPLAY. Anything that compares a class level
    against a fixed set of names (e.g. SchemeTimelineBuilder's
    NATIONAL_EXAM_CLASS_LEVELS gating) must keep using the raw,
    untranslated ClassLevel.name as its key.
    """
    class_level_name = (class_level_name or "").strip()
    if not class_level_name:
        return ""

    i18n = sw_i18n if language == "sw" else en_i18n
    return i18n.CLASS_LEVEL_NAMES.get(class_level_name, class_level_name)
