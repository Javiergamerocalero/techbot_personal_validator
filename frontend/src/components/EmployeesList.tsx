import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, getTenantId } from "@/api/client";
import type { EmployeeListItem, EmployeeUpdatePayload } from "@/types";

const PAGE_SIZE = 50;

// Sentinel para el dropdown de tenant: representa "todos". Es
// distinto de null (que en la API significa "empleados sin nombre de
// tenant"), por eso usamos un string.
const ALL_TENANTS = "__all__" as const;

export function EmployeesList() {
  const tenantId = getTenantId();
  const qc = useQueryClient();

  const [page, setPage] = useState(0);
  const [q, setQ] = useState("");
  const [tenantFilter, setTenantFilter] = useState<string>(ALL_TENANTS);
  const [editing, setEditing] = useState<EmployeeListItem | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<EmployeeListItem | null>(
    null
  );

  const tenantsQuery = useQuery({
    queryKey: ["tenants", tenantId],
    enabled: tenantId !== null,
    queryFn: () => api.listTenants(tenantId!),
  });

  const listQuery = useQuery({
    queryKey: ["employees", tenantId, page, q, tenantFilter],
    enabled: tenantId !== null,
    queryFn: () =>
      api.listEmployees(tenantId!, {
        limit: PAGE_SIZE,
        offset: page * PAGE_SIZE,
        q: q.trim() || undefined,
        // ALL_TENANTS = no filtrar. Los otros valores (incluido "")
        // van tal cual — cadena vacía significa "sin nombre".
        tenantName:
          tenantFilter === ALL_TENANTS ? undefined : tenantFilter,
      }),
  });

  const total = listQuery.data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  const invalidateAll = () => {
    qc.invalidateQueries({ queryKey: ["employees", tenantId] });
    qc.invalidateQueries({ queryKey: ["tenants", tenantId] });
  };

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.deleteEmployee(tenantId!, id),
    onSuccess: () => {
      invalidateAll();
      setConfirmDelete(null);
    },
  });

  const updateMutation = useMutation({
    mutationFn: (args: { id: number; payload: EmployeeUpdatePayload }) =>
      api.updateEmployee(tenantId!, args.id, args.payload),
    onSuccess: () => {
      invalidateAll();
      setEditing(null);
    },
  });

  const tenantOptions = useMemo(
    () => tenantsQuery.data?.items ?? [],
    [tenantsQuery.data]
  );

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <h2 className="text-xl font-semibold text-slate-800">
          Empleados cargados
        </h2>
        <div className="flex flex-col gap-2 md:flex-row md:items-center">
          <select
            value={tenantFilter}
            onChange={(e) => {
              setTenantFilter(e.target.value);
              setPage(0);
            }}
            className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            title="Filtrar por tenant"
          >
            <option value={ALL_TENANTS}>Todos los tenants</option>
            {tenantOptions.map((t) => {
              const value = t.tenantName ?? "";
              const label =
                t.tenantName === null || t.tenantName === ""
                  ? `Sin nombre (${t.count})`
                  : `${t.tenantName} (${t.count})`;
              return (
                <option key={value || "__null__"} value={value}>
                  {label}
                </option>
              );
            })}
          </select>
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
      </div>

      <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-slate-600 uppercase text-xs">
            <tr>
              <Th>Código</Th>
              <Th>Documento</Th>
              <Th>Nombre</Th>
              <Th>Tenant</Th>
              <Th>Estado</Th>
              <Th>Motivo</Th>
              <Th className="text-right">Acciones</Th>
            </tr>
          </thead>
          <tbody>
            {listQuery.isLoading && (
              <tr>
                <td colSpan={7} className="py-10 text-center text-slate-400">
                  Cargando…
                </td>
              </tr>
            )}
            {!listQuery.isLoading &&
              (listQuery.data?.items.length ?? 0) === 0 && (
                <tr>
                  <td
                    colSpan={7}
                    className="py-10 text-center text-slate-400"
                  >
                    No hay empleados que coincidan con los filtros.
                  </td>
                </tr>
              )}
            {listQuery.data?.items.map((e) => {
              const active = (e.status || "").toLowerCase() === "active";
              return (
                <tr key={e.id} className="border-t border-slate-100">
                  <Td mono>{e.employeeCode}</Td>
                  <Td mono>{e.documentNumber}</Td>
                  <Td>{e.fullName}</Td>
                  <Td>{e.tenantName ?? "—"}</Td>
                  <Td>
                    <span
                      className={
                        active
                          ? "rounded-full bg-emerald-100 text-emerald-800 px-2 py-0.5 text-xs font-medium"
                          : "rounded-full bg-red-100 text-red-800 px-2 py-0.5 text-xs font-medium"
                      }
                    >
                      {e.status.toUpperCase()}
                    </span>
                  </Td>
                  <Td>
                    <span className="text-slate-500">
                      {e.statusReason ?? "—"}
                    </span>
                  </Td>
                  <Td className="text-right">
                    <div className="flex justify-end gap-1">
                      <button
                        onClick={() => setEditing(e)}
                        className="rounded border border-slate-300 px-2 py-0.5 text-xs text-slate-700 hover:bg-slate-100"
                        title="Editar"
                      >
                        Editar
                      </button>
                      <button
                        onClick={() => setConfirmDelete(e)}
                        className="rounded border border-red-300 px-2 py-0.5 text-xs text-red-700 hover:bg-red-50"
                        title="Eliminar"
                      >
                        Eliminar
                      </button>
                    </div>
                  </Td>
                </tr>
              );
            })}
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

      {editing && (
        <EditModal
          employee={editing}
          onClose={() => setEditing(null)}
          onSubmit={(payload) =>
            updateMutation.mutate({ id: editing.id, payload })
          }
          submitting={updateMutation.isPending}
          errorMessage={
            updateMutation.error instanceof Error
              ? updateMutation.error.message
              : null
          }
        />
      )}

      {confirmDelete && (
        <ConfirmDeleteModal
          employee={confirmDelete}
          onCancel={() => setConfirmDelete(null)}
          onConfirm={() => deleteMutation.mutate(confirmDelete.id)}
          deleting={deleteMutation.isPending}
          errorMessage={
            deleteMutation.error instanceof Error
              ? deleteMutation.error.message
              : null
          }
        />
      )}
    </div>
  );
}

const Th = ({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) => (
  <th className={`text-left px-4 py-2 font-medium ${className}`}>
    {children}
  </th>
);

const Td = ({
  children,
  mono = false,
  className = "",
}: {
  children: React.ReactNode;
  mono?: boolean;
  className?: string;
}) => (
  <td
    className={`px-4 py-2 ${mono ? "font-mono text-slate-700" : ""} ${className}`}
  >
    {children}
  </td>
);

// ── Modal de edición ────────────────────────────────────────────────

interface EditModalProps {
  employee: EmployeeListItem;
  onClose: () => void;
  onSubmit: (payload: EmployeeUpdatePayload) => void;
  submitting: boolean;
  errorMessage: string | null;
}

function EditModal({
  employee,
  onClose,
  onSubmit,
  submitting,
  errorMessage,
}: EditModalProps) {
  const [form, setForm] = useState({
    employeeCode: employee.employeeCode,
    documentNumber: employee.documentNumber,
    documentType: employee.documentType,
    fullName: employee.fullName,
    status: (employee.status || "").toLowerCase() === "active"
      ? "Active"
      : "Inactive",
    statusReason: employee.statusReason ?? "",
    tenantName: employee.tenantName ?? "",
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Solo mandamos campos que cambiaron respecto al original — así
    // el PATCH del backend actualiza únicamente lo tocado y evitamos
    // sobrescribir columnas con valores idénticos.
    const changes: EmployeeUpdatePayload = {};
    if (form.employeeCode !== employee.employeeCode)
      changes.employeeCode = form.employeeCode.trim();
    if (form.documentNumber !== employee.documentNumber)
      changes.documentNumber = form.documentNumber.trim();
    if (form.documentType !== employee.documentType)
      changes.documentType = form.documentType;
    if (form.fullName !== employee.fullName)
      changes.fullName = form.fullName.trim();
    if (
      form.status.toLowerCase() !== (employee.status || "").toLowerCase()
    )
      changes.status = form.status;
    if ((form.statusReason || null) !== (employee.statusReason || null))
      changes.statusReason = form.statusReason.trim() || null;
    if ((form.tenantName || null) !== (employee.tenantName || null))
      changes.tenantName = form.tenantName.trim() || null;

    if (Object.keys(changes).length === 0) {
      onClose();
      return;
    }
    onSubmit(changes);
  };

  return (
    <ModalShell onClose={submitting ? () => {} : onClose} title="Editar empleado">
      <form onSubmit={handleSubmit} className="space-y-3">
        <Field label="Código de empleado">
          <input
            value={form.employeeCode}
            onChange={(e) => setForm({ ...form, employeeCode: e.target.value })}
            className="input"
            required
          />
        </Field>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Tipo de documento">
            <select
              value={form.documentType}
              onChange={(e) =>
                setForm({ ...form, documentType: e.target.value })
              }
              className="input"
            >
              <option value="DNI">DNI</option>
              <option value="CE">CE</option>
              <option value="PASSPORT">PASSPORT</option>
            </select>
          </Field>
          <Field label="Número de documento">
            <input
              value={form.documentNumber}
              onChange={(e) =>
                setForm({ ...form, documentNumber: e.target.value })
              }
              className="input"
              required
            />
          </Field>
        </div>
        <Field label="Nombre completo">
          <input
            value={form.fullName}
            onChange={(e) => setForm({ ...form, fullName: e.target.value })}
            className="input"
            required
          />
        </Field>
        <Field label="Tenant">
          <input
            value={form.tenantName}
            onChange={(e) =>
              setForm({ ...form, tenantName: e.target.value })
            }
            className="input"
            placeholder="Ej. San Fernando"
          />
        </Field>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Estado">
            <select
              value={form.status}
              onChange={(e) => setForm({ ...form, status: e.target.value })}
              className="input"
            >
              <option value="Active">Active</option>
              <option value="Inactive">Inactive</option>
            </select>
          </Field>
          <Field label="Motivo (opcional)">
            <input
              value={form.statusReason}
              onChange={(e) =>
                setForm({ ...form, statusReason: e.target.value })
              }
              className="input"
              placeholder="Ej. Vacaciones"
            />
          </Field>
        </div>

        {errorMessage && (
          <p className="rounded bg-red-50 px-3 py-2 text-sm text-red-700">
            {errorMessage}
          </p>
        )}

        <div className="flex justify-end gap-2 pt-2">
          <button
            type="button"
            onClick={onClose}
            disabled={submitting}
            className="rounded border border-slate-300 px-4 py-1.5 text-sm text-slate-700 hover:bg-slate-100 disabled:opacity-40"
          >
            Cancelar
          </button>
          <button
            type="submit"
            disabled={submitting}
            className="rounded bg-slate-900 px-4 py-1.5 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-40"
          >
            {submitting ? "Guardando…" : "Guardar cambios"}
          </button>
        </div>
      </form>
    </ModalShell>
  );
}

// ── Confirmación de borrado ─────────────────────────────────────────

interface ConfirmDeleteModalProps {
  employee: EmployeeListItem;
  onCancel: () => void;
  onConfirm: () => void;
  deleting: boolean;
  errorMessage: string | null;
}

function ConfirmDeleteModal({
  employee,
  onCancel,
  onConfirm,
  deleting,
  errorMessage,
}: ConfirmDeleteModalProps) {
  return (
    <ModalShell
      onClose={deleting ? () => {} : onCancel}
      title="Eliminar empleado"
    >
      <p className="text-sm text-slate-700">
        ¿Confirmás que querés eliminar a{" "}
        <span className="font-semibold">{employee.fullName}</span> ({" "}
        <span className="font-mono">{employee.employeeCode}</span> /{" "}
        <span className="font-mono">{employee.documentNumber}</span> )?
      </p>
      <p className="text-xs text-slate-500">
        La acción es inmediata y no se puede deshacer desde acá.
      </p>

      {errorMessage && (
        <p className="rounded bg-red-50 px-3 py-2 text-sm text-red-700">
          {errorMessage}
        </p>
      )}

      <div className="flex justify-end gap-2 pt-2">
        <button
          onClick={onCancel}
          disabled={deleting}
          className="rounded border border-slate-300 px-4 py-1.5 text-sm text-slate-700 hover:bg-slate-100 disabled:opacity-40"
        >
          Cancelar
        </button>
        <button
          onClick={onConfirm}
          disabled={deleting}
          className="rounded bg-red-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-40"
        >
          {deleting ? "Eliminando…" : "Eliminar"}
        </button>
      </div>
    </ModalShell>
  );
}

// ── Primitivas de modal ─────────────────────────────────────────────

function ModalShell({
  title,
  children,
  onClose,
}: {
  title: string;
  children: React.ReactNode;
  onClose: () => void;
}) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4"
      onClick={onClose}
    >
      <div
        className="w-full max-w-lg space-y-4 rounded-xl bg-white p-6 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-slate-800">{title}</h3>
          <button
            onClick={onClose}
            className="rounded p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
            aria-label="Cerrar"
          >
            ✕
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <label className="block text-sm">
      <span className="mb-1 block font-medium text-slate-700">{label}</span>
      {children}
    </label>
  );
}
