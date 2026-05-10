# syllabus/serializers/annual_calendar_serializer.py

from rest_framework import serializers
from syllabus.models.annual_calendar import AnnualCalendar
from datetime import date
from typing import Any, Dict, Optional

MONTH_NAME_TO_NUM = {
    "January": 1, "February": 2, "March": 3, "April": 4,
    "May": 5, "June": 6, "July": 7, "August": 8,
    "September": 9, "October": 10, "November": 11, "December": 12,
}


def week_of_month(dt: date) -> int:
    """
    day 1-7 -> week 1, 8-14 -> week 2, etc.
    """
    return (dt.day - 1) // 7 + 1


class AnnualCalendarSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnnualCalendar
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")

    # -------------------------
    # Convert incoming types
    # -------------------------
    def to_internal_value(self, data: Dict[str, Any]) -> Dict[str, Any]:
        data = dict(data)
        week_fields = [
            "term_start_week",
            "midterm_break_start_week",
            "midterm_start_week",
            "term_break_start_week",
            "midannual_start_week",
            "midannual_break_start_week",
            "annual_startweek",
            "annual_break_start_week",
        ]
        for wf in week_fields:
            if wf in data and data[wf] not in (None, ""):
                try:
                    data[wf] = int(data[wf])
                except Exception:
                    pass

        if "total_learning_days" in data and data["total_learning_days"] not in (None, ""):
            try:
                data["total_learning_days"] = int(data["total_learning_days"])
            except Exception:
                pass

        return super().to_internal_value(data)

    # -------------------------
    # Validate year
    # -------------------------
    def validate_year(self, value):
        if not isinstance(value, int):
            raise serializers.ValidationError("Mwaka lazima awe integer.")
        if value < 1900 or value > 2100:
            raise serializers.ValidationError("Mwaka lazima uwe kati ya 1900 na 2100.")
        return value

    # -------------------------
    # Helper: resolve field value from attrs or instance
    # -------------------------
    def _resolved(self, attrs: Dict[str, Any], field: str) -> Optional[Any]:
        if field in attrs:
            return attrs.get(field)
        if getattr(self, "instance", None):
            return getattr(self.instance, field)
        return None

    # -------------------------
    # Main validate
    # -------------------------
    def validate(self, attrs):
        attrs = super().validate(attrs)
        instance = getattr(self, "instance", None)

        def val(k):
            return self._resolved(attrs, k)

        # 1) Uniqueness: year + institute
        year = val("year")
        institute = val("institute")
        if year and institute:
            qs = AnnualCalendar.objects.filter(year=year, institute__iexact=institute)
            if instance:
                qs = qs.exclude(pk=instance.pk)
            if qs.exists():
                raise serializers.ValidationError({
                    "institute": "Kalenda ya mwaka huu tayari ipo kwa taasisi hii."
                })

        # 2) Date fields list
        date_fields = [
            "term_start_date",
            "midterm_break_start_date",
            "midterm_start_date",
            "term_break_start_date",
            "annual_startdate",
            "midannual_break_start_date",
            "midannual_start_date",
            "annual_break_start_date",
        ]

        # 3) Ensure provided dates belong to selected year
        if year is not None:
            for df in date_fields:
                d = val(df)
                if d and getattr(d, "year", None) != year:
                    raise serializers.ValidationError({
                        df: f"{df} lazima iwe mwaka {year}."
                    })

        # 4) Chronological checks (corrected order)
        pairs = [
            ("term_start_date", "midterm_break_start_date"),
            ("midterm_break_start_date", "midterm_start_date"),
            ("midterm_start_date", "term_break_start_date"),
            ("term_break_start_date", "annual_startdate"),
            ("annual_startdate", "midannual_break_start_date"),
            ("midannual_break_start_date", "midannual_start_date"),
            ("midannual_start_date", "annual_break_start_date"),
        ]
        for s_field, e_field in pairs:
            s_val = val(s_field)
            e_val = val(e_field)
            if s_val and e_val and s_val > e_val:
                raise serializers.ValidationError({
                    s_field: f"{s_field} haiwezi kuwa baada ya {e_field}."
                })

        # 5) Month <-> Date <-> Week consistency
        month_date_pairs = [
            ("term_start_month", "term_start_date", "term_start_week"),
            ("midterm_break_start_month", "midterm_break_start_date", "midterm_break_start_week"),
            ("midterm_start_month", "midterm_start_date", "midterm_start_week"),
            ("term_break_start_month", "term_break_start_date", "term_break_start_week"),
            ("annual_startmonth", "annual_startdate", "annual_startweek"),
            ("midannual_start_month", "midannual_start_date", "midannual_start_week"),
            ("midannual_break_start_month", "midannual_break_start_date", "midannual_break_start_week"),
            ("annual_break_start_month", "annual_break_start_date", "annual_break_start_week"),
        ]
        for month_field, date_field, week_field in month_date_pairs:
            m = val(month_field)
            d = val(date_field)
            w = val(week_field)
            if d and m:
                expected_month_num = MONTH_NAME_TO_NUM.get(m)
                if expected_month_num is None:
                    raise serializers.ValidationError({
                        month_field: f"{month_field} ni chaguo batili."
                    })
                if d.month != expected_month_num:
                    raise serializers.ValidationError({
                        date_field: f"{date_field} inapaswa kuwa mwezi {m}."
                    })
            if d and w is not None:
                try:
                    computed_week = week_of_month(d)
                except Exception:
                    computed_week = None
                if computed_week is not None and w != computed_week:
                    raise serializers.ValidationError({
                        week_field: f"{week_field} haikutegemea tarehe {date_field} (ilitarajiwa week={computed_week})."
                    })

        # 6) total_learning_days sanity check
        tld = val("total_learning_days")
        if tld is not None:
            try:
                tld_int = int(tld)
            except Exception:
                raise serializers.ValidationError({
                    "total_learning_days": "total_learning_days lazima iwe integer."
                })
            if tld_int < 1 or tld_int > 400:
                raise serializers.ValidationError({
                    "total_learning_days": "Jumla ya siku lazima iwe kati ya 1 na 400."
                })
            attrs["total_learning_days"] = tld_int

        return attrs