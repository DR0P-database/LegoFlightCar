from lego_flight_car import LegoVehicle

from .base import FLIGHT_MODE, HOVER_MODE, VehicleTestCase


class InvariantTests(VehicleTestCase):
    def test_m_06_road_invariant(self) -> None:
        """M-06: режим road должен однозначно соответствовать наземному состоянию."""
        vehicle = LegoVehicle(0, 20)

        self.assertRoadMode(vehicle)

    def test_m_07_hover_invariant(self) -> None:
        """M-07: режим hover должен удерживать транспорт в воздухе на роторах."""
        vehicle = LegoVehicle(0, 20)
        self.switch_to(vehicle, HOVER_MODE)

        self.assertHoverMode(vehicle)

    def test_m_08_flight_invariant(self) -> None:
        """M-08: режим flight должен означать полёт на крыльях с нужной скоростью."""
        vehicle = LegoVehicle(0, 20)
        self.setSpeed(vehicle, vehicle.MIN_FLIGHT_SPEED_KMH)
        self.switch_to(vehicle, FLIGHT_MODE)

        self.assertFlightMode(vehicle)
