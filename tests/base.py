import re
from collections.abc import Callable
from unittest import TestCase

from lego_flight_car import InsufficientFlightSpeed, LegoVehicle, NotAirborne


ROAD_MODE = "road"
HOVER_MODE = "hover"
FLIGHT_MODE = "flight"

ROAD_TO_HOVER = (ROAD_MODE, HOVER_MODE)
ROAD_TO_FLIGHT = (ROAD_MODE, FLIGHT_MODE)
HOVER_TO_ROAD = (HOVER_MODE, ROAD_MODE)
HOVER_TO_FLIGHT = (HOVER_MODE, FLIGHT_MODE)
FLIGHT_TO_HOVER = (FLIGHT_MODE, HOVER_MODE)
FLIGHT_TO_ROAD = (FLIGHT_MODE, ROAD_MODE)
EMERGENCY_FLIGHT_PATH = (FLIGHT_MODE, HOVER_MODE, ROAD_MODE)

DEPLOY_ROTORS_STEP = "deploy_rotors"
VERTICAL_TAKEOFF_STEP = "vertical_takeoff"
DEPLOY_WINGS_STEP = "deploy_wings"
ACCELERATE_ON_GROUND_STEP = "accelerate_on_ground"
TAKEOFF_STEP = "takeoff"
VERTICAL_DESCENT_STEP = "vertical_descent"
TOUCHDOWN_STEP = "touchdown"
RETRACT_ROTORS_STEP = "retract_rotors"
ACCELERATE_WITH_ROTOR_SUPPORT_STEP = "accelerate_with_rotor_support"
TRANSFER_LIFT_TO_WINGS_STEP = "transfer_lift_to_wings"
TRANSFER_LIFT_TO_ROTORS_STEP = "transfer_lift_to_rotors"
DECELERATE_TO_ZERO_STEP = "decelerate_to_zero"
RETRACT_WINGS_STEP = "retract_wings"
APPROACH_ON_WINGS_STEP = "approach_on_wings"

NOT_AIRBORNE_MESSAGE = "режим flight требует нахождения в воздухе"
INSUFFICIENT_FLIGHT_SPEED_MESSAGE = "скорость ниже минимальной для режима flight"

FLIGHT_INVARIANT_CASES = (
    (
        "flight не находится в воздухе",
        {"is_ground": True, "is_airborne": False},
        NotAirborne,
        NOT_AIRBORNE_MESSAGE,
    ),
    (
        "flight не имеет минимальной скорости",
        {"speed_kmh": 0.0},
        InsufficientFlightSpeed,
        INSUFFICIENT_FLIGHT_SPEED_MESSAGE,
    ),
)

TRANSITION_STEPS = {
    ROAD_TO_HOVER: (DEPLOY_ROTORS_STEP, VERTICAL_TAKEOFF_STEP),
    ROAD_TO_FLIGHT: (DEPLOY_WINGS_STEP, ACCELERATE_ON_GROUND_STEP, TAKEOFF_STEP),
    HOVER_TO_ROAD: (VERTICAL_DESCENT_STEP, TOUCHDOWN_STEP, RETRACT_ROTORS_STEP),
    HOVER_TO_FLIGHT: (
        DEPLOY_WINGS_STEP,
        ACCELERATE_WITH_ROTOR_SUPPORT_STEP,
        TRANSFER_LIFT_TO_WINGS_STEP,
        RETRACT_ROTORS_STEP,
    ),
    FLIGHT_TO_HOVER: (
        DEPLOY_ROTORS_STEP,
        TRANSFER_LIFT_TO_ROTORS_STEP,
        DECELERATE_TO_ZERO_STEP,
        RETRACT_WINGS_STEP,
    ),
    FLIGHT_TO_ROAD: (
        APPROACH_ON_WINGS_STEP,
        TOUCHDOWN_STEP,
        DECELERATE_TO_ZERO_STEP,
        RETRACT_WINGS_STEP,
    ),
}

EMERGENCY_FLIGHT_STEPS = (
    *TRANSITION_STEPS[FLIGHT_TO_HOVER],
    *TRANSITION_STEPS[HOVER_TO_ROAD],
)


class VehicleTestCase(TestCase):
    """Базовый TestCase с общими действиями и проверками транспорта."""

    def switch_to(self, vehicle: LegoVehicle, mode: str) -> None:
        """Выполняет переход и проверяет полный физический инвариант режима."""
        vehicle.change_mode(mode)
        vehicle.transition()
        self.assertMode(vehicle, mode)

    def setSpeed(self, vehicle: LegoVehicle, speed_kmh: float) -> None:
        """Задаёт скорость при подготовке состояния теста."""
        self.force_state(vehicle, speed_kmh=speed_kmh)

    def make_vehicle_in_mode(
        self,
        mode: str,
        *,
        fuel_l: float = 60.0,
    ) -> LegoVehicle:
        """Подготавливает скорость и переводит транспорт в тестовый режим."""
        vehicle = LegoVehicle(0, fuel_l)
        if mode != ROAD_MODE:
            if mode == FLIGHT_MODE:
                self.setSpeed(vehicle, vehicle.MIN_FLIGHT_SPEED_KMH)
            self.switch_to(vehicle, mode)
        return vehicle

    def assertMode(self, vehicle: LegoVehicle, mode: str) -> None:
        """Вызывает отдельную проверку физического состояния режима."""
        assertions = {
            ROAD_MODE: self.assertRoadMode,
            HOVER_MODE: self.assertHoverMode,
            FLIGHT_MODE: self.assertFlightMode,
        }
        try:
            assertion = assertions[mode]
        except KeyError:
            self.fail(f"неизвестный режим в тесте: {mode}")
        assertion(vehicle)

    def assertRoadMode(self, vehicle: LegoVehicle) -> None:
        """Проверяет физическое состояние транспорта в дорожном режиме."""
        self.assertEqual(vehicle.current_mode, ROAD_MODE)
        self.assertEqual(vehicle.target_mode, ROAD_MODE)
        self.assertIs(vehicle.is_ground, not vehicle.is_airborne)
        self.assertIs(vehicle.is_ground, True)
        self.assertAlmostEqual(vehicle.speed_kmh, 0.0)
        self.assertIs(vehicle.rotors_deployed, False)
        self.assertIs(vehicle.wings_deployed, False)

    def assertHoverMode(self, vehicle: LegoVehicle) -> None:
        """Проверяет физическое состояние транспорта в режиме зависания."""
        self.assertEqual(vehicle.current_mode, HOVER_MODE)
        self.assertEqual(vehicle.target_mode, HOVER_MODE)
        self.assertIs(vehicle.is_ground, not vehicle.is_airborne)
        self.assertIs(vehicle.is_airborne, True)
        self.assertAlmostEqual(vehicle.speed_kmh, 0.0)
        self.assertIs(vehicle.rotors_deployed, True)
        self.assertIs(vehicle.wings_deployed, False)

    def assertFlightMode(self, vehicle: LegoVehicle) -> None:
        """Проверяет физическое состояние транспорта в режиме полёта."""
        self.assertEqual(vehicle.current_mode, FLIGHT_MODE)
        self.assertEqual(vehicle.target_mode, FLIGHT_MODE)
        self.assertIs(vehicle.is_ground, not vehicle.is_airborne)
        self.assertIs(vehicle.is_airborne, True)
        self.assertGreaterEqual(
            vehicle.speed_kmh,
            vehicle.MIN_FLIGHT_SPEED_KMH,
        )
        self.assertIs(vehicle.rotors_deployed, False)
        self.assertIs(vehicle.wings_deployed, True)

    def force_state(self, vehicle: LegoVehicle, **state: object) -> None:
        """Создаёт повреждённое внутреннее состояние для защитных unit-тестов."""
        for field, value in state.items():
            object.__setattr__(vehicle, f"_{field}", value)

    def forceFlightState(self, vehicle: LegoVehicle, **overrides: object) -> None:
        """Создаёт устойчивый flight и применяет переданные нарушения инварианта."""
        state: dict[str, object] = {
            "current_mode": FLIGHT_MODE,
            "target_mode": FLIGHT_MODE,
            "rotors_deployed": False,
            "wings_deployed": True,
            "is_ground": False,
            "is_airborne": True,
            "speed_kmh": vehicle.MIN_FLIGHT_SPEED_KMH,
        }
        state.update(overrides)
        self.force_state(vehicle, **state)

    def assert_raises_unchanged(
        self,
        vehicle: LegoVehicle,
        error: type[BaseException],
        message: str,
        action: Callable[[], object],
    ) -> BaseException:
        """Проверяет точную ошибку и атомарную неизменность состояния."""
        before = vehicle.get_status()
        with self.assertRaisesRegex(error, re.escape(message)) as raised:
            action()
        self.assertEqual(vehicle.get_status(), before)
        return raised.exception
