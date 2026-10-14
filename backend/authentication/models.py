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

    def __str__(self):
        return f"MFA de {self.user.get_username()}"
