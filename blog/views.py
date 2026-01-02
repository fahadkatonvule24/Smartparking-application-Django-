from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from blog.forms import ClientForm, ParkingLotForm, ParkingSpaceForm, ReservationForm
from blog.models import Client, ParkingLot, ParkingSpace, Reservation
from blog.services import refresh_parking_state


def index_view(request):
    return render(request, "index.html")


def about_us_view(request):
    return render(request, "about_us.html")


@login_required
def dashboard_view(request):
    refresh_parking_state()
    now = timezone.now()
    total_clients = Client.objects.count()
    total_slots = ParkingSpace.objects.count()
    available_slots = ParkingSpace.objects.filter(
        is_active=True, is_occupied=False
    ).count()
    active_reservations = Reservation.objects.filter(
        reservation_status__in=Reservation.ACTIVE_STATUSES,
        start_time__lte=now,
        end_time__gte=now,
    )
    upcoming_reservations = (
        Reservation.objects.select_related("client", "parking_slot")
        .filter(start_time__gte=now)
        .order_by("start_time")[:5]
    )

    context = {
        "total_clients": total_clients,
        "total_slots": total_slots,
        "available_slots": available_slots,
        "active_reservations": active_reservations.count(),
        "upcoming_reservations": upcoming_reservations,
    }
    return render(request, "dashboard.html", context)


def cover_view(request):
    return render(request, "cover.html")


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard_page")

    form = AuthenticationForm(request, data=request.POST or None)
    for field in form.fields.values():
        field.widget.attrs.setdefault("class", "form-control")
    if request.method == "POST":
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, "Welcome back! You are now signed in.")
            next_page = request.POST.get("next") or reverse("dashboard_page")
            return redirect(next_page)
        messages.error(request, "Invalid credentials, please try again.")

    return render(request, "login.html", {"form": form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("index_page")


def parking_view(request):
    return render(request, "Parking.html")


@login_required
def parking_lot_view(request):
    refresh_parking_state()
    lot_form = ParkingLotForm(request.POST or None)
    show_modal = False

    if request.method == "POST" and lot_form.is_valid():
        lot_form.save()
        messages.success(request, "Parking lot added successfully.")
        return redirect("parking_lot_page")
    elif request.method == "POST":
        messages.error(
            request, "Unable to create the parking lot. Please review the form."
        )
        show_modal = True

    lots = (
        ParkingLot.objects.annotate(
            total_spaces=Count("spaces"),
            occupied_spaces=Count("spaces", filter=Q(spaces__is_occupied=True)),
        )
        .prefetch_related("spaces")
        .order_by("lot_id")
    )
    for lot in lots:
        capacity = lot.lot_capacity or lot.total_spaces
        lot.available_spaces = max(capacity - lot.occupied_spaces, 0)
        lot.capacity_display = capacity

    return render(
        request,
        "ParkingLot.html",
        {
            "lots": lots,
            "lot_form": lot_form,
            "show_lot_modal": show_modal,
        },
    )


@login_required
def parking_space_view(request):
    refresh_parking_state()
    spaces = (
        ParkingSpace.objects.select_related("parking_lot")
        .all()
        .order_by("floor_number", "label")
    )
    form = ParkingSpaceForm(request.POST or None)
    show_modal = False

    if request.method == "POST" and form.is_valid():
        form.save()
        refresh_parking_state()
        messages.success(request, "Parking slot created successfully.")
        return redirect("parking_space_page")
    elif request.method == "POST":
        messages.error(request, "Unable to create the slot. Please check the form.")
        show_modal = True

    now = timezone.now()
    active_reservations = Reservation.objects.select_related("client").filter(
        reservation_status__in=Reservation.ACTIVE_STATUSES,
        end_time__gt=now,
    )
    reservation_map = {res.parking_slot_id: res for res in active_reservations}
    for space in spaces:
        space.current_booking = reservation_map.get(space.id)
        space.recent_reservations = list(
            space.reservations.select_related("client").order_by("-start_time")[:5]
        )

    return render(
        request,
        "ParkingSpace.html",
        {
            "spaces": spaces,
            "form": form,
            "show_slot_modal": show_modal,
        },
    )


@login_required
def client_view(request):
    clients = Client.objects.all().order_by("-created_at")
    form = ClientForm(request.POST or None)
    show_modal = False

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Client profile added successfully.")
        return redirect("client_page")
    elif request.method == "POST":
        messages.error(request, "Unable to save client. Please correct errors below.")
        show_modal = True

    return render(
        request,
        "client.html",
        {"clients": clients, "form": form, "show_client_modal": show_modal},
    )


@login_required
def add_client_view(request):
    """Backward compatible route that delegates to the main client page."""
    return client_view(request)


@login_required
def edit_client_view(request, client_id):
    client_obj = get_object_or_404(Client, id=client_id)

    form = ClientForm(request.POST or None, instance=client_obj)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Client profile updated.")
        return redirect("client_page")
    elif request.method == "POST":
        messages.error(request, "Unable to update the client. Please fix errors.")

    return render(
        request,
        "edit_client.html",
        {
            "form": form,
            "client": client_obj,
        },
    )


@login_required
def delete_client_view(request, client_id):
    client_obj = get_object_or_404(Client, id=client_id)

    if request.method == "POST":
        client_obj.delete()
        messages.success(request, "Client removed successfully.")
        return redirect("client_page")

    return render(request, "confirm_delete.html", {"object": client_obj})


@login_required
def reservation_view(request):
    refresh_parking_state()
    reservations = (
        Reservation.objects.select_related("client", "parking_slot")
        .all()
        .order_by("-start_time")
    )
    form = ReservationForm(request.POST or None)
    show_modal = False

    if request.method == "POST" and form.is_valid():
        form.save()
        refresh_parking_state()
        messages.success(request, "Reservation saved and slot locked.")
        return redirect("reservation_page")
    elif request.method == "POST":
        messages.error(request, "Something went wrong. Please review the form.")
        show_modal = True

    available_slots = ParkingSpace.objects.filter(is_active=True, is_occupied=False)
    context = {
        "reservations": reservations,
        "form": form,
        "available_slots": available_slots.count(),
        "show_reservation_modal": show_modal,
    }
    return render(request, "reservation.html", context)


@login_required
def reservation_edit_view(request, reservation_id):
    reservation_instance = get_object_or_404(Reservation, id=reservation_id)
    form = ReservationForm(request.POST or None, instance=reservation_instance)

    if request.method == "POST" and form.is_valid():
        form.save()
        refresh_parking_state()
        messages.success(request, "Reservation updated.")
        return redirect("reservation_page")
    elif request.method == "POST":
        messages.error(request, "Unable to update reservation. Please try again.")

    return render(
        request,
        "reservation_edit.html",
        {"form": form, "reservation": reservation_instance},
    )


@login_required
def reservation_delete_view(request, reservation_id):
    reservation_instance = get_object_or_404(Reservation, id=reservation_id)
    if request.method == "POST":
        reservation_instance.delete()
        refresh_parking_state()
        messages.success(request, "Reservation deleted.")
        return redirect("reservation_page")
    return render(
        request,
        "confirm_delete.html",
        {"object": reservation_instance},
    )


def sign_up_view(request):
    sign_up_form = UserCreationForm(request.POST or None)
    for field in sign_up_form.fields.values():
        field.widget.attrs.setdefault("class", "form-control")
    if request.method == "POST" and sign_up_form.is_valid():
        sign_up_form.save()
        messages.success(request, "Account created! Sign in to continue.")
        return redirect("login_page")
    elif request.method == "POST":
        messages.error(request, "We could not create that account.")

    return render(request, "sign_up.html", {"form": sign_up_form})
