async function getCsrfToken() {
  const response = await fetch("/api/auth/csrf/", {
    method: "GET",
    credentials: "same-origin",
    cache: "no-store"
  });

  if (!response.ok) {
    throw new Error("No se pudo obtener el token CSRF");
  }

  const data = await response.json();

  if (!data.csrfToken) {
    throw new Error("Token CSRF no disponible");
  }

  return data.csrfToken;
}
