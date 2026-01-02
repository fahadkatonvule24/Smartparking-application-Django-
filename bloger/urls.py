"""URL configuration for bloger project."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from blog.views import (
    about_us_view,
    add_client_view,
    client_view,
    cover_view,
    dashboard_view,
    delete_client_view,
    edit_client_view,
    index_view,
    login_view,
    logout_view,
    parking_lot_view,
    parking_space_view,
    parking_view,
    reservation_delete_view,
    reservation_edit_view,
    reservation_view,
    sign_up_view,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", index_view, name="index_page"),
    path("about/", about_us_view, name="about_us_page"),
    path("dashboard/", dashboard_view, name="dashboard_page"),
    path("client/", client_view, name="client_page"),
    path("cover/", cover_view, name="cover_page"),
    path("login/", login_view, name="login_page"),
    path("logout/", logout_view, name="logout_page"),
    path("parking/", parking_view, name="parking_page"),
    path("parking_lot/", parking_lot_view, name="parking_lot_page"),
    path("parking_space/", parking_space_view, name="parking_space_page"),
    path("reservation/", reservation_view, name="reservation_page"),
    path(
        "reservation/<int:reservation_id>/edit/",
        reservation_edit_view,
        name="reservation_edit_page",
    ),
    path(
        "reservation/<int:reservation_id>/delete/",
        reservation_delete_view,
        name="reservation_delete_page",
    ),
    path("add_client/", add_client_view, name="add_client_page"),
    path("edit_client/<int:client_id>/", edit_client_view, name="edit_client_page"),
    path(
        "delete_client/<int:client_id>/", delete_client_view, name="delete_client_page"
    ),
    path("sign_up/", sign_up_view, name="sign_up_page"),
]

if settings.DEBUG and "debug_toolbar" in settings.INSTALLED_APPS:
    urlpatterns.append(path("__debug__/", include("debug_toolbar.urls")))

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
