"""Дискретная модель LegoFlightCar по SPEC.md."""

from math import isfinite
from typing import Any

from .errors import (
    InsufficientFlightSpeed,
    InvalidState,
    NotAirborne,
    NotEnoughFuel,
)


class LegoVehicle:
    """Транспорт с атомарными переходами и состоянием только для чтения."""

    MAX_PAYLOAD_KG = 200.0
    FUEL_TANK_CAPACITY_L = 60.0
    MIN_FUEL_L = 4.0
    TRANSITION_FUEL_L = 2.0
    MIN_FLIGHT_SPEED_KMH = 80.0

    ROAD_FUEL_RATE_L_PER_MIN = 0.10
    HOVER_FUEL_RATE_L_PER_MIN = 0.40
    FLIGHT_FUEL_RATE_L_PER_MIN = 0.30

    # Роторы, крылья, положение на земле для каждого устойчивого режима.
    _CONFIGURATIONS = {
        "road": (False, False, True),
        "hover": (True, False, False),
        "flight": (False, True, False),
    }
    _TRANSITION_STEPS = {
        ("road", "hover"): ("deploy_rotors", "vertical_takeoff"),
        ("road", "flight"): (
            "deploy_wings", "accelerate_on_ground", "takeoff",
        ),
        ("hover", "road"): (
            "vertical_descent", "touchdown", "retract_rotors",
        ),
        ("hover", "flight"): (
            "deploy_wings", "accelerate_with_rotor_support",
            "transfer_lift_to_wings", "retract_rotors",
        ),
        ("flight", "hover"): (
            "deploy_rotors", "transfer_lift_to_rotors",
            "decelerate_to_zero", "retract_wings",
        ),
        ("flight", "road"): (
            "approach_on_wings", "touchdown", "decelerate_to_zero",
            "retract_wings",
        ),
    }

    def __init__(self, payload_kg: float, fuel_l: float) -> None:
        """Проверяет нагрузку и топливо, создаёт устойчивый road."""
        payload = self._to_float(payload_kg, "payload_kg")
        fuel = self._to_float(fuel_l, "fuel_l")
        if not 0 <= payload <= self.MAX_PAYLOAD_KG:
            raise ValueError("payload_kg вне допустимого диапазона")
        if not 0 <= fuel <= self.FUEL_TANK_CAPACITY_L:
            raise ValueError("fuel_l вне допустимого диапазона")

        self._payload_kg = payload
        self._fuel_l = fuel
        self._current_mode = self._target_mode = "road"
        self._rotors_deployed = self._wings_deployed = False
        self._is_ground = True
        self._is_airborne = False
        self._speed_kmh = 0.0
        self._last_transition_path: tuple[str, ...] = ()
        self._last_transition_steps: tuple[str, ...] = ()

    @property
    def payload_kg(self) -> float:
        """Полезная нагрузка в килограммах."""
        return self._payload_kg

    @property
    def fuel_l(self) -> float:
        """Остаток топлива в литрах."""
        return self._fuel_l

    @property
    def current_mode(self) -> str:
        """Последний достигнутый режим."""
        return self._current_mode

    @property
    def target_mode(self) -> str:
        """Запрошенный режим."""
        return self._target_mode

    @property
    def rotors_deployed(self) -> bool:
        """Раскрыты ли роторы."""
        return self._rotors_deployed

    @property
    def wings_deployed(self) -> bool:
        """Раскрыты ли крылья."""
        return self._wings_deployed

    @property
    def is_ground(self) -> bool:
        """Находится ли транспорт на земле."""
        return self._is_ground

    @property
    def is_airborne(self) -> bool:
        """Находится ли транспорт в воздухе."""
        return self._is_airborne

    @property
    def speed_kmh(self) -> float:
        """Скорость, подготовленная внутренним или внешним расчётом."""
        return self._speed_kmh

    @property
    def last_transition_path(self) -> tuple[str, ...]:
        """Маршрут последнего успешного перехода."""
        return self._last_transition_path

    @property
    def last_transition_steps(self) -> tuple[str, ...]:
        """Физические шаги последнего успешного перехода."""
        return self._last_transition_steps

    def change_mode(self, target_mode: str) -> None:
        """Выбирает, заменяет или отменяет цель без смены конфигурации."""
        if not isinstance(target_mode, str):
            raise TypeError("target_mode должен быть строкой")
        if target_mode not in self._CONFIGURATIONS:
            raise ValueError(f"неизвестный режим: {target_mode}")
        self._target_mode = target_mode

    def transition(self) -> None:
        """Выполняет прямой переход; при ошибке сохраняет весь снимок."""
        if self._current_mode == self._target_mode:
            return
        self._validate_state(target_flight=self._target_mode == "flight")

        fuel_after = self._fuel_l - self.TRANSITION_FUEL_L
        if self._target_mode == "road":
            if fuel_after < 0:
                raise NotEnoughFuel("недостаточно топлива для посадки")
        elif fuel_after < self.MIN_FUEL_L:
            raise NotEnoughFuel(
                "недостаточно топлива для сохранения аварийного резерва"
            )
        self._complete_transition(
            (self._current_mode, self._target_mode), fuel_after,
        )

    def move(
        self,
        duration_min: float,
        power_usage: float,
    ) -> None:
        """Расходует топливо в текущем режиме или аварийно сажает транспорт."""
        duration, power = self._operation_arguments(duration_min, power_usage)
        if self._current_mode != self._target_mode:
            raise InvalidState("транспорт находится в процессе перехода")
        self._validate_state()
        self._consume_fuel(duration, power)

    def hover(self, duration_min: float, power_usage: float) -> None:
        """Выполняет зависание только в устойчивом hover."""
        duration, power = self._operation_arguments(duration_min, power_usage)
        if self._current_mode != "hover" or self._target_mode != "hover":
            raise InvalidState(
                "транспорт не находится в устойчивом режиме hover"
            )
        self._validate_state()
        self._consume_fuel(duration, power)

    def get_status(self) -> dict[str, Any]:
        """Возвращает независимый снимок, включая неизменяемые журналы."""
        return {
            "payload_kg": self._payload_kg,
            "fuel_l": self._fuel_l,
            "current_mode": self._current_mode,
            "target_mode": self._target_mode,
            "rotors_deployed": self._rotors_deployed,
            "wings_deployed": self._wings_deployed,
            "is_ground": self._is_ground,
            "is_airborne": self._is_airborne,
            "speed_kmh": self._speed_kmh,
            "last_transition_path": self._last_transition_path,
            "last_transition_steps": self._last_transition_steps,
        }

    @staticmethod
    def _to_float(value: Any, name: str) -> float:
        """Приводит аргумент к float, запрещая bool согласно SPEC 6.2."""
        if isinstance(value, bool):
            raise ValueError(f"параметр {name} не должен иметь тип bool")
        try:
            return float(value)
        except (TypeError, OverflowError) as error:
            raise ValueError(str(error)) from error

    @classmethod
    def _operation_arguments(
        cls, duration_min: float, power_usage: float,
    ) -> tuple[float, float]:
        """Сначала преобразует оба аргумента, затем проверяет диапазоны."""
        duration = cls._to_float(duration_min, "duration_min")
        power = cls._to_float(power_usage, "power_usage")
        # Политика для NaN и бесконечности зафиксирована в BUGREPORT BR-02.
        if not isfinite(duration) or not duration > 0:
            raise ValueError("duration_min должен быть положительным")
        if not 0 < power <= 1:
            raise ValueError("power_usage должен быть в диапазоне (0, 1]")
        return duration, power

    def _validate_state(self, *, target_flight: bool = False) -> None:
        """Проверяет предусловия flight до остальных инвариантов."""
        if self._current_mode == "flight":
            if not self._is_airborne:
                raise NotAirborne("режим flight требует нахождения в воздухе")
        if self._current_mode == "flight" or target_flight:
            if self._speed_kmh < self.MIN_FLIGHT_SPEED_KMH:
                raise InsufficientFlightSpeed(
                    "скорость ниже минимальной для режима flight"
                )

        configuration = self._CONFIGURATIONS.get(self._current_mode)
        valid = (
            configuration is not None
            and self._target_mode in self._CONFIGURATIONS
            and isfinite(self._speed_kmh)
            and self._speed_kmh >= 0
            and 0 <= self._payload_kg <= self.MAX_PAYLOAD_KG
            and 0 <= self._fuel_l <= self.FUEL_TANK_CAPACITY_L
        )
        if valid:
            rotors, wings, ground = configuration
            valid = (
                self._rotors_deployed is rotors
                and self._wings_deployed is wings
                and self._is_ground is ground
                and self._is_airborne is (not ground)
            )
            # Подготовленная скорость разрешена для ребра, ведущего в flight.
            if self._current_mode != "flight" and not target_flight:
                valid = valid and self._speed_kmh == 0
        if not valid:
            raise InvalidState("нарушен инвариант режима")

    def _complete_transition(
        self, path: tuple[str, ...], fuel_after: float,
    ) -> None:
        """Подготавливает итог маршрута до записи любого поля состояния."""
        steps = tuple(
            step
            for source, target in zip(path, path[1:])
            for step in self._TRANSITION_STEPS[(source, target)]
        )
        mode = path[-1]
        rotors, wings, ground = self._CONFIGURATIONS[mode]
        speed = self._speed_kmh if mode == "flight" else 0.0

        self._fuel_l = fuel_after
        self._current_mode = self._target_mode = mode
        self._rotors_deployed = rotors
        self._wings_deployed = wings
        self._is_ground = ground
        self._is_airborne = not ground
        self._speed_kmh = speed
        self._last_transition_path = path
        self._last_transition_steps = steps

    def _consume_fuel(self, duration: float, power: float) -> None:
        """Списывает расход либо целиком выполняет аварийный маршрут."""
        rate = {
            "road": self.ROAD_FUEL_RATE_L_PER_MIN,
            "hover": self.HOVER_FUEL_RATE_L_PER_MIN,
            "flight": self.FLIGHT_FUEL_RATE_L_PER_MIN,
        }[self._current_mode]
        load_factor = 1 + 0.5 * self._payload_kg / self.MAX_PAYLOAD_KG
        fuel_required = rate * duration * power * load_factor
        fuel_after = self._fuel_l - fuel_required
        if self._current_mode == "road":
            if fuel_after < 0:
                raise NotEnoughFuel("недостаточно топлива")
        elif fuel_after < self.MIN_FUEL_L:
            path = (
                ("flight", "hover", "road")
                if self._current_mode == "flight" else ("hover", "road")
            )
            landing_fuel = (len(path) - 1) * self.TRANSITION_FUEL_L
            if self._fuel_l < landing_fuel:
                raise NotEnoughFuel("недостаточно топлива для посадки")
            self._complete_transition(path, self._fuel_l - landing_fuel)
            return
        self._fuel_l = fuel_after
