# jammikazini/syllabus/tests/test_models/test_annual_calendar_model.py

import pytest
from datetime import date
from django.db import IntegrityError
from syllabus.models.annual_calendar import AnnualCalendar

@pytest.mark.django_db
class TestAnnualCalendarModel:

    def test_can_create_annual_calendar(self):
        ac = AnnualCalendar.objects.create(
            institute="Shule ya Msingi Mzingi",
            year=date.today().year,
            total_learning_days=200,
            term_start_month="January",
            term_start_week=1,
            term_start_date=date.today(),
            midterm_break_start_month="February",
            midterm_break_start_week=2,
            midterm_break_start_date=date.today(),
            term_break_start_month="March",
            term_break_start_week=3,
            term_break_start_date=date.today(),
            midannual_start_month="April",
            midannual_start_week=4,
            midannual_start_date=date.today(),
            midannual_break_start_month="May",
            midannual_break_start_week=1,
            midannual_break_start_date=date.today(),
            annual_break_start_month="December",
            annual_break_start_week=4,
            annual_break_start_date=date.today(),
        )
        assert ac.pk is not None
        assert ac.status is True
        assert str(ac) == f"Shule ya Msingi Mzingi ({date.today().year})"

    def test_year_choices_contains_current_previous_next(self):
        choices = [y[0] for y in AnnualCalendar.year_choices()]
        current = date.today().year
        assert current-1 in choices
        assert current in choices
        assert current+1 in choices

    def test_unique_together_constraint(self):
        # Create first instance
        AnnualCalendar.objects.create(
            institute="Shule ya Msingi Mzingi",
            year=date.today().year,
            total_learning_days=200,
            term_start_month="January",
            term_start_week=1,
            term_start_date=date.today(),
            midterm_break_start_month="February",
            midterm_break_start_week=2,
            midterm_break_start_date=date.today(),
            term_break_start_month="March",
            term_break_start_week=3,
            term_break_start_date=date.today(),
            midannual_start_month="April",
            midannual_start_week=4,
            midannual_start_date=date.today(),
            midannual_break_start_month="May",
            midannual_break_start_week=1,
            midannual_break_start_date=date.today(),
            annual_break_start_month="December",
            annual_break_start_week=4,
            annual_break_start_date=date.today(),
        )

        # Attempt to create duplicate should raise IntegrityError
        with pytest.raises(IntegrityError):
            AnnualCalendar.objects.create(
                institute="Shule ya Msingi Mzingi",
                year=date.today().year,
                total_learning_days=180,
                term_start_month="January",
                term_start_week=1,
                term_start_date=date.today(),
                midterm_break_start_month="February",
                midterm_break_start_week=2,
                midterm_break_start_date=date.today(),
                term_break_start_month="March",
                term_break_start_week=3,
                term_break_start_date=date.today(),
                midannual_start_month="April",
                midannual_start_week=4,
                midannual_start_date=date.today(),
                midannual_break_start_month="May",
                midannual_break_start_week=1,
                midannual_break_start_date=date.today(),
                annual_break_start_month="December",
                annual_break_start_week=4,
                annual_break_start_date=date.today(),
            )

    def test_ordering_by_year_and_institute(self):
        # Create two instances
        ac1 = AnnualCalendar.objects.create(
            institute="A Shule",
            year=date.today().year,
            total_learning_days=200,
            term_start_month="January",
            term_start_week=1,
            term_start_date=date.today(),
            midterm_break_start_month="February",
            midterm_break_start_week=2,
            midterm_break_start_date=date.today(),
            term_break_start_month="March",
            term_break_start_week=3,
            term_break_start_date=date.today(),
            midannual_start_month="April",
            midannual_start_week=4,
            midannual_start_date=date.today(),
            midannual_break_start_month="May",
            midannual_break_start_week=1,
            midannual_break_start_date=date.today(),
            annual_break_start_month="December",
            annual_break_start_week=4,
            annual_break_start_date=date.today(),
        )
        ac2 = AnnualCalendar.objects.create(
            institute="B Shule",
            year=date.today().year - 1,
            total_learning_days=200,
            term_start_month="January",
            term_start_week=1,
            term_start_date=date.today(),
            midterm_break_start_month="February",
            midterm_break_start_week=2,
            midterm_break_start_date=date.today(),
            term_break_start_month="March",
            term_break_start_week=3,
            term_break_start_date=date.today(),
            midannual_start_month="April",
            midannual_start_week=4,
            midannual_start_date=date.today(),
            midannual_break_start_month="May",
            midannual_break_start_week=1,
            midannual_break_start_date=date.today(),
            annual_break_start_month="December",
            annual_break_start_week=4,
            annual_break_start_date=date.today(),
        )
        results = list(AnnualCalendar.objects.all())
        assert results == [ac2, ac1]  # ordered by year, then institute