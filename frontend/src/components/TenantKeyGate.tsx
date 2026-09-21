import { useState } from "react";
import { api, setAdminToken, setTenantId } from "@/api/client";

export function TenantKeyGate({ onSet }: { onSet: () => void }) {
  const [token, setToken] = useState("");
  const [tenantId, setTid] = useState("");
  const [pidiendo, setPidiendo] = useState(false);
  const [aviso, setAviso] = useState<string | null>(null);

  // El token generado NO vuelve por acá: se le envía por correo a
  // TECHBOT y quien lo pidió tiene que contactarlos (Javier,
  // 2026-09-21). Por eso lo único que se muestra es el mensaje.
  const pedirToken = async () => {
    setPidiendo(true);
    setAviso(null);
    try {
      // Se manda el tenant que el operador tiene escrito, para que el
      // correo indique de qué cliente se trata.
      const tid = Number(tenantId.trim());
      const r = await api.requestAdminToken(
        Number.isFinite(tid) && tid > 0 ? tid : null
      );
      setAviso(r.message);
    } catch {
      setAviso(
        "No se pudo generar el token. Contacta a TECHBOT para que te lo facilite."
      );
    } finally {
      setPidiendo(false);
    }
  };

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

        <div className="border-t border-slate-200 pt-4">
          <button
            type="button"
            onClick={pedirToken}
            disabled={pidiendo}
            className="w-full rounded-lg border border-indigo-600 text-indigo-700 hover:bg-indigo-50 disabled:opacity-50 font-medium py-2"
          >
            {pidiendo ? "Generando…" : "Generar token"}
          </button>
          <p className="mt-2 text-xs text-slate-500">
            Genera un token nuevo y lo envía a TECHBOT. Por seguridad no se
            muestra en pantalla.
          </p>
          {aviso && (
            <p className="mt-2 rounded-lg bg-slate-100 px-3 py-2 text-sm text-slate-700">
              {aviso}
            </p>
          )}
        </div>
      </form>
    </div>
  );
}
