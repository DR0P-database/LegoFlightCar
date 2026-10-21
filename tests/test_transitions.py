from lego_flight_car import (
    CrazyVehicleError,
    InsufficientFlightSpeed,
    InvalidState,
    LegoVehicle,
    LegoVehicleError,
    NotEnoughFuel,
)

from .base import (
    FLIGHT_INVARIANT_CASES,
    FLIGHT_MODE,
    HOVER_MODE,
    INSUFFICIENT_FLIGHT_SPEED_MESSAGE,
    ROAD_MODE,
    TRANSITION_STEPS,
    VehicleTestCase,
)


class TransitionTests(VehicleTestCase):
    def test_m_09_all_six_direct_transitions(self) -> None:
        """M-09: каждое ребро автомата должно иметь точные итог и журнал шагов."""
        for source, target in TRANSITION_STEPS:
            with self.subTest(msg=f"{source} -> {target}"):
                vehicle = self.make_vehicle_in_mode(source)
                fuel_before = vehicle.fuel_l

                if target == FLIGHT_MODE:
                    self.setSpeed(vehicle, vehicle.MIN_FLIGHT_SPEED_KMH)
                self.switch_to(vehicle, target)

                self.assertMode(vehicle, target)
                self.assertAlmostEqual(
                    vehicle.fuel_l,
                    fuel_before - vehicle.TRANSITION_FUEL_L,
                )
                self.assertEqual(vehicle.last_transition_path, (source, target))
                self.assertEqual(
                    vehicle.last_transition_steps,
                    TRANSITION_STEPS[(source, target)],
                )

    def test_m_10a_transition_without_request_is_noop(self) -> None:
        """M-10a: transition без новой цели не должен изменять объект."""
        vehicle = LegoVehicle(0, 20)
        before = vehicle.get_status()

        vehicle.transition()

        self.assertEqual(vehicle.get_status(), before)

    def test_m_10b_explicit_request_of_current_mode_is_noop(self) -> None:
        """M-10b: явный запрос текущего режима должен быть полным no-op."""
        vehicle = self.make_vehicle_in_mode(HOVER_MODE)
        self.switch_to(vehicle, ROAD_MODE)
        self.assertEqual(
            vehicle.last_transition_path,
            (HOVER_MODE, ROAD_MODE),
        )
        before = vehicle.get_status()

        vehicle.change_mode(ROAD_MODE)
        vehicle.transition()

        self.assertEqual(vehicle.get_status(), before)

    def test_m_11_takeoff_can_leave_exact_emergency_reserve(self) -> None:
        """M-11: взлёт разрешён, если после него остаётся ровно аварийный резерв."""
        vehicle = LegoVehicle(0, 6.0)

        self.setSpeed(vehicle, vehicle.MIN_FLIGHT_SPEED_KMH)
        self.switch_to(vehicle, FLIGHT_MODE)

        self.assertMode(vehicle, FLIGHT_MODE)
        self.assertAlmostEqual(vehicle.fuel_l, vehicle.MIN_FUEL_L)

    def test_m_12_transition_errors_are_atomic(self) -> None:
        """M-12: ошибки топлива и инварианта не должны частично менять состояние."""
        with self.subTest(msg="недостаточно резерва для взлёта"):
            vehicle = LegoVehicle(0, 5.99)
            self.setSpeed(vehicle, vehicle.MIN_FLIGHT_SPEED_KMH)
            vehicle.change_mode(FLIGHT_MODE)
            error = self.assert_raises_unchanged(
                vehicle,
                NotEnoughFuel,
                "недостаточно топлива для сохранения аварийного резерва",
                vehicle.transition,
            )
            self.assertIsInstance(error, LegoVehicleError)
            self.assertIsInstance(error, CrazyVehicleError)

        with self.subTest(msg="нет скорости для перехода в flight"):
            vehicle = LegoVehicle(0, 20)
            vehicle.change_mode(FLIGHT_MODE)
            error = self.assert_raises_unchanged(
                vehicle,
                InsufficientFlightSpeed,
                INSUFFICIENT_FLIGHT_SPEED_MESSAGE,
                vehicle.transition,
            )
            self.assertIsInstance(error, InvalidState)
            self.assertIsInstance(error, LegoVehicleError)
            self.assertIsInstance(error, CrazyVehicleError)

        with self.subTest(msg="недостаточно топлива для посадки"):
            vehicle = LegoVehicle(0, 20)
            self.force_state(
                vehicle,
                fuel_l=1.99,
                current_mode=HOVER_MODE,
                target_mode=HOVER_MODE,
                rotors_deployed=True,
                wings_deployed=False,
                is_ground=False,
                is_airborne=True,
                speed_kmh=0.0,
            )
            vehicle.change_mode(ROAD_MODE)
            self.assert_raises_unchanged(
                vehicle,
                NotEnoughFuel,
                "недостаточно топлива для посадки",
                vehicle.transition,
            )

        for case_name, broken_state, error, message in FLIGHT_INVARIANT_CASES:
            with self.subTest(msg=case_name):
                vehicle = LegoVehicle(0, 20)
                self.forceFlightState(vehicle, **broken_state)
                vehicle.change_mode(HOVER_MODE)
                raised = self.assert_raises_unchanged(
                    vehicle,
                    error,
                    message,
                    vehicle.transition,
                )
                self.assertIsInstance(raised, InvalidState)
                self.assertIsInstance(raised, LegoVehicleError)
                self.assertIsInstance(raised, CrazyVehicleError)
