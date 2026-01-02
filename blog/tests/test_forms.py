from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from blog.forms import ReservationForm
from blog.models import Client, ParkingLot, ParkingSpace, Reservation


class ReservationFormTests(TestCase):
    def setUp(self):
        self.customer = Client.objects.create(
            full_name="Form Driver",
            contact="1234567890",
            plate_number="FORM01",
            dimension=400,
        )
        self.lot = ParkingLot.objects.create(lot_id=50, lot_capacity=2)
        self.space = ParkingSpace.objects.create(
            label="F1", parking_lot=self.lot, dimension_limit=500
        )
        self.start = timezone.now()
        self.end = self.start + timedelta(hours=1)

    def _payload(self, start, end):
        return {
            "client": self.customer.id,
            "parking_slot": self.space.id,
            "type_of_reservation": "BOX",
            "start_time": start.isoformat(timespec="minutes"),
            "end_time": end.isoformat(timespec="minutes"),
            "reservation_status": Reservation.ReservationStatus.CONFIRMED,
        }

    def test_rejects_overlapping_reservations(self):
        Reservation.objects.create(
            client=self.customer,
            parking_slot=self.space,
            start_time=self.start,
            end_time=self.end,
            reservation_status=Reservation.ReservationStatus.CONFIRMED,
        )

        form = ReservationForm(
            data=self._payload(
                self.start + timedelta(minutes=15),
                self.end + timedelta(minutes=15),
            )
        )

        self.assertFalse(form.is_valid())
        self.assertTrue(form.errors)
        self.assertIn("already booked", form.errors["__all__"][0])

    def test_accepts_available_slot(self):
        form = ReservationForm(
            data=self._payload(
                self.end + timedelta(hours=1),
                self.end + timedelta(hours=2),
            )
        )

        self.assertTrue(form.is_valid())
        instance = form.save()
        self.assertEqual(instance.client, self.customer)
