import json

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST


@csrf_exempt
@require_POST
def login_view(request):
    try:
        data = json.loads(request.body or "{}")

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

        return JsonResponse(
            {
                "authenticated": True,
                "mfa_required": True,
                "username": user.username,
                "message": "Credenciales válidas. Se requiere MFA.",
            },
            status=200,
        )

    except json.JSONDecodeError:
        return JsonResponse(
            {
                "authenticated": False,
                "error": "Solicitud JSON inválida.",
            },
            status=400,
        )

    except Exception:
        return JsonResponse(
            {
                "authenticated": False,
                "error": "Error interno del servidor.",
            },
            status=500,
        )
