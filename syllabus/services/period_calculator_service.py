# syllabus/services/period_calculator_service.py

from typing import List, Dict, Any, Optional
from django.utils.translation import gettext_lazy as _
import logging

logger = logging.getLogger(__name__)


class PeriodCalculatorService:
    """
    Production-ready service for allocating subject periods across studying weeks.
    
    Handles two scenarios:
    1. Normal: Sufficient weeks available for all periods
    2. Adjusted: Insufficient weeks, periods are distributed evenly
    """

    def __init__(
        self,
        calendar_service,
        periods_per_week: int,
        total_periods_needed: int,
    ):
        """
        Initialize period calculator.
        
        Args:
            calendar_service: CalendarService instance
            periods_per_week: Number of periods allocated per week
            total_periods_needed: Total periods required for the syllabus
            
        Raises:
            ValueError: If inputs are invalid
        """
        # Validate inputs
        if not calendar_service:
            raise ValueError(_("Calendar service is required"))
        
        if periods_per_week <= 0:
            raise ValueError(_("Periods per week must be greater than zero"))
        
        if total_periods_needed <= 0:
            raise ValueError(_("Total periods needed must be greater than zero"))

        self.calendar = calendar_service
        self.periods_per_week = periods_per_week
        self.total_periods_needed = total_periods_needed

        # Get studying weeks from calendar
        self.studying_weeks = self.calendar.get_studying_weeks()
        
        logger.info(
            f"PeriodCalculator initialized: "
            f"{periods_per_week} periods/week, "
            f"{total_periods_needed} total periods needed, "
            f"{len(self.studying_weeks)} studying weeks available"
        )

    # ------------------------------------------------------------------
    # PUBLIC API
    # ------------------------------------------------------------------

    def calculate(self) -> Dict[str, Any]:
        """
        Calculate period allocation plan.
        
        Returns:
            Dict with allocation plan and statistics
            
        Example:
            {
                "status": "ok" | "adjusted",
                "total_periods_needed": 100,
                "total_available_periods": 120,
                "unused_periods": 20,
                "shortage": 0,
                "weeks": [
                    {"week": 1, "periods": 4, "status": "normal"},
                    ...
                ],
                "warning": None | "Not enough studying weeks..."
            }
        """
        logger.debug("Starting period calculation")
        
        total_available = self._total_available_periods()
        
        # Log calculation context
        logger.debug(
            f"Calculation context: "
            f"needed={self.total_periods_needed}, "
            f"available={total_available}, "
            f"weeks={len(self.studying_weeks)}"
        )
        
        # Choose allocation strategy
        if total_available < self.total_periods_needed:
            result = self._adjusted_plan(total_available)
            logger.warning(
                f"Insufficient periods: needed {self.total_periods_needed}, "
                f"available {total_available}, shortage {result['shortage']}"
            )
        else:
            result = self._normal_plan()
            logger.info(
                f"Sufficient periods: needed {self.total_periods_needed}, "
                f"available {total_available}, unused {result['unused_periods']}"
            )
        
        return result

    # ------------------------------------------------------------------
    # ALLOCATION STRATEGIES
    # ------------------------------------------------------------------

    def _total_available_periods(self) -> int:
        """Calculate total periods available across all studying weeks."""
        return len(self.studying_weeks) * self.periods_per_week

    def _normal_plan(self) -> Dict[str, Any]:
        """
        Allocate periods when sufficient weeks are available.
        
        Strategy: Fill weeks sequentially until all periods are allocated.
        """
        allocation = []
        remaining = self.total_periods_needed
        
        logger.debug(f"Using normal plan allocation, remaining periods: {remaining}")

        for week in self.studying_weeks:
            if remaining <= 0:
                break

            # Allocate up to periods_per_week for this week
            periods = min(self.periods_per_week, remaining)
            
            allocation.append({
                "week": week,
                "periods": periods,
                "status": "normal",
                "is_full": periods == self.periods_per_week,
            })

            remaining -= periods
        
        # Calculate unused periods
        total_available = self._total_available_periods()
        unused_periods = total_available - self.total_periods_needed
        
        # Fill remaining weeks with 0 periods for completeness
        allocated_weeks = len(allocation)
        for week in self.studying_weeks[allocated_weeks:]:
            allocation.append({
                "week": week,
                "periods": 0,
                "status": "unused",
                "is_full": False,
            })

        return {
            "status": "ok",
            "total_periods_needed": self.total_periods_needed,
            "total_available_periods": total_available,
            "unused_periods": unused_periods,
            "shortage": 0,
            "allocated_weeks": allocated_weeks,
            "total_weeks": len(self.studying_weeks),
            "utilization_percentage": (self.total_periods_needed / total_available * 100) if total_available > 0 else 0,
            "weeks": allocation,
            "warning": None,
        }

    def _adjusted_plan(self, total_available: int) -> Dict[str, Any]:
        """
        Distribute periods evenly when demand exceeds supply.
        
        Strategy: Evenly distribute available periods across all weeks.
        """
        weeks_count = len(self.studying_weeks)
        
        if weeks_count == 0:
            return {
                "status": "error",
                "total_periods_needed": self.total_periods_needed,
                "total_available_periods": 0,
                "shortage": self.total_periods_needed,
                "allocated_weeks": 0,
                "total_weeks": 0,
                "utilization_percentage": 0,
                "weeks": [],
                "warning": _("No studying weeks available."),
                "error": _("Cannot allocate periods without studying weeks."),
            }
        
        # Calculate base allocation per week
        base_periods = total_available // weeks_count
        extra_periods = total_available % weeks_count
        
        logger.debug(
            f"Adjusted plan: {weeks_count} weeks, "
            f"base={base_periods}/week, extra={extra_periods} weeks get +1"
        )

        allocation = []
        
        for index, week in enumerate(self.studying_weeks):
            # Distribute extra periods to first 'extra_periods' weeks
            periods = base_periods + (1 if index < extra_periods else 0)
            
            allocation.append({
                "week": week,
                "periods": periods,
                "status": "adjusted",
                "is_full": periods == self.periods_per_week,
                "is_extra": index < extra_periods,
            })

        shortage = self.total_periods_needed - total_available
        
        return {
            "status": "adjusted",
            "total_periods_needed": self.total_periods_needed,
            "total_available_periods": total_available,
            "shortage": shortage,
            "allocated_weeks": weeks_count,
            "total_weeks": weeks_count,
            "utilization_percentage": 100,  # Using all available periods
            "average_periods_per_week": total_available / weeks_count if weeks_count > 0 else 0,
            "weeks": allocation,
            "warning": _(
                "Not enough studying weeks. "
                f"Shortage of {shortage} periods. "
                "Periods have been evenly distributed across available weeks."
            ),
        }

    # ------------------------------------------------------------------
    # UTILITY METHODS
    # ------------------------------------------------------------------

    def get_summary(self) -> Dict[str, Any]:
        """Get calculation summary without detailed week allocation."""
        result = self.calculate()
        
        return {
            "status": result["status"],
            "total_periods_needed": result["total_periods_needed"],
            "total_available_periods": result["total_available_periods"],
            "shortage": result.get("shortage", 0),
            "unused_periods": result.get("unused_periods", 0),
            "allocated_weeks": result.get("allocated_weeks", 0),
            "total_weeks": result.get("total_weeks", 0),
            "utilization_percentage": result.get("utilization_percentage", 0),
            "warning": result.get("warning"),
        }

    def validate_allocation(self) -> Dict[str, Any]:
        """Validate if allocation is feasible and provide recommendations."""
        total_available = self._total_available_periods()
        
        validation = {
            "is_feasible": total_available >= self.total_periods_needed,
            "total_available": total_available,
            "total_needed": self.total_periods_needed,
            "difference": total_available - self.total_periods_needed,
            "studying_weeks_count": len(self.studying_weeks),
            "recommendations": [],
        }
        
        if total_available < self.total_periods_needed:
            shortage = self.total_periods_needed - total_available
            validation["recommendations"].append(
                _(
                    f"Increase teaching weeks or reduce syllabus content. "
                    f"Shortage: {shortage} periods."
                )
            )
            
            # Calculate needed additional weeks
            additional_weeks_needed = -(-shortage // self.periods_per_week)  # Ceiling division
            validation["recommendations"].append(
                _(
                    f"Need approximately {additional_weeks_needed} "
                    f"additional week(s) at {self.periods_per_week} periods/week."
                )
            )
        
        return validation

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"PeriodCalculatorService("
            f"periods_per_week={self.periods_per_week}, "
            f"total_needed={self.total_periods_needed}, "
            f"weeks={len(self.studying_weeks)})"
        )