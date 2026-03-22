export type MeResponse = {
  user_id: string;
  email: string;
  full_name: string;
  roles: string[];
};

export type PatientResponse = {
  id: string;
  patient_id: string;
  hospital_number: string;
  full_name: string;
  date_of_birth: string;
  sex: "female" | "male" | "other";
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export type PatientListResponse = {
  page: number;
  page_size: number;
  total: number;
  items: PatientResponse[];
};

export type PatientCreateRequest = {
  patient_id: string;
  hospital_number: string;
  full_name: string;
  date_of_birth: string;
  sex: "female" | "male" | "other";
  notes?: string | null;
};

export type AnalysisCreateResponse = {
  analysis_id: string;
};

export type AnalysisItem = {
  id: string;
  status: string;
  exam_date: string | null;
  erosion_probability: number | null;
  predicted_class: number | null;
  model_version: string | null;
  created_at: string;
  latest_review_status: string | null;
  latest_review_decision: string | null;
  latest_review_signed_at: string | null;
};

export type AnalysisListResponse = {
  patient_id: string;
  items: AnalysisItem[];
};

export type ReviewResponse = {
  id: string;
  analysis_id: string;
  patient_id: string;
  reviewer_user_id: string;
  status: "DRAFT" | "FINAL";
  decision: "CONFIRMED" | "NOT_CONFIRMED" | "UNCERTAIN" | null;
  structured_note: Record<string, unknown>;
  free_text: string | null;
  version: number;
  is_current: boolean;
  signed_at: string | null;
  created_at: string;
};

export type AnalysisDetailResponse = {
  id: string;
  status: string;
  patient: {
    id: string;
    patient_id: string;
    full_name: string;
  } | null;
  exam: {
    id: string;
    exam_date: string;
  } | null;
  erosion_probability: number | null;
  threshold: number | null;
  predicted_class: number | null;
  model_version: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  roi_image_id: string | null;
  full_image_id: string | null;
  roi_selection_id: string | null;
  error_message: string | null;
  metadata: Record<string, unknown>;
  latest_review: ReviewResponse | null;
};

export type ReviewCreateRequest = {
  decision: "CONFIRMED" | "NOT_CONFIRMED" | "UNCERTAIN";
  structured_note: Record<string, unknown>;
  free_text?: string | null;
};