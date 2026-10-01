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
import { PurchasesView } from "@/components/PurchasesView";

type View = "employees" | "purchases";

export default function App() {
  const [authed, setAuthed] = useState(
    Boolean(getAdminToken() && getTenantId())
  );
  const [view, setView] = useState<View>("employees");
  const qc = useQueryClient();

  if (!authed) {
    return <TenantKeyGate onSet={() => setAuthed(true)} />;
  }

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-8">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-800">
            Validador de Empleados
          </h1>
          <p className="text-slate-500 text-sm">
            Tenant <strong>{getTenantId()}</strong> ·{" "}
            {view === "employees"
              ? "Carga masiva de colaboradores autorizados."
              : "Registros de compra por fechas."}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <nav className="flex rounded-lg border border-slate-200 overflow-hidden text-sm">
            <button
              onClick={() => setView("employees")}
              className={
                "px-4 py-2 " +
                (view === "employees"
                  ? "bg-slate-800 text-white"
                  : "text-slate-600 hover:bg-slate-50")
              }
            >
              Empleados
            </button>
            <button
              onClick={() => setView("purchases")}
              className={
                "px-4 py-2 " +
                (view === "purchases"
                  ? "bg-slate-800 text-white"
                  : "text-slate-600 hover:bg-slate-50")
              }
            >
              Compras
            </button>
          </nav>
          <button
            onClick={() => {
              clearCredentials();
              setAuthed(false);
            }}
            className="text-sm text-slate-500 hover:text-slate-700"
          >
            Cambiar credenciales
          </button>
        </div>
      </header>

      {view === "employees" ? (
        <div className="space-y-10">
          <ExcelUploader
            onImported={() =>
              qc.invalidateQueries({ queryKey: ["employees"] })
            }
          />
          <EmployeesList />
        </div>
      ) : (
        <PurchasesView />
      )}
    </div>
  );
}
