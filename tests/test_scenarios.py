from lego_flight_car import LegoVehicle

from .base import (
    DECELERATE_TO_ZERO_STEP,
    DEPLOY_ROTORS_STEP,
    EMERGENCY_FLIGHT_PATH,
    EMERGENCY_FLIGHT_STEPS,
    FLIGHT_MODE,
    FLIGHT_TO_HOVER,
    FLIGHT_TO_ROAD,
    FORWARD_DIRECTION,
    HOVER_MODE,
    HOVER_TO_FLIGHT,
    HOVER_TO_ROAD,
    RETRACT_ROTORS_STEP,
    ROAD_MODE,
    ROAD_TO_FLIGHT,
    TRANSITION_STEPS,
    TRANSFER_LIFT_TO_WINGS_STEP,
    VehicleTestCase,
)


class ScenarioTests(VehicleTestCase):
    def test_s_01_airplane_takeoff_and_direct_landing(self) -> None:
        """S-01: проверяет полный сценарий самолётного взлёта и посадки."""
        vehicle = LegoVehicle(0, 20)

        self.setSpeed(vehicle, vehicle.MIN_FLIGHT_SPEED_KMH)
        self.switch_to(vehicle, FLIGHT_MODE)
        self.assertMode(vehicle, FLIGHT_MODE)
        self.assertEqual(vehicle.last_transition_path, ROAD_TO_FLIGHT)

        self.switch_to(vehicle, ROAD_MODE)
        self.assertMode(vehicle, ROAD_MODE)
        self.assertEqual(vehicle.last_transition_path, FLIGHT_TO_ROAD)
        self.assertAlmostEqual(vehicle.fuel_l, 16.0)

    def test_s_02_vertical_takeoff_then_forward_flight(self) -> None:
        """S-02: проверяет вертикальный взлёт и передачу нагрузки крыльям."""
        vehicle = LegoVehicle(0, 30)

        self.switch_to(vehicle, HOVER_MODE)
        self.assertMode(vehicle, HOVER_MODE)

        self.setSpeed(vehicle, vehicle.MIN_FLIGHT_SPEED_KMH)
        self.switch_to(vehicle, FLIGHT_MODE)
        self.assertMode(vehicle, FLIGHT_MODE)
        self.assertEqual(
            vehicle.last_transition_steps,
            TRANSITION_STEPS[HOVER_TO_FLIGHT],
        )
        self.assertLess(
            vehicle.last_transition_steps.index(TRANSFER_LIFT_TO_WINGS_STEP),
            vehicle.last_transition_steps.index(RETRACT_ROTORS_STEP),
        )
        self.assertAlmostEqual(vehicle.fuel_l, 26.0)

    def test_s_03_flight_to_hover_preserves_support_order(self) -> None:
        """S-03: роторы должны принять нагрузку до снижения полётной скорости."""
        vehicle = LegoVehicle(0, 20)
        self.setSpeed(vehicle, vehicle.MIN_FLIGHT_SPEED_KMH)
        self.switch_to(vehicle, FLIGHT_MODE)
        self.assertIs(vehicle.is_airborne, True)
        self.assertGreaterEqual(
            vehicle.speed_kmh,
            vehicle.MIN_FLIGHT_SPEED_KMH,
        )

        self.switch_to(vehicle, HOVER_MODE)

        self.assertMode(vehicle, HOVER_MODE)
        self.assertEqual(vehicle.last_transition_path, FLIGHT_TO_HOVER)
        self.assertEqual(
            vehicle.last_transition_steps,
            TRANSITION_STEPS[FLIGHT_TO_HOVER],
        )
        self.assertLess(
            vehicle.last_transition_steps.index(DEPLOY_ROTORS_STEP),
            vehicle.last_transition_steps.index(DECELERATE_TO_ZERO_STEP),
        )

    def test_s_04_hover_emergency_landing(self) -> None:
        """S-04: нарушение резерва в hover должно запустить автопосадку."""
        vehicle = LegoVehicle(0, 9)
        self.switch_to(vehicle, HOVER_MODE)

        vehicle.hover(10, 1.0)

        self.assertMode(vehicle, ROAD_MODE)
        self.assertEqual(vehicle.last_transition_path, HOVER_TO_ROAD)
        self.assertAlmostEqual(vehicle.fuel_l, 5.0)

    def test_s_05_flight_emergency_landing_uses_hover(self) -> None:
        """S-05: аварийный маршрут из flight должен обязательно пройти через hover."""
        vehicle = LegoVehicle(0, 9)
        self.setSpeed(vehicle, vehicle.MIN_FLIGHT_SPEED_KMH)
        self.switch_to(vehicle, FLIGHT_MODE)
        self.assertIs(vehicle.is_airborne, True)
        self.assertGreaterEqual(
            vehicle.speed_kmh,
            vehicle.MIN_FLIGHT_SPEED_KMH,
        )

        vehicle.move(FORWARD_DIRECTION, 11, 1.0)

        self.assertMode(vehicle, ROAD_MODE)
        self.assertEqual(
            vehicle.last_transition_path,
            EMERGENCY_FLIGHT_PATH,
        )
        self.assertEqual(vehicle.last_transition_steps, EMERGENCY_FLIGHT_STEPS)
        self.assertAlmostEqual(vehicle.fuel_l, 3.0)
