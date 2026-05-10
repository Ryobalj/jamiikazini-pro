import pytest
from datetime import date, timedelta
from syllabus.models.annual_calendar import AnnualCalendar
from syllabus.serializers.annual_calendar_serializer import AnnualCalendarSerializer

@pytest.mark.django_db
class TestAnnualCalendarSerializer:

    @pytest.fixture
    def base_data(self):
        today = date.today()
        return {
            "institute": "Shule ya Msingi Mzingi",
            "year": today.year,
            "total_learning_days": 200,
            "term_start_month": "January",
            "term_start_week": 1,
            "term_start_date": date(today.year, 1, 3),
            "midterm_break_start_month": "February",
            "midterm_break_start_week": 2,
            "midterm_break_start_date": date(today.year, 2, 10),
            "term_break_start_month": "March",
            "term_break_start_week": 3,
            "term_break_start_date": date(today.year, 3, 15),
            "midannual_start_month": "April",
            "midannual_start_week": 1,
            "midannual_start_date": date(today.year, 4, 2),
            "midannual_break_start_month": "May",
            "midannual_break_start_week": 2,
            "midannual_break_start_date": date(today.year, 5, 10),
            "annual_break_start_month": "June",
            "annual_break_start_week": 3,
            "annual_break_start_date": date(today.year, 6, 16),
            "status": True
        }

    def test_valid_data_saves(self, base_data):
        serializer = AnnualCalendarSerializer(data=base_data)
        assert serializer.is_valid(), serializer.errors
        ac = serializer.save()
        assert ac.id is not None

    def test_year_validation_rejects_invalid(self, base_data):
        base_data["year"] = date.today().year + 5
        serializer = AnnualCalendarSerializer(data=base_data)
        assert not serializer.is_valid()
        assert "year" in serializer.errors

    def test_unique_institute_year_validation(self, base_data):
        AnnualCalendar.objects.create(**base_data)
        serializer = AnnualCalendarSerializer(data=base_data)
        assert not serializer.is_valid()
        assert "institute" in serializer.errors

    def test_date_must_be_in_declared_year(self, base_data):
        base_data["term_start_date"] = date(base_data["year"] + 1, 1, 5)
        serializer = AnnualCalendarSerializer(data=base_data)
        assert not serializer.is_valid()
        assert "term_start_date" in serializer.errors

    def test_month_and_date_consistency(self, base_data):
        # mismatch month vs date
        base_data["term_start_month"] = "February"
        base_data["term_start_date"] = date(base_data["year"], 1, 5)
        serializer = AnnualCalendarSerializer(data=base_data)
        assert not serializer.is_valid()
        assert "term_start_date" in serializer.errors

    def test_week_mismatch(self, base_data):
        # set date that falls in week 2 but give week=1
        base_data["term_start_date"] = date(base_data["year"], 1, 10)  # day 10 -> week 2
        base_data["term_start_week"] = 1
        serializer = AnnualCalendarSerializer(data=base_data)
        assert not serializer.is_valid()
        assert "term_start_week" in serializer.errors

    def test_total_learning_days_bounds(self, base_data):
        base_data["total_learning_days"] = 0
        serializer = AnnualCalendarSerializer(data=base_data)
        assert not serializer.is_valid()
        assert "total_learning_days" in serializer.errors