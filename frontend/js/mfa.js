document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("mfa-form");
  const error = document.getElementById("error-message");

  if (!form) return;

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    if (error) {
      error.textContent = "";
      error.style.display = "none";
    }

    const code = document.getElementById("mfa-code")?.value;

    try {
      const csrfToken = await getCsrfToken();

      const response = await fetch("/api/auth/mfa/verify/", {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken
        },
        body: JSON.stringify({code})
      });

      const result = await response.json();

      if (response.ok && result.verified === true) {
        window.location.assign("/dashboard.html");
        return;
      }

      throw new Error(
        result.error ||
        result.message ||
        "Código de verificación incorrecto"
      );
    } catch (err) {
      if (error) {
        error.textContent = err.message;
        error.style.display = "block";
      }
    }
  });
});
