from lego_flight_car import (
    CrazyVehicleError,
    InvalidState,
    LegoVehicle,
    LegoVehicleError,
    NotEnoughFuel,
)

from .base import (
    FLIGHT_INVARIANT_CASES,
    FLIGHT_MODE,
    FORWARD_DIRECTION,
    HOVER_MODE,
    ROAD_MODE,
    UNAVAILABLE_DIRECTION,
    VehicleTestCase,
)


class MovementTests(VehicleTestCase):
    def test_m_13_road_movement_uses_load_factor(self) -> None:
        """M-13: движение по дороге должно учитывать коэффициент нагрузки."""
        vehicle = LegoVehicle(100, 20)

        vehicle.move(FORWARD_DIRECTION, 10, 0.5)

        self.assertAlmostEqual(vehicle.fuel_l, 19.375)
        self.assertMode(vehicle, ROAD_MODE)

    def test_m_14_flight_movement_consumes_flight_fuel(self) -> None:
        """M-14: полёт должен расходовать топливо по тарифу flight."""
        vehicle = LegoVehicle(0, 22)
        self.setSpeed(vehicle, vehicle.MIN_FLIGHT_SPEED_KMH)
        self.switch_to(vehicle, FLIGHT_MODE)

        vehicle.move(FORWARD_DIRECTION, 10, 1.0)

        self.assertAlmostEqual(vehicle.fuel_l, 17.0)
        self.assertMode(vehicle, FLIGHT_MODE)

    def test_m_15_hover_can_leave_exact_emergency_reserve(self) -> None:
        """M-15: зависание разрешено до точной границы аварийного резерва."""
        vehicle = LegoVehicle(0, 10)
        self.switch_to(vehicle, HOVER_MODE)

        vehicle.hover(10, 1.0)

        self.assertAlmostEqual(vehicle.fuel_l, vehicle.MIN_FUEL_L)
        self.assertMode(vehicle, HOVER_MODE)

    def test_m_15_flight_can_leave_exact_emergency_reserve(self) -> None:
        """M-15: полёт разрешён до точной границы аварийного резерва."""
        vehicle = LegoVehicle(0, 9)
        self.setSpeed(vehicle, vehicle.MIN_FLIGHT_SPEED_KMH)
        self.switch_to(vehicle, FLIGHT_MODE)

        vehicle.move(FORWARD_DIRECTION, 10, 1.0)

        self.assertAlmostEqual(vehicle.fuel_l, vehicle.MIN_FUEL_L)
        self.assertMode(vehicle, FLIGHT_MODE)

    def test_m_16_move_rejects_all_invalid_calls_atomically(self) -> None:
        """M-16: move должен валидировать аргументы, состояние и запас топлива."""
        argument_cases = (
            ((1, 10, 0.5), TypeError, "параметр direction имеет недопустимый тип"),
            (
                (FORWARD_DIRECTION, "много", 0.5),
                ValueError,
                "could not convert string to float: 'много'",
            ),
            (
                (FORWARD_DIRECTION, 10, "много"),
                ValueError,
                "could not convert string to float: 'много'",
            ),
            (
                (UNAVAILABLE_DIRECTION, 10, 0.5),
                ValueError,
                "направление up недоступно в режиме road",
            ),
            (
                (FORWARD_DIRECTION, 0, 0.5),
                ValueError,
                "duration_min должен быть положительным",
            ),
            (
                (FORWARD_DIRECTION, -1, 0.5),
                ValueError,
                "duration_min должен быть положительным",
            ),
            (
                (FORWARD_DIRECTION, 10, 0),
                ValueError,
                "power_usage должен быть в диапазоне (0, 1]",
            ),
            (
                (FORWARD_DIRECTION, 10, 1.1),
                ValueError,
                "power_usage должен быть в диапазоне (0, 1]",
            ),
        )

        for args, error, message in argument_cases:
            with self.subTest(msg=f"{message}: args={args!r}"):
                vehicle = LegoVehicle(0, 20)
                self.assert_raises_unchanged(
                    vehicle,
                    error,
                    message,
                    lambda args=args: vehicle.move(*args),  # type: ignore[arg-type]
                )

        with self.subTest(msg="незавершённый переход"):
            vehicle = LegoVehicle(0, 20)
            vehicle.change_mode(HOVER_MODE)
            error = self.assert_raises_unchanged(
                vehicle,
                InvalidState,
                "транспорт находится в процессе перехода",
                lambda: vehicle.move(FORWARD_DIRECTION, 1, 0.5),
            )
            self.assertIsInstance(error, LegoVehicleError)
            self.assertIsInstance(error, CrazyVehicleError)

        with self.subTest(msg="нарушенный инвариант"):
            vehicle = LegoVehicle(0, 20)
            self.force_state(vehicle, is_ground=False, is_airborne=True)
            self.assert_raises_unchanged(
                vehicle,
                InvalidState,
                "нарушен инвариант режима",
                lambda: vehicle.move(FORWARD_DIRECTION, 1, 0.5),
            )

        for case_name, broken_state, error, message in FLIGHT_INVARIANT_CASES:
            with self.subTest(msg=f"аварийный маршрут: {case_name}"):
                vehicle = LegoVehicle(0, 7)
                self.forceFlightState(vehicle, **broken_state)
                raised = self.assert_raises_unchanged(
                    vehicle,
                    error,
                    message,
                    lambda: vehicle.move(FORWARD_DIRECTION, 11, 1.0),
                )
                self.assertIsInstance(raised, InvalidState)
                self.assertIsInstance(raised, LegoVehicleError)
                self.assertIsInstance(raised, CrazyVehicleError)

        with self.subTest(msg="недостаточно топлива"):
            vehicle = LegoVehicle(0, 0)
            error = self.assert_raises_unchanged(
                vehicle,
                NotEnoughFuel,
                "недостаточно топлива",
                lambda: vehicle.move(FORWARD_DIRECTION, 1, 1.0),
            )
            self.assertIsInstance(error, LegoVehicleError)
            self.assertIsInstance(error, CrazyVehicleError)

    def test_m_17_hover_rejects_all_invalid_calls_atomically(self) -> None:
        """M-17: hover должен валидировать аргументы и устойчивость режима."""
        argument_cases = (
            (("много", 0.5), ValueError, "could not convert string to float: 'много'"),
            (
                (10, "много"),
                ValueError,
                "could not convert string to float: 'много'",
            ),
            ((0, 0.5), ValueError, "duration_min должен быть положительным"),
            (
                (10, 0),
                ValueError,
                "power_usage должен быть в диапазоне (0, 1]",
            ),
            (
                (10, 1.1),
                ValueError,
                "power_usage должен быть в диапазоне (0, 1]",
            ),
        )

        for args, error, message in argument_cases:
            with self.subTest(msg=f"{message}: args={args!r}"):
                vehicle = self.make_vehicle_in_mode(HOVER_MODE)
                self.assert_raises_unchanged(
                    vehicle,
                    error,
                    message,
                    lambda args=args: vehicle.hover(*args),  # type: ignore[arg-type]
                )

        with self.subTest(msg="неверный режим"):
            vehicle = LegoVehicle(0, 20)
            self.assert_raises_unchanged(
                vehicle,
                InvalidState,
                "транспорт не находится в устойчивом режиме hover",
                lambda: vehicle.hover(1, 0.5),
            )

        with self.subTest(msg="незавершённый переход"):
            vehicle = self.make_vehicle_in_mode(HOVER_MODE)
            vehicle.change_mode(FLIGHT_MODE)
            self.assert_raises_unchanged(
                vehicle,
                InvalidState,
                "транспорт не находится в устойчивом режиме hover",
                lambda: vehicle.hover(1, 0.5),
            )

        with self.subTest(msg="нарушенный инвариант"):
            vehicle = LegoVehicle(0, 20)
            self.force_state(
                vehicle,
                current_mode=HOVER_MODE,
                target_mode=HOVER_MODE,
                rotors_deployed=False,
                wings_deployed=False,
                is_ground=False,
                is_airborne=True,
                speed_kmh=0.0,
            )
            self.assert_raises_unchanged(
                vehicle,
                InvalidState,
                "нарушен инвариант режима",
                lambda: vehicle.hover(1, 0.5),
            )

    def test_move_converts_numeric_strings(self) -> None:
        """Движение должно принимать числовые строки."""
        vehicle = LegoVehicle(100, 20)
        vehicle.move(FORWARD_DIRECTION, "10", "0.5")  # type: ignore[arg-type]
        self.assertAlmostEqual(vehicle.fuel_l, 19.375)
        self.assertMode(vehicle, ROAD_MODE)

    def test_hover_converts_numeric_strings(self) -> None:
        """Зависание должно принимать числовые строки."""
        vehicle = LegoVehicle(0, 10)
        self.switch_to(vehicle, HOVER_MODE)
        vehicle.hover("10", "1.0")  # type: ignore[arg-type]
        self.assertAlmostEqual(vehicle.fuel_l, vehicle.MIN_FUEL_L)
        self.assertMode(vehicle, HOVER_MODE)
