from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from blog.models import Client, ParkingLot, ParkingSpace, Reservation
from blog.services import refresh_parking_state


class RefreshParkingStateTests(TestCase):
    def setUp(self):
        self.customer = Client.objects.create(
            full_name="Occupancy Driver",
            contact="1234567890",
            plate_number="OCC01",
            dimension=400,
        )
        self.lot = ParkingLot.objects.create(lot_id=99, lot_capacity=1)
        self.space = ParkingSpace.objects.create(
            label="O1", parking_lot=self.lot, dimension_limit=500
        )

    def test_marks_spaces_occupied_and_lot_full(self):
        start = timezone.now()
        end = start + timedelta(hours=1)
        Reservation.objects.create(
            client=self.customer,
            parking_slot=self.space,
            start_time=start,
            end_time=end,
            reservation_status=Reservation.ReservationStatus.CONFIRMED,
        )

        refresh_parking_state()
        self.space.refresh_from_db()
        self.lot.refresh_from_db()

        self.assertTrue(self.space.is_occupied)
        self.assertEqual(self.lot.current_status, "Full")

    def test_resets_occupancy_when_reservation_finished(self):
        start = timezone.now() - timedelta(hours=2)
        end = timezone.now() - timedelta(hours=1)
        Reservation.objects.create(
            client=self.customer,
            parking_slot=self.space,
            start_time=start,
            end_time=end,
            reservation_status=Reservation.ReservationStatus.CONFIRMED,
        )
        self.space.is_occupied = True
        self.space.save(update_fields=["is_occupied"])
        self.lot.current_status = "Full"
        self.lot.save(update_fields=["current_status"])

        refresh_parking_state()
        self.space.refresh_from_db()
        self.lot.refresh_from_db()

        self.assertFalse(self.space.is_occupied)
        self.assertEqual(self.lot.current_status, "Open")
