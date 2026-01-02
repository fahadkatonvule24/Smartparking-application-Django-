from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from blog.models import Client, ParkingLot, ParkingSpace, Reservation


class ReservationModelTests(TestCase):
    def setUp(self):
        self.customer = Client.objects.create(
            full_name="Test Driver",
            contact="1234567890",
            plate_number="ABC123",
            dimension=400,
            car_type="Sedan",
        )
        self.lot = ParkingLot.objects.create(lot_id=1, lot_capacity=2)
        self.space = ParkingSpace.objects.create(
            label="A1", parking_lot=self.lot, dimension_limit=500
        )

    def test_reservation_duration_cost_and_sequence_number(self):
        start = timezone.now()
        end = start + timedelta(hours=2)

        reservation = Reservation.objects.create(
            client=self.customer,
            parking_slot=self.space,
            type_of_reservation="BOX",
            start_time=start,
            end_time=end,
            reservation_status=Reservation.ReservationStatus.CONFIRMED,
        )
        later_end = end + timedelta(hours=1)
        second_reservation = Reservation.objects.create(
            client=self.customer,
            parking_slot=ParkingSpace.objects.create(
                label="A2", parking_lot=self.lot, dimension_limit=600
            ),
            type_of_reservation="BOX",
            start_time=end,
            end_time=later_end,
            reservation_status=Reservation.ReservationStatus.CONFIRMED,
        )

        self.assertEqual(reservation.duration_hours, Decimal("2"))
        self.assertEqual(reservation.total_cost, Decimal("5.00"))
        self.assertIsNotNone(reservation.reservation_number)
        self.assertEqual(
            second_reservation.reservation_number,
            reservation.reservation_number + 1,
        )

    def test_overlapping_reservations_are_rejected(self):
        start = timezone.now()
        end = start + timedelta(hours=1)
        Reservation.objects.create(
            client=self.customer,
            parking_slot=self.space,
            start_time=start,
            end_time=end,
            reservation_status=Reservation.ReservationStatus.CONFIRMED,
        )

        overlap = Reservation(
            client=self.customer,
            parking_slot=self.space,
            start_time=start + timedelta(minutes=10),
            end_time=end + timedelta(minutes=10),
            reservation_status=Reservation.ReservationStatus.CONFIRMED,
        )

        with self.assertRaises(ValidationError):
            overlap.full_clean()

    def test_completed_status_set_when_end_time_passed(self):
        start = timezone.now() - timedelta(hours=2)
        end = timezone.now() - timedelta(hours=1)

        reservation = Reservation.objects.create(
            client=self.customer,
            parking_slot=self.space,
            start_time=start,
            end_time=end,
            reservation_status=Reservation.ReservationStatus.CONFIRMED,
        )

        self.assertEqual(
            reservation.reservation_status, Reservation.ReservationStatus.COMPLETED
        )


class ParkingSpaceTests(TestCase):
    def setUp(self):
        self.customer = Client.objects.create(
            full_name="Parked Driver",
            contact="1234567890",
            plate_number="PARK01",
            dimension=400,
        )
        self.lot = ParkingLot.objects.create(lot_id=10, lot_capacity=1)
        self.space = ParkingSpace.objects.create(
            label="L1", parking_lot=self.lot, dimension_limit=500
        )

    def test_is_available_respects_exclusion(self):
        start = timezone.now()
        end = start + timedelta(hours=1)
        active = Reservation.objects.create(
            client=self.customer,
            parking_slot=self.space,
            start_time=start,
            end_time=end,
            reservation_status=Reservation.ReservationStatus.CONFIRMED,
        )

        self.assertFalse(self.space.is_available(start, end))
        self.assertTrue(
            self.space.is_available(start, end, exclude_reservation_id=active.id)
        )

    def test_active_reservation_property(self):
        start = timezone.now() - timedelta(minutes=5)
        end = timezone.now() + timedelta(minutes=30)
        active = Reservation.objects.create(
            client=self.customer,
            parking_slot=self.space,
            start_time=start,
            end_time=end,
            reservation_status=Reservation.ReservationStatus.CONFIRMED,
        )

        self.assertEqual(self.space.active_reservation, active)
