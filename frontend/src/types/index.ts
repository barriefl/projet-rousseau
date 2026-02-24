export enum AssessmentType {
  INITIAL = "INITIAL",
  FINAL = "FINAL"
}

export interface Mistake {
    id?: number
    student_word: string;
    correct_word: string;
    position_index: number;
    length: number;
    category_code: string;
    type_rousseau: 'D' | 'S' | 'R' | 'A';
    malus_applied: number;
    rule_id_lt: string;
    message: string;
}

export interface Submission {
    id: number;
    created_at: string;
    final_score: number;
    scores: Record<string, number>;
    content_student?: string;
    mistakes: Mistake[];
}

export interface SubmissionCreate {
  student_uuid: string;
  dictation_id: number;
  content_student: string;
  assessment_type: AssessmentType | string;
}

export interface CorrectionPayload {
    student_id: number;
    dictation_id: number;
    assessment_type: string;
    content_student: string;
}

export interface Student {
    id: string;
    first_name: string;
    last_name: string;
    promo: string;
    group: string;
}

export interface StudentCreate {
  first_name: string;
  last_name: string;
  promo?: string;
  group?: string;
}

export interface Dictation {
  id: number;
  title: string;
  content_reference: string;
  rules_config?: Record<string, number>;
}

export interface GradingScale {
  id: number;
  code: string;
  name: string;
  type_rousseau: string;
  penalty: number;
  lt_rule_patterns: string | null;
}

export interface StudentProgression {
  id: string;
  first_name: string;
  last_name: string;
  group: string | null;
  score_initial: number | null;
  score_final: number | null;
  progress: number | null;
}