from dataclasses import dataclass
from typing import Optional

from app.core.config import settings


# ── Fare Result ───────────────────────────────────────────────────────────────
@dataclass
class PassengerFare:
    category: str                    # "adult" | "child" | "senior"
    count: int
    unit_fare_paise: int             # fare per single passenger
    total_fare_paise: int
    concession_percent: int
    base_fare_paise: int             # before concession


@dataclass
class FareBreakdown:
    boarding_stop: str
    destination_stop: str
    distance_km: float
    adult: PassengerFare
    child: PassengerFare
    senior: PassengerFare
    total_fare_paise: int

    @property
    def total_fare_rupees(self) -> float:
        return round(self.total_fare_paise / 100, 2)

    @property
    def adult_fare_rupees(self) -> float:
        return round(self.adult.total_fare_paise / 100, 2)

    @property
    def child_fare_rupees(self) -> float:
        return round(self.child.total_fare_paise / 100, 2)

    @property
    def senior_fare_rupees(self) -> float:
        return round(self.senior.total_fare_paise / 100, 2)

    def to_dict(self) -> dict:
        return {
            "boarding_stop": self.boarding_stop,
            "destination_stop": self.destination_stop,
            "distance_km": self.distance_km,
            "total_fare_rupees": self.total_fare_rupees,
            "total_fare_paise": self.total_fare_paise,
            "breakdown": {
                "adult": {
                    "count": self.adult.count,
                    "unit_fare_rupees": round(self.adult.unit_fare_paise / 100, 2),
                    "total_fare_rupees": self.adult_fare_rupees,
                    "concession_percent": self.adult.concession_percent,
                },
                "child": {
                    "count": self.child.count,
                    "unit_fare_rupees": round(self.child.unit_fare_paise / 100, 2),
                    "total_fare_rupees": self.child_fare_rupees,
                    "concession_percent": self.child.concession_percent,
                },
                "senior": {
                    "count": self.senior.count,
                    "unit_fare_rupees": round(self.senior.unit_fare_paise / 100, 2),
                    "total_fare_rupees": self.senior_fare_rupees,
                    "concession_percent": self.senior.concession_percent,
                },
            },
        }


# ── Core Fare Engine ──────────────────────────────────────────────────────────
class FareEngine:
    """
    Implements Haryana Roadways fare rules:
    - Base fare: ₹0.85 per km (ordinary)
    - Minimum fare: ₹10
    - Children (under 12): 50% concession
    - Senior citizens (60+): 50% concession
    - Fares stored and calculated in paise to avoid float errors
    """

    def _base_fare_paise(self, distance_km: float) -> int:
        """Calculate raw base fare in paise before concessions."""
        raw = int(distance_km * settings.FARE_BASE_PAISE_PER_KM)
        return max(raw, settings.FARE_MIN_PAISE)

    def _round_to_nearest_50_paise(self, paise: int) -> int:
        """
        Haryana Roadways rounds fares to nearest 50 paise.
        e.g. 1820 paise → 1850, 1860 → 1900
        """
        remainder = paise % 50
        if remainder == 0:
            return paise
        return paise + (50 - remainder)

    def _apply_concession(self, base_paise: int, percent: int) -> int:
        """Apply concession percentage, then round."""
        discounted = int(base_paise * (100 - percent) / 100)
        return max(discounted, settings.FARE_MIN_PAISE)

    def calculate(
        self,
        distance_km: float,
        boarding_stop: str,
        destination_stop: str,
        adult_count: int = 1,
        child_count: int = 0,
        senior_count: int = 0,
    ) -> FareBreakdown:
        """
        Calculate full fare breakdown for a journey.

        Args:
            distance_km:       distance between boarding and destination stops
            boarding_stop:     name of boarding stop
            destination_stop:  name of destination stop
            adult_count:       number of adult passengers
            child_count:       number of child passengers (under 12)
            senior_count:      number of senior citizen passengers (60+)

        Returns:
            FareBreakdown with per-category and total fares
        """
        if distance_km <= 0:
            raise ValueError("Distance must be greater than 0")
        if adult_count < 0 or child_count < 0 or senior_count < 0:
            raise ValueError("Passenger counts cannot be negative")
        if adult_count + child_count + senior_count == 0:
            raise ValueError("At least one passenger required")

        base = self._base_fare_paise(distance_km)
        base = self._round_to_nearest_50_paise(base)

        # Adult — no concession
        adult_unit = base
        adult_total = adult_unit * adult_count

        # Child — 50% concession
        child_unit = self._apply_concession(base, settings.CHILD_FARE_PERCENT)
        child_unit = self._round_to_nearest_50_paise(child_unit)
        child_total = child_unit * child_count

        # Senior citizen — 50% concession
        senior_unit = self._apply_concession(base, settings.SENIOR_FARE_PERCENT)
        senior_unit = self._round_to_nearest_50_paise(senior_unit)
        senior_total = senior_unit * senior_count

        total = adult_total + child_total + senior_total

        return FareBreakdown(
            boarding_stop=boarding_stop,
            destination_stop=destination_stop,
            distance_km=round(distance_km, 2),
            adult=PassengerFare(
                category="adult",
                count=adult_count,
                unit_fare_paise=adult_unit,
                total_fare_paise=adult_total,
                concession_percent=0,
                base_fare_paise=base,
            ),
            child=PassengerFare(
                category="child",
                count=child_count,
                unit_fare_paise=child_unit,
                total_fare_paise=child_total,
                concession_percent=settings.CHILD_FARE_PERCENT,
                base_fare_paise=base,
            ),
            senior=PassengerFare(
                category="senior",
                count=senior_count,
                unit_fare_paise=senior_unit,
                total_fare_paise=senior_total,
                concession_percent=settings.SENIOR_FARE_PERCENT,
                base_fare_paise=base,
            ),
            total_fare_paise=total,
        )

    def calculate_from_stops(
        self,
        route_stops: list,
        boarding_stop_name: str,
        destination_stop_name: str,
        adult_count: int = 1,
        child_count: int = 0,
        senior_count: int = 0,
    ) -> FareBreakdown:
        """
        Calculate fare using RouteStop ORM objects.
        Looks up distance between stops from route stop data.
        """
        stop_map = {s.stop_name: s for s in route_stops}

        if boarding_stop_name not in stop_map:
            raise ValueError(f"Boarding stop '{boarding_stop_name}' not found on route")
        if destination_stop_name not in stop_map:
            raise ValueError(f"Destination stop '{destination_stop_name}' not found on route")

        boarding = stop_map[boarding_stop_name]
        destination = stop_map[destination_stop_name]

        if boarding.stop_order >= destination.stop_order:
            raise ValueError("Destination must come after boarding stop on route")

        distance_km = (
            destination.distance_from_origin_km
            - boarding.distance_from_origin_km
        )

        return self.calculate(
            distance_km=distance_km,
            boarding_stop=boarding_stop_name,
            destination_stop=destination_stop_name,
            adult_count=adult_count,
            child_count=child_count,
            senior_count=senior_count,
        )


# ── Singleton ─────────────────────────────────────────────────────────────────
fare_engine = FareEngine()