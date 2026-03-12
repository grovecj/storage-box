export interface Location {
  latitude: number;
  longitude: number;
}

export interface StorageBox {
  id: number;
  box_code: string;
  name: string;
  latitude: number | null;
  longitude: number | null;
  location_name: string | null;
  item_count: number;
  created_at: string;
  updated_at: string;
  created_by: number | null;
  updated_by: number | null;
}

export interface BoxListResponse {
  boxes: StorageBox[];
  total: number;
  page: number;
  page_size: number;
}

export interface BoxItem {
  id: number;
  item_id: number;
  name: string;
  quantity: number;
  tags: string[];
  created_at: string;
  updated_at: string;
  created_by: number | null;
  updated_by: number | null;
}

export interface BoxItemListResponse {
  items: BoxItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface AuditLogEntry {
  id: number;
  action: string;
  details: Record<string, unknown>;
  created_at: string;
}

export interface AuditLogResponse {
  logs: AuditLogEntry[];
  total: number;
  page: number;
  page_size: number;
}

export interface Tag {
  id: number;
  name: string;
}

export interface SearchResult {
  boxes: SearchBoxResult[];
  items: SearchItemResult[];
}

export interface SearchBoxResult {
  id: number;
  box_code: string;
  name: string;
  latitude: number | null;
  longitude: number | null;
  item_count: number;
  match_type: string;
}

export interface SearchItemResult {
  id: number;
  item_id: number;
  name: string;
  quantity: number;
  tags: string[];
  box_id: number;
  box_code: string;
  box_name: string;
}

export interface TransferRequest {
  from_box_id: number;
  to_box_id: number;
  item_id: number;
  quantity: number;
}

export interface ReportRequest {
  box_ids?: number[] | null;
  tag_filter: string[];
  location_filter?: string;
  format: "html" | "pdf" | "csv" | "text";
}
