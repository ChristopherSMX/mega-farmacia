import test from "node:test";
import assert from "node:assert/strict";
import worker from "../worker.js";

async function run(path, {
  status = 401,
  data = {},
  fail = false
} = {}) {
  const originalFetch = globalThis.fetch;

  globalThis.fetch = async () => {
    if (fail) {
      throw new Error("Backend unavailable");
    }

    return new Response(JSON.stringify(data), {
      status,
      headers: {
        "Content-Type": "application/json"
      }
    });
  };

  try {
    const request = new Request(
      `https://siali.example${path}`
    );

    const env = {
      ASSETS: {
        fetch: async () => new Response("ASSET", {
          status: 200
        })
      }
    };

    return await worker.fetch(request, env);
  } finally {
    globalThis.fetch = originalFetch;
  }
}

const validMfa = {
  status: 200,
  data: {
    configured: true,
    enabled: true,
    username: "usuario_prueba"
  }
};

test("01 - Login publico", async () => {
  const r = await run("/login.html");
  assert.equal(r.status, 200);
});

test("02 - Dashboard sin sesion", async () => {
  const r = await run("/dashboard.html");
  assert.equal(r.status, 302);
});

test("03 - MFA deshabilitado", async () => {
  const r = await run("/dashboard.html", {
    status: 200,
    data: {
      configured: true,
      enabled: false,
      username: "usuario_prueba"
    }
  });
  assert.equal(r.status, 302);
});

test("04 - MFA valido", async () => {
  const r = await run("/dashboard.html", validMfa);
  assert.equal(r.status, 200);
});

test("05 - Backend no disponible", async () => {
  const r = await run("/dashboard.html", {
    fail: true
  });
  assert.equal(r.status, 302);
});

test("06 - Ruta con barra final", async () => {
  const r = await run("/dashboard.html/", validMfa);
  assert.equal(r.status, 200);
});

test("07 - Ruta con mayusculas", async () => {
  const r = await run("/DASHBOARD.HTML");
  assert.equal(r.status, 302);
});

test("08 - Inventario protegido", async () => {
  const r = await run("/inventario.html");
  assert.equal(r.status, 302);
});

test("09 - Auditoria protegida", async () => {
  const r = await run("/auditoria.html");
  assert.equal(r.status, 302);
});

test("10 - Respuesta MFA incompleta", async () => {
  const r = await run("/dashboard.html", {
    status: 200,
    data: {
      configured: true,
      enabled: true
    }
  });
  assert.equal(r.status, 302);
});
