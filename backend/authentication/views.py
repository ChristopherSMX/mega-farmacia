import json

import pyotp
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .mfa_crypto import (
    MFAEncryptionError,
    decrypt_totp_secret,
    encrypt_totp_secret,
)
from .models import UserMFA


def _read_json(request):
    try:
        return json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return None


def _get_user(username):
    username = str(username or "").strip()

    if not username:
        return None

    try:
        return User.objects.get(username__iexact=username)
    except (User.DoesNotExist, User.MultipleObjectsReturned):
        return None


@csrf_exempt
@require_POST
def login_view(request):
    data = _read_json(request)

    if data is None:
        return JsonResponse(
            {
                "authenticated": False,
                "error": "Solicitud JSON inválida.",
            },
            status=400,
        )

    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))

    if not username or not password:
        return JsonResponse(
            {
                "authenticated": False,
                "error": "Usuario y contraseña son obligatorios.",
            },
            status=400,
        )

    user = authenticate(
        request,
        username=username,
        password=password,
    )

    if user is None and "@" in username:
        try:
            account = User.objects.get(email__iexact=username)

            user = authenticate(
                request,
                username=account.username,
                password=password,
            )
        except (User.DoesNotExist, User.MultipleObjectsReturned):
            user = None

    if user is None:
        return JsonResponse(
            {
                "authenticated": False,
                "error": "Usuario o contraseña incorrectos.",
            },
            status=401,
        )

    if not user.is_active:
        return JsonResponse(
            {
                "authenticated": False,
                "error": "La cuenta está deshabilitada.",
            },
            status=403,
        )

    mfa = UserMFA.objects.filter(user=user).first()

    return JsonResponse(
        {
            "authenticated": True,
            "mfa_required": True,
            "mfa_configured": bool(
                mfa
                and mfa.is_enabled
                and mfa.secret_encrypted
            ),
            "username": user.username,
            "message": "Credenciales válidas. Se requiere MFA.",
        },
        status=200,
    )


@csrf_exempt
@require_POST
def mfa_setup_view(request):
    data = _read_json(request)

    if data is None:
        return JsonResponse(
            {"error": "Solicitud JSON inválida."},
            status=400,
        )

    user = _get_user(data.get("username"))

    if user is None:
        return JsonResponse(
            {"error": "Usuario no encontrado."},
            status=404,
        )

    mfa, _ = UserMFA.objects.get_or_create(user=user)

    if mfa.is_enabled and mfa.secret_encrypted:
        return JsonResponse(
            {
                "error": "MFA ya está configurado para este usuario.",
            },
            status=409,
        )

    secret = pyotp.random_base32()

    try:
        mfa.secret_encrypted = encrypt_totp_secret(secret)
    except MFAEncryptionError as exc:
        return JsonResponse(
            {"error": str(exc)},
            status=500,
        )

    mfa.is_enabled = False
    mfa.last_verified_at = None
    mfa.save()

    issuer = "SIALI Mega Farmacia"

    provisioning_uri = pyotp.TOTP(secret).provisioning_uri(
        name=user.username,
        issuer_name=issuer,
    )

    return JsonResponse(
        {
            "username": user.username,
            "issuer": issuer,
            "secret": secret,
            "provisioning_uri": provisioning_uri,
            "message": (
                "Agregue la cuenta a Google Authenticator y "
                "verifique el primer código antes de habilitar MFA."
            ),
        },
        status=200,
    )


@csrf_exempt
@require_POST
def mfa_verify_view(request):
    data = _read_json(request)

    if data is None:
        return JsonResponse(
            {"verified": False, "error": "Solicitud JSON inválida."},
            status=400,
        )

    user = _get_user(data.get("username"))
    code = str(data.get("code", "")).strip().replace(" ", "")

    if user is None:
        return JsonResponse(
            {"verified": False, "error": "Usuario no encontrado."},
            status=404,
        )

    if not code or not code.isdigit() or len(code) != 6:
        return JsonResponse(
            {
                "verified": False,
                "error": "El código MFA debe contener 6 dígitos.",
            },
            status=400,
        )

    try:
        mfa = UserMFA.objects.get(user=user)
    except UserMFA.DoesNotExist:
        return JsonResponse(
            {
                "verified": False,
                "error": "MFA no está configurado para este usuario.",
            },
            status=404,
        )

    try:
        secret = decrypt_totp_secret(mfa.secret_encrypted)
    except MFAEncryptionError as exc:
        return JsonResponse(
            {"verified": False, "error": str(exc)},
            status=500,
        )

    verified = pyotp.TOTP(secret).verify(
        code,
        valid_window=1,
    )

    if not verified:
        return JsonResponse(
            {
                "verified": False,
                "error": "Código MFA inválido o expirado.",
            },
            status=401,
        )

    mfa.is_enabled = True
    mfa.last_verified_at = timezone.now()
    mfa.save(
        update_fields=[
            "is_enabled",
            "last_verified_at",
        ]
    )

    return JsonResponse(
        {
            "verified": True,
            "username": user.username,
            "mfa_enabled": True,
            "message": "Código MFA verificado correctamente.",
        },
        status=200,
    )


@require_GET
def mfa_status_view(request):
    username = str(
        request.GET.get("username", "")
    ).strip()

    user = _get_user(username)

    if user is None:
        return JsonResponse(
            {"error": "Usuario no encontrado."},
            status=404,
        )

    mfa = UserMFA.objects.filter(user=user).first()

    if mfa is None:
        return JsonResponse(
            {
                "username": user.username,
                "configured": False,
                "enabled": False,
                "last_verified_at": None,
            },
            status=200,
        )

    configured = bool(mfa.secret_encrypted)

    return JsonResponse(
        {
            "username": user.username,
            "configured": configured,
            "enabled": mfa.is_enabled,
            "last_verified_at": (
                mfa.last_verified_at.isoformat()
                if mfa.last_verified_at
                else None
            ),
        },
        status=200,
    )
