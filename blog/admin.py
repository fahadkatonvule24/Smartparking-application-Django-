from django.contrib import admin

from .models import Client, Parking, ParkingLot, ParkingSpace, Reservation


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("full_name", "plate_number", "contact", "car_type", "dimension")
    search_fields = ("full_name", "plate_number")


@admin.register(ParkingSpace)
class ParkingSpaceAdmin(admin.ModelAdmin):
    list_display = ("label", "floor_number", "space_type", "is_active")
    list_filter = ("space_type", "is_active")
    search_fields = ("label",)


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = (
        "reservation_number",
        "client",
        "parking_slot",
        "start_time",
        "end_time",
        "reservation_status",
        "total_cost",
    )
    list_filter = ("reservation_status", "parking_slot")
    search_fields = ("reservation_number", "client__full_name", "parking_slot__label")


admin.site.register(Parking)
admin.site.register(ParkingLot)
