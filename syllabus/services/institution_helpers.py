# syllabus/services/institution_helpers.py
"""
Derives the full, professional school display name (e.g. "Shule ya Msingi
Mzingi") from the bare name a teacher registers (e.g. "Mzingi") plus the
curriculum family of the muhtasari being used — so teachers only ever type
their school's bare name once, and the correct Awali/Msingi/Sekondari
prefix is applied consistently everywhere documents are generated.
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
    Combine a bare school name with the institution-type prefix implied by
    the curriculum family (Awali/Msingi/Sekondari) in use.

    Example: get_school_display_name("Mzingi", is_awali=False,
    is_sekondari=False, language="sw") -> "Shule ya Msingi Mzingi"
    """
    bare_name = (bare_name or "").strip()
    if not bare_name:
        return ""

    i18n = sw_i18n if language == "sw" else en_i18n
    level = get_curriculum_level(is_awali, is_sekondari)
    prefix = i18n.SCHOOL_TYPE_PREFIX.get(level, i18n.SCHOOL_TYPE_PREFIX["msingi"])

    # Avoid double-prefixing if a legacy record still has the full name
    # stored (e.g. seeded/entered before the frontend started stripping
    # institution-type words from the input).
    if bare_name.lower().startswith(prefix.lower()):
        return bare_name

    return f"{prefix} {bare_name}"
