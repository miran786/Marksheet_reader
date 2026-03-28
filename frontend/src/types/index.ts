export interface DashboardStats {
  total_students: number;
  total_marksheets: number;
  pending_review: number;
  completed: number;
  failed: number;
  total_boards: number;
  total_subjects: number;
  unresolved_mappings: number;
}

export interface MarkResponse {
  id: number;
  raw_subject_name: string;
  standard_subject_id: number | null;
  standard_subject_name: string | null;
  mapping_confidence: number | null;
  marks_obtained: number | null;
  max_marks: number | null;
  grade: string | null;
  is_verified: boolean;
}

export interface MarksheetResponse {
  id: number;
  student_id: number | null;
  student_name: string | null;
  file_name: string;
  file_url: string | null;
  file_type: string;
  processing_status: string;
  confidence_score: number | null;
  board_detected_id: number | null;
  board_name: string | null;
  uploaded_at: string;
  processed_at: string | null;
  reviewed_by: string | null;
  marks: MarkResponse[];
}

export interface StudentResponse {
  id: number;
  name: string;
  roll_number: string;
  board_id: number | null;
  board_name: string | null;
  exam_year: number | null;
  exam_type: string | null;
  date_of_birth: string | null;
  school_name: string | null;
  created_at: string;
  marksheet_count: number;
}

export interface StudentListResponse {
  students: StudentResponse[];
  total: number;
  page: number;
  page_size: number;
}

export interface MappingRuleResponse {
  id: number;
  raw_text: string;
  standard_subject_id: number;
  standard_subject_name: string | null;
  board_id: number | null;
  board_name: string | null;
  confidence_threshold: number;
  is_manual: boolean;
  created_at: string;
}

export interface StandardSubject {
  id: number;
  name: string;
  code: string;
  category: string | null;
}

export interface UploadResponse {
  id: number;
  file_name: string;
  processing_status: string;
  message: string;
}

export interface BatchStatusResponse {
  id: number;
  name: string | null;
  total_files: number;
  processed_count: number;
  failed_count: number;
  status: string;
  created_at: string;
  marksheets: UploadResponse[];
}
