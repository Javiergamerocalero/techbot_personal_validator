import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api, getTenantId } from "@/api/client";

const PAGE_SIZE = 50;

export function EmployeesList() {
  const [page, setPage] = useState(0);
  const [q, setQ] = useState("");
  const tenantId = getTenantId();

  const query = useQuery({
    queryKey: ["employees", tenantId, page, q],
    enabled: tenantId !== null,
    queryFn: () =>
      api.listEmployees(tenantId!, {
        limit: PAGE_SIZE,
        offset: page * PAGE_SIZE,
        q: q.trim() || undefined,
      }),
  });

  const total = query.data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-4">
        <h2 className="text-xl font-semibold text-slate-800">
          Empleados cargados
        </h2>
        <input
          value={q}
          onChange={(e) => {
            setQ(e.target.value);
            setPage(0);
          }}
          placeholder="Buscar por nombre, código o DNI…"
          className="w-72 rounded-lg border border-slate-300 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
      </div>

      <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-slate-600 uppercase text-xs">
            <tr>
              <Th>Código</Th>
              <Th>Documento</Th>
              <Th>Nombre</Th>
              <Th>Estado</Th>
              <Th>Motivo</Th>
              <Th>Centro de costo</Th>
            </tr>
          </thead>
          <tbody>
            {query.isLoading && (
              <tr>
                <td colSpan={6} className="py-10 text-center text-slate-400">
                  Cargando…
                </td>
              </tr>
            )}
            {!query.isLoading && (query.data?.items.length ?? 0) === 0 && (
              <tr>
                <td colSpan={6} className="py-10 text-center text-slate-400">
                  Todavía no hay empleados cargados.
                </td>
              </tr>
            )}
            {query.data?.items.map((e) => (
              <tr key={e.id} className="border-t border-slate-100">
                <Td mono>{e.employeeCode}</Td>
                <Td mono>{e.documentNumber}</Td>
                <Td>{e.fullName}</Td>
                <Td>
                  <span
                    className={
                      e.status
                        ? "rounded-full bg-emerald-100 text-emerald-800 px-2 py-0.5 text-xs font-medium"
                        : "rounded-full bg-red-100 text-red-800 px-2 py-0.5 text-xs font-medium"
                    }
                  >
                    {e.status ? "ACTIVO" : "INACTIVO"}
                  </span>
                </Td>
                <Td>
                  <span className="text-slate-500">{e.statusReason}</span>
                </Td>
                <Td>{e.costCenter ?? "—"}</Td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between text-sm text-slate-500">
        <span>
          {total === 0
            ? "Sin resultados"
            : `Mostrando ${page * PAGE_SIZE + 1}–${Math.min(
                (page + 1) * PAGE_SIZE,
                total
              )} de ${total}`}
        </span>
        <div className="flex gap-2">
          <button
            onClick={() => setPage((p) => Math.max(0, p - 1))}
            disabled={page === 0}
            className="rounded border border-slate-300 px-3 py-1 disabled:opacity-40"
          >
            Anterior
          </button>
          <button
            onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
            disabled={page >= totalPages - 1}
            className="rounded border border-slate-300 px-3 py-1 disabled:opacity-40"
          >
            Siguiente
          </button>
        </div>
      </div>
    </div>
  );
}

const Th = ({ children }: { children: React.ReactNode }) => (
  <th className="text-left px-4 py-2 font-medium">{children}</th>
);
const Td = ({
  children,
  mono = false,
}: {
  children: React.ReactNode;
  mono?: boolean;
}) => (
  <td className={`px-4 py-2 ${mono ? "font-mono text-slate-700" : ""}`}>
    {children}
  </td>
);
