from typing import Any


class LegoVehicle:
    MAX_PAYLOAD_KG = 200.0
    FUEL_TANK_CAPACITY_L = 60.0
    MIN_FUEL_L = 4.0
    TRANSITION_FUEL_L = 2.0
    MIN_FLIGHT_SPEED_KMH = 80.0

    ROAD_FUEL_RATE_L_PER_MIN = 0.10
    HOVER_FUEL_RATE_L_PER_MIN = 0.40
    FLIGHT_FUEL_RATE_L_PER_MIN = 0.30

    def __init__(self, payload_kg: float, fuel_l: float) -> None:
        raise NotImplementedError

    @property
    def payload_kg(self) -> float:
        raise NotImplementedError

    @property
    def fuel_l(self) -> float:
        raise NotImplementedError

    @property
    def current_mode(self) -> str:
        raise NotImplementedError

    @property
    def target_mode(self) -> str:
        raise NotImplementedError

    @property
    def rotors_deployed(self) -> bool:
        raise NotImplementedError

    @property
    def wings_deployed(self) -> bool:
        raise NotImplementedError

    @property
    def is_ground(self) -> bool:
        raise NotImplementedError

    @property
    def is_airborne(self) -> bool:
        raise NotImplementedError

    @property
    def speed_kmh(self) -> float:
        raise NotImplementedError

    @property
    def last_transition_path(self) -> tuple[str, ...]:
        raise NotImplementedError

    @property
    def last_transition_steps(self) -> tuple[str, ...]:
        raise NotImplementedError

    def change_mode(self, target_mode: str) -> None:
        raise NotImplementedError

    def transition(self) -> None:
        raise NotImplementedError

    def move(
        self,
        duration_min: float,
        power_usage: float,
    ) -> None:
        raise NotImplementedError

    def hover(self, duration_min: float, power_usage: float) -> None:
        raise NotImplementedError

    def get_status(self) -> dict[str, Any]:
        raise NotImplementedError
