from django.contrib.auth.forms import AuthenticationForm


def global_login_form(request):
    """Provide a login form to every template so we can render the modal globally."""
    form = AuthenticationForm(request=request)
    for field in form.fields.values():
        field.widget.attrs.setdefault("class", "form-control")
    return {
        "global_login_form": form,
    }
