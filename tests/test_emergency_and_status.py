from lego_flight_car import LegoVehicle

from .base import (
    EMERGENCY_FLIGHT_PATH,
    EMERGENCY_FLIGHT_STEPS,
    FLIGHT_MODE,
    FORWARD_DIRECTION,
    HOVER_MODE,
    HOVER_TO_ROAD,
    ROAD_MODE,
    ROAD_TO_FLIGHT,
    TRANSITION_STEPS,
    VehicleTestCase,
)


class EmergencyAndStatusTests(VehicleTestCase):
    def test_m_18_hover_operation_triggers_emergency_landing(self) -> None:
        """M-18: опасное зависание должно отмениться и завершиться посадкой."""
        vehicle = LegoVehicle(0, 9)
        self.switch_to(vehicle, HOVER_MODE)

        vehicle.hover(10, 1.0)

        self.assertMode(vehicle, ROAD_MODE)
        self.assertAlmostEqual(vehicle.fuel_l, 5.0)
        self.assertEqual(vehicle.last_transition_path, HOVER_TO_ROAD)
        self.assertEqual(
            vehicle.last_transition_steps,
            TRANSITION_STEPS[HOVER_TO_ROAD],
        )

    def test_m_19_flight_operation_triggers_emergency_route_via_hover(self) -> None:
        """M-19: опасный полёт должен посадить транспорт через режим hover."""
        vehicle = LegoVehicle(0, 9)
        self.setSpeed(vehicle, vehicle.MIN_FLIGHT_SPEED_KMH)
        self.switch_to(vehicle, FLIGHT_MODE)

        vehicle.move(FORWARD_DIRECTION, 11, 1.0)

        self.assertMode(vehicle, ROAD_MODE)
        self.assertAlmostEqual(vehicle.fuel_l, 3.0)
        self.assertEqual(
            vehicle.last_transition_path,
            EMERGENCY_FLIGHT_PATH,
        )
        self.assertEqual(vehicle.last_transition_steps, EMERGENCY_FLIGHT_STEPS)

    def test_m_20_status_is_independent_and_transition_log_is_observable(self) -> None:
        """M-20: снимки статуса независимы и содержат журнал перехода."""
        vehicle = LegoVehicle(0, 20)
        first = vehicle.get_status()
        second = vehicle.get_status()

        first["fuel_l"] = -1
        self.assertAlmostEqual(second["fuel_l"], 20.0)
        self.assertAlmostEqual(vehicle.fuel_l, 20.0)

        self.setSpeed(vehicle, vehicle.MIN_FLIGHT_SPEED_KMH)
        self.switch_to(vehicle, FLIGHT_MODE)
        status = vehicle.get_status()

        self.assertEqual(status["last_transition_path"], ROAD_TO_FLIGHT)
        self.assertEqual(
            status["last_transition_steps"],
            TRANSITION_STEPS[ROAD_TO_FLIGHT],
        )
