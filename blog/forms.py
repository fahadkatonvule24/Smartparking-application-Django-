from django import forms
from django.forms import ModelForm

from blog.models import Client, ParkingLot, ParkingSpace, Reservation


class StyledModelForm(ModelForm):
    """Base form that injects Bootstrap styling."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css_classes = field.widget.attrs.get("class", "")
            if isinstance(field.widget, forms.CheckboxInput):
                default_class = "form-check-input"
            elif isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
                default_class = "form-select"
            else:
                default_class = "form-control"
            field.widget.attrs["class"] = f"{css_classes} {default_class}".strip()


class ClientForm(StyledModelForm):
    class Meta:
        model = Client
        fields = [
            "full_name",
            "contact",
            "plate_number",
            "dimension",
            "car_type",
        ]
        widgets = {
            "car_type": forms.Select(attrs={"class": "form-select"}),
        }


class ParkingSpaceForm(StyledModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "parking_lot" in self.fields:
            self.fields["parking_lot"].required = False
            self.fields["parking_lot"].empty_label = "Unassigned"

    class Meta:
        model = ParkingSpace
        fields = [
            "label",
            "parking_lot",
            "floor_number",
            "space_type",
            "dimension_limit",
            "is_active",
        ]
        widgets = {
            "space_type": forms.Select(attrs={"class": "form-select"}),
            "parking_lot": forms.Select(attrs={"class": "form-select"}),
            "is_active": forms.CheckboxInput(
                attrs={"class": "form-check-input", "role": "switch"}
            ),
        }


class ParkingLotForm(StyledModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "parking" in self.fields:
            self.fields["parking"].required = False
            self.fields["parking"].empty_label = "Not linked"

    class Meta:
        model = ParkingLot
        fields = ["lot_id", "lot_capacity", "parking"]
        widgets = {
            "parking": forms.Select(attrs={"class": "form-select"}),
        }


class ReservationForm(StyledModelForm):
    start_time = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local", "class": "form-control"}
        )
    )
    end_time = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local", "class": "form-control"}
        )
    )

    class Meta:
        model = Reservation
        fields = [
            "client",
            "parking_slot",
            "type_of_reservation",
            "start_time",
            "end_time",
            "reservation_status",
        ]
        widgets = {
            "client": forms.Select(attrs={"class": "form-select"}),
            "parking_slot": forms.Select(attrs={"class": "form-select"}),
            "type_of_reservation": forms.Select(attrs={"class": "form-select"}),
            "reservation_status": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["reservation_status"].initial = (
            Reservation.ReservationStatus.CONFIRMED
        )

    def clean(self):
        cleaned_data = super().clean()
        slot = cleaned_data.get("parking_slot")
        start = cleaned_data.get("start_time")
        end = cleaned_data.get("end_time")

        if slot and start and end:
            exclude_id = (
                self.instance.pk if self.instance and self.instance.pk else None
            )
            if not slot.is_available(start, end, exclude_reservation_id=exclude_id):
                raise forms.ValidationError(
                    "The selected slot is already booked for the selected window."
                )

        return cleaned_data
