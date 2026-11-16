const API_ORIGIN = "https://mega-farmacia-api.onrender.com";

const PRIVATE_PAGES = new Set([
  "dashboard.html",
  "inventario.html",
  "medicamentos.html",
  "usuarios.html",
  "auditoria.html",
  "pedidos.html",
  "recepcion.html",
  "devoluciones.html",
  "reportes.html"
]);

function normalizePath(pathname) {
  let path = pathname.replace(/\/+/g, "/");
  if (path.endsWith("/")) {
    path = path.slice(0, -1);
  }
  return path.toLowerCase();
}

function isPrivate(pathname) {
  const page = normalizePath(pathname).replace(/^\//, "");
  return PRIVATE_PAGES.has(page);
}

function loginRedirect(request) {
  return Response.redirect(
    new URL("/login.html", request.url),
    302
  );
}

async function checkAuthentication(request) {
  const statusUrl = new URL(
    "/api/auth/mfa/status/",
    API_ORIGIN
  );

  try {
    const response = await fetch(statusUrl, {
      method: "GET",
      headers: {
        Cookie: request.headers.get("Cookie") || "",
        Accept: "application/json"
      },
      redirect: "manual"
    });

    if (response.status !== 200) {
      return false;
    }

    const data = await response.json();

    return (
      data.configured === true &&
      data.enabled === true &&
      typeof data.username === "string" &&
      data.username.length > 0
    );
  } catch {
    return false;
  }
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const pathname = url.pathname;

    if (pathname.startsWith("/api/auth/")) {
      const target = new URL(
        pathname + url.search,
        API_ORIGIN
      );

      const headers = new Headers(request.headers);
      headers.delete("host");

      return fetch(
        new Request(target, {
          method: request.method,
          headers,
          body: ["GET", "HEAD"].includes(request.method)
            ? undefined
            : request.body,
          redirect: "manual"
        })
      );
    }

    if (isPrivate(pathname)) {
      const authenticated =
        await checkAuthentication(request);

      if (!authenticated) {
        return loginRedirect(request);
      }
    }

    return env.ASSETS.fetch(request);
  }
};
