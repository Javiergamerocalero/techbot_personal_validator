import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import {
  clearCredentials,
  getAdminToken,
  getTenantId,
} from "@/api/client";
import { TenantKeyGate } from "@/components/TenantKeyGate";
import { ExcelUploader } from "@/components/ExcelUploader";
import { EmployeesList } from "@/components/EmployeesList";

export default function App() {
  const [authed, setAuthed] = useState(
    Boolean(getAdminToken() && getTenantId())
  );
  const qc = useQueryClient();

  if (!authed) {
    return <TenantKeyGate onSet={() => setAuthed(true)} />;
  }

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-10">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-800">
            Validador de Empleados
          </h1>
          <p className="text-slate-500 text-sm">
            Tenant <strong>{getTenantId()}</strong> · Carga masiva de
            colaboradores autorizados.
          </p>
        </div>
        <button
          onClick={() => {
            clearCredentials();
            setAuthed(false);
          }}
          className="text-sm text-slate-500 hover:text-slate-700"
        >
          Cambiar credenciales
        </button>
      </header>

      <ExcelUploader
        onImported={() => qc.invalidateQueries({ queryKey: ["employees"] })}
      />
      <EmployeesList />
    </div>
  );
}
