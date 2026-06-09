import { useState } from "react";
import { setTenantKey } from "@/api/client";

export function TenantKeyGate({ onSet }: { onSet: () => void }) {
  const [value, setValue] = useState("");

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = value.trim();
    if (!trimmed) return;
    setTenantKey(trimmed);
    onSet();
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <form
        onSubmit={submit}
        className="w-full max-w-md space-y-4 bg-white rounded-2xl shadow-md p-8"
      >
        <h1 className="text-2xl font-bold text-slate-800">
          Empleados · Acceso
        </h1>
        <p className="text-sm text-slate-500">
          Pegá la API key de tu tenant para empezar. Se guarda solo en
          este navegador.
        </p>
        <input
          type="password"
          autoFocus
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="X-Tenant-Key"
          className="w-full rounded-lg border border-slate-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
        <button
          type="submit"
          disabled={!value.trim()}
          className="w-full rounded-lg bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 text-white font-semibold py-2"
        >
          Continuar
        </button>
      </form>
    </div>
  );
}
