class CrazyVehicleError(Exception):
    pass


class LegoVehicleError(CrazyVehicleError):
    pass


class InvalidState(LegoVehicleError):
    pass


class NotAirborne(InvalidState):
    pass


class InsufficientFlightSpeed(InvalidState):
    pass


class NotEnoughFuel(LegoVehicleError):
    pass
