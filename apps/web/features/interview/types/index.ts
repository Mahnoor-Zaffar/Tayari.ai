export interface OptionItem {
  value: string;
  label: string;
}

export interface InterviewOptions {
  interview_types: OptionItem[];
  companies: string[];
  roles: string[];
  languages: OptionItem[];
  frameworks: OptionItem[];
  experience_levels: OptionItem[];
  difficulties: OptionItem[];
  durations: OptionItem[];
}

export interface ResumeUploadResult {
  id: string;
  original_filename: string;
  mime_type: string;
  file_size: number;
  file_hash: string;
  created_at: string;
}

export interface JobDescriptionUploadResult {
  id: string;
  source: string;
  original_filename: string;
  created_at: string;
}

export interface DeviceCheckResult {
  microphone: boolean;
  camera: boolean;
  speaker: boolean;
  browser: boolean;
  all_passed: boolean;
}

export interface InterviewResponse {
  id: string;
  type: string;
  company: string;
  role: string;
  experience_level: string;
  language: string | null;
  spoken_language: string | null;
  framework: string | null;
  difficulty: string;
  duration_minutes: number;
  custom_instructions: string | null;
  status: string;
  timer_remaining: number;
  resume_id: string | null;
  job_description_id: string | null;
  template_id: string | null;
  created_at: string;
}
