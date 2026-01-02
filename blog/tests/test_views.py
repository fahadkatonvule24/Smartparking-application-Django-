from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from blog.models import Client, ParkingLot, ParkingSpace, Reservation


class ViewFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="strong-pass")
        self.customer = Client.objects.create(
            full_name="View Driver",
            contact="1234567890",
            plate_number="VIEW01",
            dimension=400,
        )
        self.lot = ParkingLot.objects.create(lot_id=5, lot_capacity=1)
        self.space = ParkingSpace.objects.create(
            label="V1", parking_lot=self.lot, dimension_limit=500
        )

    def test_dashboard_view_counts_and_context(self):
        self.client.force_login(self.user)
        start = timezone.now()
        end = start + timedelta(hours=1)
        Reservation.objects.create(
            client=self.customer,
            parking_slot=self.space,
            start_time=start,
            end_time=end,
            reservation_status=Reservation.ReservationStatus.CONFIRMED,
        )

        response = self.client.get(reverse("dashboard_page"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_clients"], 1)
        self.assertEqual(response.context["total_slots"], 1)
        self.assertEqual(response.context["available_slots"], 0)
        self.assertEqual(response.context["active_reservations"], 1)

    def test_create_client_via_view(self):
        self.client.force_login(self.user)
        payload = {
            "full_name": "New Driver",
            "contact": "5551234567",
            "plate_number": "NEW123",
            "dimension": 450,
            "car_type": "Sedan",
        }

        response = self.client.post(reverse("client_page"), data=payload, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Client.objects.count(), 2)

    def test_reservation_creation_sets_slot_occupied(self):
        self.client.force_login(self.user)
        start = timezone.now() + timedelta(hours=1)
        end = start + timedelta(hours=1)
        payload = {
            "client": self.customer.id,
            "parking_slot": self.space.id,
            "type_of_reservation": "BOX",
            "start_time": start.isoformat(timespec="minutes"),
            "end_time": end.isoformat(timespec="minutes"),
            "reservation_status": Reservation.ReservationStatus.CONFIRMED,
        }

        response = self.client.post(
            reverse("reservation_page"), data=payload, follow=True
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Reservation.objects.count(), 1)
        self.space.refresh_from_db()
        self.assertTrue(self.space.is_occupied)

    def test_parking_lot_creation(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("parking_lot_page"),
            data={"lot_id": 2, "lot_capacity": 5, "parking": ""},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(ParkingLot.objects.count(), 2)

    def test_parking_space_view_get(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("parking_space_page"))

        self.assertEqual(response.status_code, 200)
        self.assertIn("spaces", response.context)

    def test_reservation_edit_and_delete(self):
        self.client.force_login(self.user)
        start = timezone.now() + timedelta(hours=1)
        end = start + timedelta(hours=1)
        reservation = Reservation.objects.create(
            client=self.customer,
            parking_slot=self.space,
            start_time=start,
            end_time=end,
            reservation_status=Reservation.ReservationStatus.CONFIRMED,
        )
        updated_end = end + timedelta(hours=1)

        edit_response = self.client.post(
            reverse("reservation_edit_page", args=[reservation.id]),
            data={
                "client": self.customer.id,
                "parking_slot": self.space.id,
                "type_of_reservation": "BOX",
                "start_time": start.isoformat(timespec="minutes"),
                "end_time": updated_end.isoformat(timespec="minutes"),
                "reservation_status": Reservation.ReservationStatus.CONFIRMED,
            },
            follow=True,
        )
        reservation.refresh_from_db()

        self.assertEqual(edit_response.status_code, 200)
        self.assertEqual(
            reservation.end_time, updated_end.replace(second=0, microsecond=0)
        )

        delete_response = self.client.post(
            reverse("reservation_delete_page", args=[reservation.id]), follow=True
        )

        self.assertEqual(delete_response.status_code, 200)
        self.assertFalse(Reservation.objects.filter(id=reservation.id).exists())

    def test_delete_client_view(self):
        self.client.force_login(self.user)
        new_customer = Client.objects.create(
            full_name="Removable",
            contact="0001112222",
            plate_number="DEL001",
            dimension=400,
        )

        response = self.client.post(
            reverse("delete_client_page", args=[new_customer.id]), follow=True
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Client.objects.filter(id=new_customer.id).exists())

    def test_login_redirects_when_authenticated(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("login_page"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("dashboard_page"))
