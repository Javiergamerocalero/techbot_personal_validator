import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { clearTenantKey, getTenantKey } from "@/api/client";
import { TenantKeyGate } from "@/components/TenantKeyGate";
import { ExcelUploader } from "@/components/ExcelUploader";
import { EmployeesList } from "@/components/EmployeesList";

export default function App() {
  const [hasKey, setHasKey] = useState(Boolean(getTenantKey()));
  const qc = useQueryClient();

  if (!hasKey) {
    return <TenantKeyGate onSet={() => setHasKey(true)} />;
  }

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-10">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-800">
            Qapp · Empleados
          </h1>
          <p className="text-slate-500 text-sm">
            Carga masiva de colaboradores autorizados.
          </p>
        </div>
        <button
          onClick={() => {
            clearTenantKey();
            setHasKey(false);
          }}
          className="text-sm text-slate-500 hover:text-slate-700"
        >
          Cambiar tenant
        </button>
      </header>

      <ExcelUploader
        onImported={() => qc.invalidateQueries({ queryKey: ["employees"] })}
      />
      <EmployeesList />
    </div>
  );
}
