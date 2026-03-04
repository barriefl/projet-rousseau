import type { AssessmentType, MistakeType, Platform } from './generated_enums'

// --- TYPES POUR PROMOTIONS. ---
export interface Promotion {
  id: number
  name: string
}

export interface PromotionCreatePayload {
  name: string
}

export interface PromotionUpdatePayload {
  name?: string
}

// --- TYPES POUR GROUPES. ---
export interface Group {
  id: number
  name: string
  description?: string | null
}

export interface GroupCreatePayload {
  name: string
  description?: string | null
}

export interface GroupUpdatePayload {
  name?: string
  description?: string | null
}

export interface ImportExecutePayload {
  promotion_id: number
  create_missing_groups: boolean
  students: {
    csv_data: CsvRowData
    action: string
    db_student_id: number | null
  }[]
}

// --- TYPES POUR IMPORT DE CSV (ENQUÊTE). ---
export interface CsvRowData {
  first_name: string
  last_name: string
  group_name?: string
  appetence_level?: string
  reading_works?: string
  motive?: string
  reading_support?: string
  declared_level?: string
  parent_1_degree?: string
  parent_2_degree?: string
  parent_1_csp?: string
  parent_2_csp?: string
  has_library?: string
}

export interface StudentMatchPreview {
  csv_data: CsvRowData
  match_type: string
  db_student_id?: number | null
  db_first_name?: string | null
  db_last_name?: string | null
  user_choice?: string
}

export interface ImportPreviewResponse {
  promotion_id: number
  groups_to_create: string[]
  exact_matches: StudentMatchPreview[]
  fuzzy_matches: StudentMatchPreview[]
  new_students: StudentMatchPreview[]
}

// --- TYPES POUR L'IMPORT DES RÉSULTATS (ÉVALUATIONS). ---
export interface AssessmentMatchPreview {
  csv_nom: string
  csv_prenom: string
  db_student_id?: number | null
  db_first_name?: string | null
  db_last_name?: string | null
  match_type: 'exact' | 'fuzzy' | 'not_found'
  score: number
  details: Record<string, unknown>
  user_validated?: boolean
}

export interface AssessmentPreviewResponse {
  platform: Platform
  assessment_type: AssessmentType
  matched_results: AssessmentMatchPreview[]
  unmatched_results: AssessmentMatchPreview[]
}

export interface AssessmentExecuteAction {
  student_id: number
  score: number
  details: Record<string, unknown>
}

export interface AssessmentExecuteRequest {
  platform: Platform
  assessment_type: AssessmentType
  results: AssessmentExecuteAction[]
}

// --- TYPES POUR LES ÉTUDIANTS. ---
export interface Student {
  id: string
  first_name: string
  last_name: string

  promotion_id?: number | null
  group_id?: number | null
  promotion_name?: string | null
  group_name?: string | null

  appetence_level?: string | null
  has_library?: string | null
  reading_support?: string | null
  reading_works?: string | null
  motive?: string | null
  parent_1_degree?: string | null
  parent_1_csp?: string | null
  parent_2_degree?: string | null
  parent_2_csp?: string | null
  declared_level?: string | null
}

export interface StudentCreatePayload {
  first_name: string
  last_name: string
  promotion_id?: number | null
  group_id?: number | null
  appetence_level?: string | null
  has_library?: string | null
  reading_support?: string | null
  reading_works?: string | null
  motive?: string | null
  parent_1_degree?: string | null
  parent_1_csp?: string | null
  parent_2_degree?: string | null
  parent_2_csp?: string | null
  declared_level?: string | null
}

export interface StudentUpdatePayload {
  id: string
  first_name?: string
  last_name?: string
  promotion_id?: number | null
  group_id?: number | null
  appetence_level?: string | null
  has_library?: string | null
  reading_support?: string | null
  reading_works?: string | null
  motive?: string | null
  parent_1_degree?: string | null
  parent_1_csp?: string | null
  parent_2_degree?: string | null
  parent_2_csp?: string | null
  declared_level?: string | null
}

export interface StudentProgression {
  id: string
  first_name: string
  last_name: string
  group_name?: string | null
  score_initial?: number | null
  score_final?: number | null
  progress?: number | null
}

// --- TYPES POUR LA PAGE DE CORRECTION. ---

export interface Mistake {
  id?: number
  student_word: string
  correct_word: string
  position_index: number
  length: number
  category_id: number | null
  type_rousseau: 'D' | 'S' | 'R' | 'A'
  malus_applied: number
  rule_id_lt: string
  message: string
}

export interface SubmissionDetails {
  id: number
  html_text: string
  final_score: number
  mistakes: {
    id?: number | undefined
    student_word: string
    correct_word: string
    position_index: number
    length: number
    category_id: number | null
    type_rousseau: MistakeType
    malus_applied: number
    rule_id_lt: string
    message: string
  }[]
  scores: Record<string, number>
}

export interface StudentSubmission {
  id: number
  assessment_type: string
  created_at: string
}

// --- TYPES POUR LA PAGE DE CATÉGORIES & RÈGLES. ---

export interface Category {
  id: number
  lt_category_id: string
  name: string
  type_rousseau: MistakeType
  penalty: number
  rules: Rule[]
}

export interface Rule {
  id: number
  lt_rule_id: string
  description: string
  is_active: boolean
  category_id: number | null
  category?: Category
}

export interface UpdateCategoryPayload {
  type_rousseau?: 'Dessin' | 'Règle' | 'Sens' | 'Autre'
  penalty?: number
}

export interface UpdateRulePayload {
  is_active: boolean
}

// --- TYPES POUR L'ÉTUDE ROUSSEAU. ---
export interface H1Summary {
  labels: string[]
  dictation_initial: number[]
  dictation_final: number[]
  tools_initial: number[]
  tools_final: number[]
  effectif: number[]
}

export interface H2Equivalence {
  labels: string[]
  g2_final: number[]
  g2_progress: number[]
  g5_final: number[]
  g5_progress: number[]
  effectif: number[]
}

export interface TeacherStat {
  score: number
  effectif: number
}

export interface H4DataPoint {
  Initial: number
  Progress: number
  Effectif: number
}

export interface RousseauStats {
  h1_summary: H1Summary
  h2_equivalence: H2Equivalence
  h3_teacher: Record<string, TeacherStat>
  h4_sociocultural: Record<string, Record<string, Record<string, H4DataPoint>>>
}

export interface CustomDataset {
  effectifData?: number[];
  useScaling?: boolean;
  maxEffectif?: number;
};

export interface CustomBarElement {
  _originalHeight?: number;
  height: number;
};

// --- TYPES POUR LES DICTÉES RÉFÉRENTES. ---
export interface DictationCreatePayload {
  title: string
  content_reference: string
}

export interface Dictation {
  id: number
  title: string
  content_reference: string
}

// --- TYPES POUR LES DICTÉES. ---
export interface SubmissionCreatePayload {
  student_id: string
  dictation_id: number
  assessment_type: AssessmentType
  content_student: string
}

export interface Submission {
  id: number
  created_at: string
  assessment_type: AssessmentType
}

// --- AUTRE. ---
export interface ImportSummary {
  created: number
  updated: number
  message?: string
}