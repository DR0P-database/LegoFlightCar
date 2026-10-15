from lego_flight_car import LegoVehicle

from .base import ROAD_MODE, VehicleTestCase


class ConstructorTests(VehicleTestCase):
    def test_m_01_initial_state(self) -> None:
        """M-01: новый транспорт должен находиться в исходном режиме road."""
        vehicle = LegoVehicle(payload_kg=0, fuel_l=20)

        self.assertEqual(
            vehicle.get_status(),
            {
                "payload_kg": 0.0,
                "fuel_l": 20.0,
                "current_mode": ROAD_MODE,
                "target_mode": ROAD_MODE,
                "rotors_deployed": False,
                "wings_deployed": False,
                "is_ground": True,
                "is_airborne": False,
                "speed_kmh": 0.0,
                "last_transition_path": (),
                "last_transition_steps": (),
            },
        )

    def test_m_02_constructor_accepts_boundaries(self) -> None:
        """M-02: конструктор должен принимать обе границы параметров."""
        for payload_kg, fuel_l in ((0, 0), (200, 60)):
            with self.subTest(msg=f"payload_kg={payload_kg}, fuel_l={fuel_l}"):
                vehicle = LegoVehicle(payload_kg, fuel_l)
                self.assertAlmostEqual(vehicle.payload_kg, payload_kg)
                self.assertAlmostEqual(vehicle.fuel_l, fuel_l)

    def test_m_03_constructor_rejects_invalid_values(self) -> None:
        """M-03: конструктор должен отклонять типы и значения вне диапазона."""
        cases = (
            (-0.1, 20, ValueError, "payload_kg вне допустимого диапазона"),
            (200.1, 20, ValueError, "payload_kg вне допустимого диапазона"),
            (0, -0.1, ValueError, "fuel_l вне допустимого диапазона"),
            (0, 60.1, ValueError, "fuel_l вне допустимого диапазона"),
            ("много", 20, TypeError, "параметр payload_kg должен иметь тип float"),
            (True, 20, TypeError, "параметр payload_kg должен иметь тип float"),
            (0, "много", TypeError, "параметр fuel_l должен иметь тип float"),
            (0, False, TypeError, "параметр fuel_l должен иметь тип float"),
        )

        for payload_kg, fuel_l, error, message in cases:
            case_message = (
                f"{message}: payload_kg={payload_kg!r}, fuel_l={fuel_l!r}"
            )
            with self.subTest(msg=case_message):
                with self.assertRaisesRegex(error, message):
                    LegoVehicle(payload_kg, fuel_l)  # type: ignore[arg-type]
