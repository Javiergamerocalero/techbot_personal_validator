import { useState } from "react";
import { setAdminToken, setTenantId } from "@/api/client";

export function TenantKeyGate({ onSet }: { onSet: () => void }) {
  const [token, setToken] = useState("");
  const [tenantId, setTid] = useState("");

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    const cleanToken = token.trim();
    const cleanTid = Number(tenantId.trim());
    if (!cleanToken || !cleanTid || cleanTid <= 0) return;
    setAdminToken(cleanToken);
    setTenantId(cleanTid);
    onSet();
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <form
        onSubmit={submit}
        className="w-full max-w-md space-y-4 bg-white rounded-2xl shadow-md p-8"
      >
        <h1 className="text-2xl font-bold text-slate-800">
          Validador de Empleados · Acceso
        </h1>
        <p className="text-sm text-slate-500">
          Ingresá el token de administración y el tenant_id del cliente
          con el que vas a trabajar (ej. San Fernando = 22). Quedan
          guardados solo en este navegador.
        </p>

        <label className="block text-sm font-medium text-slate-700">
          Token de administración
          <input
            type="password"
            autoFocus
            value={token}
            onChange={(e) => setToken(e.target.value)}
            placeholder="X-Admin-Token"
            className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </label>

        <label className="block text-sm font-medium text-slate-700">
          Tenant ID
          <input
            type="number"
            min={1}
            value={tenantId}
            onChange={(e) => setTid(e.target.value)}
            placeholder="22"
            className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </label>

        <button
          type="submit"
          disabled={!token.trim() || !tenantId.trim()}
          className="w-full rounded-lg bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 text-white font-semibold py-2"
        >
          Continuar
        </button>
      </form>
    </div>
  );
}
