from __future__ import annotations

from collections import defaultdict

from django.db.models import Count, Q
from django.utils import timezone


def refresh_parking_state():
    """Sync parking slot occupancy and lot status based on active reservations."""
    from blog.models import ParkingLot, ParkingSpace, Reservation

    now = timezone.now()
    active_reservations = (
        Reservation.objects.filter(
            reservation_status__in=Reservation.ACTIVE_STATUSES,
            end_time__gt=now,
        )
        .select_related("parking_slot")
        .only("id", "parking_slot_id")
    )

    slot_to_reservation = defaultdict(list)
    for booking in active_reservations:
        slot_to_reservation[booking.parking_slot_id].append(booking)

    spaces = ParkingSpace.objects.select_related("parking_lot").all()
    to_update = []
    for space in spaces:
        should_be_occupied = space.id in slot_to_reservation
        if space.is_occupied != should_be_occupied:
            space.is_occupied = should_be_occupied
            to_update.append(space)

    if to_update:
        ParkingSpace.objects.bulk_update(to_update, ["is_occupied"])

    lot_updates = []
    lot_stats = ParkingLot.objects.annotate(
        total_spaces=Count("spaces"),
        occupied_spaces=Count("spaces", filter=Q(spaces__is_occupied=True)),
    )
    for lot in lot_stats:
        capacity = lot.lot_capacity or lot.total_spaces or 0
        available = max(capacity - lot.occupied_spaces, 0)
        status = "Full" if available <= 0 and capacity > 0 else "Open"
        if lot.current_status != status:
            lot.current_status = status
            lot_updates.append(lot)

    if lot_updates:
        ParkingLot.objects.bulk_update(lot_updates, ["current_status"])
