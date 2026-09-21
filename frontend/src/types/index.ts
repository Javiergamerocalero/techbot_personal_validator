export interface ImportError {
  row: number;
  column: string | null;
  reason: string;
}

export interface ImportSummary {
  received: number;
  inserted: number;
  updated: number;
  failed: number;
  errors: ImportError[];
}

export interface EmployeeListItem {
  id: number;
  tenantId: number;
  tenantName: string | null;
  employeeCode: string;
  documentNumber: string;
  documentType: string;
  fullName: string;
  /** "Active" o "Inactive" — string libre del backend */
  status: string;
  statusReason: string | null;
  updatedAt: string;
}

export interface EmployeeListResponse {
  total: number;
  items: EmployeeListItem[];
}

export interface EmployeeUpdatePayload {
  employeeCode?: string;
  documentNumber?: string;
  documentType?: string;
  fullName?: string;
  status?: string;
  statusReason?: string | null;
  tenantName?: string | null;
}

export interface TenantSummary {
  tenantName: string | null;
  count: number;
}

export interface TenantListResponse {
  items: TenantSummary[];
}
