import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api, getTenantId } from "@/api/client";
import type { EmployeeListItem, PurchaseListResponse } from "@/types";

/**
 * Vista de compras del tenant. Pedido por Javier el 2026-10-01: ver y
 * descargar las ventas por fechas, con subfiltro por empleado o general.
 *
 * - Rango de fechas (inclusivo; el día "hasta" entra entero).
 * - Subfiltro: "General" (todos) o un empleado concreto, que se busca por
 *   nombre/documento reutilizando el listado de empleados.
 * - Tabla con el total del período y botón de descarga a Excel (el mismo
 *   filtro que se ve en pantalla).
 */
const PAGE = 100;
const money = (cents: number) =>
  `S/ ${(cents / 100).toLocaleString("es-PE", { minimumFractionDigits: 2 })}`;
const dateTime = (iso: string) =>
  new Date(iso).toLocaleString("es-PE", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

export function PurchasesView() {
  const tenantId = getTenantId() ?? 0;
  const today = new Date().toISOString().slice(0, 10);
  const firstOfMonth = `${today.slice(0, 8)}01`;

  const [dateFrom, setDateFrom] = useState(firstOfMonth);
  const [dateTo, setDateTo] = useState(today);
  const [employee, setEmployee] = useState<EmployeeListItem | null>(null);
  const [page, setPage] = useState(0);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const filters = useMemo(
    () => ({
      dateFrom: dateFrom || undefined,
      dateTo: dateTo || undefined,
      employeeId: employee?.id ?? undefined,
    }),
    [dateFrom, dateTo, employee]
  );

  const query = useQuery<PurchaseListResponse>({
    queryKey: ["purchases", tenantId, filters, page],
    queryFn: () =>
      api.listPurchases(tenantId, {
        ...filters,
        limit: PAGE,
        offset: page * PAGE,
      }),
    enabled: tenantId > 0,
  });

  const data = query.data;
  const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE)) : 1;

  async function onDownload() {
    setDownloading(true);
    setError(null);
    try {
      const blob = await api.downloadPurchases(tenantId, filters);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      const suf = [dateFrom, dateTo].filter(Boolean).join("_");
      a.download = `compras${suf ? "_" + suf : ""}.xlsx`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo descargar.");
    } finally {
      setDownloading(false);
    }
  }

  function resetPageAnd(fn: () => void) {
    setPage(0);
    fn();
  }

  return (
    <section className="space-y-5">
      <div className="bg-white rounded-xl border border-slate-200 p-5 space-y-4">
        <div className="flex flex-wrap items-end gap-4">
          <label className="text-sm text-slate-600">
            Desde
            <input
              type="date"
              value={dateFrom}
              max={dateTo || undefined}
              onChange={(e) => resetPageAnd(() => setDateFrom(e.target.value))}
              className="mt-1 block border rounded-lg px-3 py-2"
            />
          </label>
          <label className="text-sm text-slate-600">
            Hasta
            <input
              type="date"
              value={dateTo}
              min={dateFrom || undefined}
              onChange={(e) => resetPageAnd(() => setDateTo(e.target.value))}
              className="mt-1 block border rounded-lg px-3 py-2"
            />
          </label>
          <div className="text-sm text-slate-600">
            Empleado
            <EmployeePicker
              tenantId={tenantId}
              selected={employee}
              onSelect={(emp) => resetPageAnd(() => setEmployee(emp))}
            />
          </div>
          <button
            onClick={onDownload}
            disabled={downloading || !data || data.total === 0}
            className="ml-auto bg-slate-800 text-white rounded-lg px-4 py-2 text-sm disabled:opacity-40"
          >
            {downloading ? "Generando…" : "Descargar Excel"}
          </button>
        </div>
        <p className="text-sm text-slate-500">
          {employee
            ? `Mostrando compras de ${employee.fullName}.`
            : "Mostrando compras de todos los empleados."}
          {data
            ? ` ${data.total} registro(s) · Total del período: ${money(
                data.totalCents
              )}.`
            : ""}
        </p>
        {error && <p className="text-sm text-red-600">{error}</p>}
      </div>

      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-slate-600 uppercase text-xs">
            <tr>
              <th className="text-left px-4 py-2 font-medium">Fecha</th>
              <th className="text-left px-4 py-2 font-medium">Empleado</th>
              <th className="text-left px-4 py-2 font-medium">Documento</th>
              <th className="text-right px-4 py-2 font-medium">Monto</th>
              <th className="text-left px-4 py-2 font-medium">Kiosco</th>
            </tr>
          </thead>
          <tbody>
            {query.isLoading && (
              <tr>
                <td colSpan={5} className="py-10 text-center text-slate-400">
                  Cargando…
                </td>
              </tr>
            )}
            {query.isError && (
              <tr>
                <td colSpan={5} className="py-10 text-center text-red-500">
                  {(query.error as Error).message}
                </td>
              </tr>
            )}
            {data && data.items.length === 0 && !query.isLoading && (
              <tr>
                <td colSpan={5} className="py-10 text-center text-slate-400">
                  Sin compras para este filtro.
                </td>
              </tr>
            )}
            {data?.items.map((p) => (
              <tr key={p.id} className="border-t border-slate-100">
                <td className="px-4 py-2 whitespace-nowrap">
                  {dateTime(p.purchasedAt)}
                </td>
                <td className="px-4 py-2">
                  {p.employeeName}
                  <span className="text-slate-400"> · {p.employeeCode}</span>
                </td>
                <td className="px-4 py-2">{p.documentNumber}</td>
                <td className="px-4 py-2 text-right whitespace-nowrap">
                  {money(p.amountCents)}
                </td>
                <td className="px-4 py-2 text-slate-500">{p.kioskName || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {data && data.total > PAGE && (
        <div className="flex items-center justify-between text-sm">
          <button
            onClick={() => setPage((p) => Math.max(0, p - 1))}
            disabled={page === 0}
            className="px-3 py-1 rounded border disabled:opacity-40"
          >
            Anterior
          </button>
          <span className="text-slate-500">
            Página {page + 1} de {totalPages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
            disabled={page >= totalPages - 1}
            className="px-3 py-1 rounded border disabled:opacity-40"
          >
            Siguiente
          </button>
        </div>
      )}
    </section>
  );
}

/** Buscador de empleado para el subfiltro: escribe y elige, o "General". */
function EmployeePicker({
  tenantId,
  selected,
  onSelect,
}: {
  tenantId: number;
  selected: EmployeeListItem | null;
  onSelect: (e: EmployeeListItem | null) => void;
}) {
  const [term, setTerm] = useState("");
  const [open, setOpen] = useState(false);

  const search = useQuery({
    queryKey: ["employees-pick", tenantId, term],
    queryFn: () => api.listEmployees(tenantId, { q: term, limit: 8 }),
    enabled: tenantId > 0 && open && term.trim().length >= 2,
  });

  if (selected) {
    return (
      <div className="mt-1 flex items-center gap-2">
        <span className="px-3 py-2 border rounded-lg bg-slate-50">
          {selected.fullName}
        </span>
        <button
          onClick={() => {
            onSelect(null);
            setTerm("");
          }}
          className="text-slate-500 hover:text-slate-700 text-sm"
        >
          General
        </button>
      </div>
    );
  }

  return (
    <div className="mt-1 relative">
      <input
        value={term}
        placeholder="Todos — escribe para filtrar"
        onChange={(e) => {
          setTerm(e.target.value);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        className="block border rounded-lg px-3 py-2 w-64"
      />
      {open && term.trim().length >= 2 && (
        <ul className="absolute z-10 mt-1 w-64 bg-white border rounded-lg shadow max-h-56 overflow-auto">
          {search.isLoading && (
            <li className="px-3 py-2 text-slate-400 text-sm">Buscando…</li>
          )}
          {search.data?.items.length === 0 && (
            <li className="px-3 py-2 text-slate-400 text-sm">Sin resultados</li>
          )}
          {search.data?.items.map((emp) => (
            <li key={emp.id}>
              <button
                onClick={() => {
                  onSelect(emp);
                  setOpen(false);
                }}
                className="w-full text-left px-3 py-2 hover:bg-slate-50 text-sm"
              >
                {emp.fullName}
                <span className="text-slate-400"> · {emp.documentNumber}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
