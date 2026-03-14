import axios from "axios";
import type {
  StorageBox,
  BoxListResponse,
  BoxItem,
  BoxItemListResponse,
  AuditLogResponse,
  Tag,
  SearchResult,
  TransferRequest,
  ReportRequest,
  BoxGroup,
  GroupListResponse,
} from "@/types";

const api = axios.create({
  baseURL: "/api/v1",
});

// Request interceptor to attach auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("auth_token");
    if (token) {
      config.headers = config.headers ?? {};
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle 401 errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Redirect to login on 401
      localStorage.removeItem("auth_token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

// Boxes
export const listBoxes = (params?: {
  page?: number;
  page_size?: number;
  sort?: string;
  lat?: number;
  lng?: number;
  group_id?: number;
}) => api.get<BoxListResponse>("/boxes", { params });

export const getBox = (id: number) => api.get<StorageBox>(`/boxes/${id}`);

export const getBoxByCode = (code: string) =>
  api.get<StorageBox>(`/boxes/code/${code}`);

export const createBox = (data: { name: string; location?: { latitude: number; longitude: number } | null; location_name?: string | null; group_id?: number | null }) =>
  api.post<StorageBox>("/boxes", data);

export const updateBox = (id: number, data: { name?: string; location?: { latitude: number; longitude: number } | null; location_name?: string | null; group_id?: number | null }) =>
  api.put<StorageBox>(`/boxes/${id}`, data);

export const deleteBox = (id: number) => api.delete(`/boxes/${id}`);

// Items
export const listItems = (boxId: number, params?: { page?: number; page_size?: number }) =>
  api.get<BoxItemListResponse>(`/boxes/${boxId}/items`, { params });

export const addItem = (boxId: number, data: { name: string; quantity: number; tags: string[] }) =>
  api.post<BoxItem>(`/boxes/${boxId}/items`, data);

export const updateItem = (boxId: number, itemId: number, data: { quantity?: number; tags?: string[] }) =>
  api.put<BoxItem>(`/boxes/${boxId}/items/${itemId}`, data);

export const removeItem = (boxId: number, itemId: number) =>
  api.delete(`/boxes/${boxId}/items/${itemId}`);

// Transfers
export const transferItem = (data: TransferRequest) =>
  api.post("/transfers", data);

// Search
export const search = (q: string) =>
  api.get<SearchResult>("/search", { params: { q } });

export const autocompleteItems = (q: string) =>
  api.get<{ id: number; name: string }[]>("/search/autocomplete/items", { params: { q } });

// Tags
export const listTags = () => api.get<Tag[]>("/tags");

export const createTag = (name: string) => api.post<Tag>("/tags", { name });

// Reports
export const generateReport = (data: ReportRequest) =>
  api.post("/reports", data, {
    responseType: data.format === "html" || data.format === "text" ? "text" : "blob",
  });

// Audit Log
export const getAuditLog = (boxId: number, params?: { page?: number; page_size?: number }) =>
  api.get<AuditLogResponse>(`/boxes/${boxId}/audit-log`, { params });

// Config
export const getConfig = () => api.get<{ base_url: string }>("/config");

// Groups
export const listGroups = () => api.get<GroupListResponse>("/groups");

export const createGroup = (data: { name: string; latitude?: number; longitude?: number }) =>
  api.post<BoxGroup>("/groups", data);

export const updateGroup = (id: number, data: { name?: string; latitude?: number; longitude?: number }) =>
  api.put<BoxGroup>(`/groups/${id}`, data);

export const deleteGroup = (id: number) => api.delete(`/groups/${id}`);

export default api;
