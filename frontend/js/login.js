document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("login-form");
  const error = document.getElementById("error-message");

  if (!form) return;

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    if (error) {
      error.textContent = "";
      error.style.display = "none";
    }

    const data = new FormData(form);
    const username = data.get("username");
    const password = data.get("password");

    try {
      const csrfToken = await getCsrfToken();

      const response = await fetch("/api/auth/login/", {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken
        },
        body: JSON.stringify({username, password})
      });

      const result = await response.json();

      if (response.ok && result.mfa_required === true) {
        window.location.assign("/mfa.html");
        return;
      }

      throw new Error(
        result.error ||
        result.message ||
        "No fue posible iniciar sesión"
      );
    } catch (err) {
      if (error) {
        error.textContent = err.message;
        error.style.display = "block";
      }
    }
  });
});
