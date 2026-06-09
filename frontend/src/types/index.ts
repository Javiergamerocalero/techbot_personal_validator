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
  employeeCode: string;
  documentNumber: string;
  documentType: string;
  fullName: string;
  status: boolean;
  statusReason: string;
  costCenter: string | null;
  updatedAt: string;
}

export interface EmployeeListResponse {
  total: number;
  items: EmployeeListItem[];
}
