from lego_flight_car import LegoVehicle

from .base import FLIGHT_MODE, HOVER_MODE, ROAD_MODE, VehicleTestCase


class ModeSelectionTests(VehicleTestCase):
    def test_m_04_target_can_be_selected_replaced_and_cancelled(self) -> None:
        """M-04: цель можно выбрать, заменить и отменить без физического перехода."""
        vehicle = LegoVehicle(0, 20)
        initial = vehicle.get_status()
        cases = (
            ("выбор режима зависания", HOVER_MODE),
            ("замена цели на полёт", FLIGHT_MODE),
            ("отмена перехода", ROAD_MODE),
        )

        for case_name, target in cases:
            with self.subTest(msg=case_name):
                vehicle.change_mode(target)
                self.assertEqual(vehicle.target_mode, target)
                self.assertEqual(vehicle.current_mode, ROAD_MODE)
                self.assertAlmostEqual(vehicle.speed_kmh, 0.0)
                expected_status = {**initial, "target_mode": target}
                self.assertEqual(vehicle.get_status(), expected_status)

    def test_m_05_change_mode_rejects_invalid_target(self) -> None:
        """M-05: change_mode должен отклонять неверный тип и неизвестный режим."""
        cases = (
            (1, TypeError, "target_mode должен быть строкой"),
            ("submarine", ValueError, "неизвестный режим: submarine"),
        )

        for target, error, message in cases:
            with self.subTest(msg=message):
                vehicle = LegoVehicle(0, 20)
                self.assert_raises_unchanged(
                    vehicle,
                    error,
                    message,
                    lambda: vehicle.change_mode(target),  # type: ignore[arg-type]
                )
