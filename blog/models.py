from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Client(models.Model):
    """Vehicle owner information."""

    CAR_TYPE_OPTIONS = [
        ("Sedan", "Sedan"),
        ("SUV", "SUV"),
        ("Truck", "Truck"),
    ]

    full_name = models.CharField(max_length=120, default="Unnamed Client")
    contact = models.CharField(max_length=13, verbose_name="Client contact")
    plate_number = models.CharField(max_length=10)
    dimension = models.PositiveIntegerField()
    car_type = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        default="N/A",
        choices=CAR_TYPE_OPTIONS,
    )
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Client"
        verbose_name_plural = "Clients"

    def __str__(self) -> str:
        return f"{self.full_name} - {self.plate_number}"


class Parking(models.Model):
    """Raw parking record (currently used as a reference for lots)."""

    parking_id = models.IntegerField()
    time_in = models.TimeField()
    time_out = models.TimeField()
    status_pay = models.CharField(max_length=10)

    class Meta:
        verbose_name = "Parking"
        verbose_name_plural = "Parkings"

    def __str__(self) -> str:
        return f"Parking #{self.parking_id}"


class ParkingLot(models.Model):
    lot_id = models.IntegerField()
    parking = models.ForeignKey(
        Parking, on_delete=models.CASCADE, null=True, blank=True, related_name="lots"
    )
    current_status = models.CharField(max_length=32, default="Open")
    lot_capacity = models.PositiveIntegerField(default=10)

    class Meta:
        ordering = ["lot_id"]
        verbose_name = "Parking lot"
        verbose_name_plural = "Parking lots"

    def __str__(self):
        return f"Lot {self.lot_id}"


class ParkingSpace(models.Model):
    SPACE_TYPE_OPTIONS = [
        ("BOX", "Box parking"),
        ("Angular", "Angular parking"),
    ]
    label = models.CharField(max_length=20, unique=True, null=True)
    parking_lot = models.ForeignKey(
        ParkingLot,
        on_delete=models.CASCADE,
        related_name="spaces",
        null=True,
        blank=True,
    )
    space_type = models.CharField(
        max_length=20, null=True, blank=True, choices=SPACE_TYPE_OPTIONS
    )
    floor_number = models.IntegerField(default=1)
    dimension_limit = models.PositiveIntegerField(default=500)
    is_active = models.BooleanField(default=True)
    is_occupied = models.BooleanField(default=False)

    class Meta:
        ordering = ["floor_number", "label"]
        verbose_name = "Parking space"
        verbose_name_plural = "Parking spaces"

    def __str__(self):
        return f"{self.label} (Floor {self.floor_number})"

    def is_available(self, start_time, end_time, exclude_reservation_id=None):
        """Return True when the slot has no overlapping active reservations."""
        overlapping = self.reservations.filter(
            start_time__lt=end_time,
            end_time__gt=start_time,
            reservation_status__in=Reservation.ACTIVE_STATUSES,
        )
        if exclude_reservation_id:
            overlapping = overlapping.exclude(pk=exclude_reservation_id)
        return not overlapping.exists()

    @property
    def active_reservation(self):
        now = timezone.now()
        return (
            self.reservations.filter(
                start_time__lte=now,
                end_time__gt=now,
                reservation_status__in=Reservation.ACTIVE_STATUSES,
            )
            .order_by("start_time")
            .first()
        )


class Reservation(models.Model):
    RESERVATION_TYPE_OPTIONS = [
        ("BOX", "Box parking"),
        ("Angular", "Angular parking"),
    ]

    class ReservationStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        CONFIRMED = "CONFIRMED", "Confirmed"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    ACTIVE_STATUSES = (ReservationStatus.PENDING, ReservationStatus.CONFIRMED)

    reservation_number = models.PositiveIntegerField(unique=True, blank=True, null=True)
    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name="reservations", null=True
    )
    parking_slot = models.ForeignKey(
        ParkingSpace,
        on_delete=models.PROTECT,
        related_name="reservations",
        null=True,
    )
    type_of_reservation = models.CharField(
        max_length=10, null=True, blank=True, choices=RESERVATION_TYPE_OPTIONS
    )
    start_time = models.DateTimeField(null=True)
    end_time = models.DateTimeField(null=True)
    reservation_status = models.CharField(
        max_length=10,
        choices=ReservationStatus.choices,
        default=ReservationStatus.PENDING,
    )
    total_cost = models.DecimalField(
        max_digits=8, decimal_places=2, default=Decimal("0")
    )
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        ordering = ["-start_time"]
        verbose_name = "Reservation"
        verbose_name_plural = "Reservations"

    def __str__(self):
        return f"Reservation #{self.reservation_number}"

    @property
    def duration_hours(self):
        """Return the booking duration in hours as Decimal."""
        if not self.start_time or not self.end_time:
            return Decimal("0")
        delta = self.end_time - self.start_time
        return Decimal(delta.total_seconds()) / Decimal(3600)

    def clean(self):
        if not self.parking_slot or not self.start_time or not self.end_time:
            return

        if self.end_time <= self.start_time:
            raise ValidationError("Checkout time must be later than check in time.")

        overlapping = Reservation.objects.filter(
            parking_slot=self.parking_slot,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time,
            reservation_status__in=Reservation.ACTIVE_STATUSES,
        )
        if self.pk:
            overlapping = overlapping.exclude(pk=self.pk)
        if overlapping.exists():
            raise ValidationError(
                "The selected slot is not available during the requested period."
            )

    def save(self, *args, **kwargs):
        if not self.reservation_number:
            last_reservation = Reservation.objects.order_by(
                "-reservation_number"
            ).first()
            base_number = (
                last_reservation.reservation_number if last_reservation else 1000
            )
            self.reservation_number = base_number + 1

        self.full_clean()
        hourly_rate = Decimal("2.50")
        self.total_cost = (self.duration_hours * hourly_rate).quantize(Decimal("0.01"))

        if (
            self.reservation_status == Reservation.ReservationStatus.CONFIRMED
            and self.end_time
            and self.end_time <= timezone.now()
        ):
            self.reservation_status = Reservation.ReservationStatus.COMPLETED

        super().save(*args, **kwargs)
