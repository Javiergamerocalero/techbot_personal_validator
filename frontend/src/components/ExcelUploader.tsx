import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { useMutation } from "@tanstack/react-query";
import { api, getTenantId } from "@/api/client";
import type { ImportSummary } from "@/types";

interface Props {
  onImported: () => void;
}

export function ExcelUploader({ onImported }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<ImportSummary | null>(null);

  const onDrop = useCallback((accepted: File[]) => {
    setResult(null);
    setFile(accepted[0] ?? null);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [
        ".xlsx",
      ],
    },
    maxFiles: 1,
  });

  const importMutation = useMutation({
    mutationFn: () => {
      const tid = getTenantId();
      if (!tid) throw new Error("tenant_id no configurado");
      return api.importEmployees(file!, tid);
    },
    onSuccess: (summary) => {
      setResult(summary);
      if (summary.failed === 0) onImported();
    },
  });

  const downloadTemplate = async () => {
    const blob = await api.downloadTemplate();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "empleados_plantilla.xlsx";
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold text-slate-800">
            Cargar empleados
          </h2>
          <p className="text-sm text-slate-500">
            Tenant actual: <strong>{getTenantId()}</strong>. Descargá la
            plantilla, completala con tus colaboradores y subila acá.
          </p>
        </div>
        <button
          onClick={downloadTemplate}
          className="shrink-0 rounded-lg bg-slate-800 hover:bg-slate-900 text-white text-sm font-semibold px-4 py-2"
        >
          Descargar plantilla
        </button>
      </div>

      <div
        {...getRootProps()}
        className={`rounded-2xl border-2 border-dashed p-12 text-center cursor-pointer transition ${
          isDragActive
            ? "border-indigo-500 bg-indigo-50"
            : "border-slate-300 bg-white hover:border-slate-400"
        }`}
      >
        <input {...getInputProps()} />
        {file ? (
          <p className="text-slate-700">
            <span className="font-semibold">{file.name}</span>{" "}
            <span className="text-slate-400">
              ({(file.size / 1024).toFixed(1)} KB)
            </span>
          </p>
        ) : (
          <p className="text-slate-500">
            Arrastrá un archivo <code>.xlsx</code> acá, o tocá para elegir
            uno.
          </p>
        )}
      </div>

      {file && !result && (
        <div className="flex justify-end gap-2">
          <button
            onClick={() => setFile(null)}
            className="rounded-lg border border-slate-300 px-4 py-2 text-sm hover:bg-slate-50"
          >
            Quitar
          </button>
          <button
            onClick={() => importMutation.mutate()}
            disabled={importMutation.isPending}
            className="rounded-lg bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 text-white text-sm font-semibold px-5 py-2"
          >
            {importMutation.isPending ? "Subiendo…" : "Confirmar carga"}
          </button>
        </div>
      )}

      {importMutation.isError && (
        <div className="rounded-lg bg-red-50 border border-red-200 text-red-800 p-4 text-sm">
          Error subiendo el archivo: {(importMutation.error as Error).message}
        </div>
      )}

      {result && <ImportSummaryView summary={result} />}
    </div>
  );
}

function ImportSummaryView({ summary }: { summary: ImportSummary }) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Stat label="Recibidas" value={summary.received} />
        <Stat label="Insertadas" value={summary.inserted} tone="ok" />
        <Stat label="Actualizadas" value={summary.updated} tone="info" />
        <Stat
          label="Con error"
          value={summary.failed}
          tone={summary.failed ? "warn" : "muted"}
        />
      </div>
      {summary.errors.length > 0 && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-4">
          <h3 className="font-semibold text-amber-900 mb-2">
            Filas que no se importaron
          </h3>
          <div className="max-h-64 overflow-auto">
            <table className="w-full text-sm">
              <thead className="text-amber-900 sticky top-0 bg-amber-50">
                <tr className="text-left">
                  <th className="py-1">Fila</th>
                  <th className="py-1">Columna</th>
                  <th className="py-1">Motivo</th>
                </tr>
              </thead>
              <tbody>
                {summary.errors.map((e, i) => (
                  <tr key={i} className="border-t border-amber-100">
                    <td className="py-1 pr-2">{e.row}</td>
                    <td className="py-1 pr-2 font-mono">
                      {e.column ?? "—"}
                    </td>
                    <td className="py-1">{e.reason}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

function Stat({
  label,
  value,
  tone = "muted",
}: {
  label: string;
  value: number;
  tone?: "ok" | "info" | "warn" | "muted";
}) {
  const colors: Record<typeof tone, string> = {
    ok: "bg-emerald-50 text-emerald-900 border-emerald-200",
    info: "bg-blue-50 text-blue-900 border-blue-200",
    warn: "bg-amber-50 text-amber-900 border-amber-200",
    muted: "bg-slate-50 text-slate-800 border-slate-200",
  };
  return (
    <div className={`rounded-xl border p-4 ${colors[tone]}`}>
      <div className="text-2xl font-bold">{value}</div>
      <div className="text-xs uppercase tracking-wide">{label}</div>
    </div>
  );
}
