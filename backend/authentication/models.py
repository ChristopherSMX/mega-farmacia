from django.conf import settings
from django.db import models


class UserMFA(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="mfa",
    )
    secret_encrypted = models.TextField(
        blank=True,
        help_text="Secreto TOTP cifrado; nunca almacenar el secreto en texto plano.",
    )
    is_enabled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    last_verified_at = models.DateTimeField(null=True, blank=True)
    last_accepted_totp_counter = models.BigIntegerField(
        null=True,
        blank=True,
        help_text=(
            "Último contador temporal TOTP aceptado; "
            "se utiliza para impedir la reutilización de códigos."
        ),
    )
    failed_attempts = models.PositiveSmallIntegerField(default=0)
    locked_until = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha y hora hasta la que la verificación MFA está bloqueada.",
    )
    login_failed_attempts = models.PositiveSmallIntegerField(default=0)
    login_locked_until = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha y hora hasta la que el inicio de sesión está bloqueado.",
    )

    def __str__(self):
        return f"MFA de {self.user.get_username()}"
