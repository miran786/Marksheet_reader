import axios from 'axios';
import type {
  DashboardStats,
  MarksheetResponse,
  StudentListResponse,
  MappingRuleResponse,
  StandardSubject,
  MarkResponse,
  UploadResponse,
  BatchStatusResponse,
} from '../types';

const TOKEN_KEY = 'auth_token';

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
});

// Request interceptor: attach JWT token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor: redirect to login on 401
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (
      error.response?.status === 401 &&
      !error.config?.url?.includes('/auth/')
    ) {
      localStorage.removeItem(TOKEN_KEY);
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Dashboard
export const getDashboardStats = () =>
  api.get<DashboardStats>('/dashboard/stats').then(r => r.data);

// Upload
export const uploadSingle = (file: File) => {
  const form = new FormData();
  form.append('file', file);
  return api.post<UploadResponse>('/upload/single', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then(r => r.data);
};

export const uploadBulk = (files: File[]) => {
  const form = new FormData();
  files.forEach(f => form.append('files', f));
  return api.post<BatchStatusResponse>('/upload/bulk', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then(r => r.data);
};

export const getBatchStatus = (batchId: number) =>
  api.get<BatchStatusResponse>(`/upload/batch/${batchId}`).then(r => r.data);

// Marksheets
export const getMarksheets = (params?: { page?: number; page_size?: number; status?: string }) =>
  api.get<MarksheetResponse[]>('/marksheets', { params }).then(r => r.data);

export const getMarksheet = (id: number) =>
  api.get<MarksheetResponse>(`/marksheets/${id}`).then(r => r.data);

export const updateMark = (marksheetId: number, markId: number, data: Record<string, unknown>) =>
  api.put<MarkResponse>(`/marksheets/${marksheetId}/marks/${markId}`, data).then(r => r.data);

export const verifyMarksheet = (id: number) =>
  api.post(`/marksheets/${id}/verify`).then(r => r.data);

export const deleteMarksheet = (id: number) =>
  api.delete(`/marksheets/${id}`).then(r => r.data);

// Students
export const getStudents = (params?: { page?: number; page_size?: number; search?: string; board_id?: number }) =>
  api.get<StudentListResponse>('/students', { params }).then(r => r.data);

export const getStudent = (id: number) =>
  api.get('/students/' + id).then(r => r.data);

// Mappings
export const getMappings = (boardId?: number) =>
  api.get<MappingRuleResponse[]>('/mappings', { params: boardId ? { board_id: boardId } : {} }).then(r => r.data);

export const createMapping = (data: { raw_text: string; standard_subject_id: number; board_id?: number }) =>
  api.post<MappingRuleResponse>('/mappings', data).then(r => r.data);

export const deleteMapping = (id: number) =>
  api.delete(`/mappings/${id}`).then(r => r.data);

export const getUnresolved = () =>
  api.get<MarkResponse[]>('/mappings/unresolved').then(r => r.data);

export const resolveMapping = (markId: number, standardSubjectId: number) =>
  api.post<MarkResponse>(`/mappings/resolve/${markId}`, { standard_subject_id: standardSubjectId }).then(r => r.data);

// Subjects
export const getSubjects = () =>
  api.get<StandardSubject[]>('/mappings/subjects').then(r => r.data);

export const createSubject = (data: { name: string; code: string; category?: string }) =>
  api.post<StandardSubject>('/mappings/subjects', data).then(r => r.data);

// ERP
export const exportCSV = () =>
  api.get('/erp/export/csv', { responseType: 'blob' }).then(r => r.data);

export default api;
