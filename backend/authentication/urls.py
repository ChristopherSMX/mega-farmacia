from django.urls import path

from .views import (
    login_view,
    logout_view,
    mfa_setup_view,
    mfa_status_view,
    mfa_verify_view,
)

urlpatterns = [
    path("login/", login_view, name="api_login"),
    path("logout/", logout_view, name="api_logout"),
    path("mfa/setup/", mfa_setup_view, name="mfa_setup"),
    path("mfa/verify/", mfa_verify_view, name="mfa_verify"),
    path("mfa/status/", mfa_status_view, name="mfa_status"),
]
