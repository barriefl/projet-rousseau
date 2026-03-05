import axios from 'axios'
import type {
  Dictation,
  Student,
  PromotionCreatePayload,
  PromotionUpdatePayload,
  GroupCreatePayload,
  GroupUpdatePayload,
  ImportExecutePayload,
  AssessmentExecuteRequest,
  StudentUpdatePayload,
  UpdateCategoryPayload,
  UpdateRulePayload,
  Category,
  Promotion,
  Group,
  ImportPreviewResponse,
  AssessmentPreviewResponse,
  StudentProgression,
  StudentCreatePayload,
  ImportSummary,
  RousseauStats,
  DictationCreatePayload,
  SubmissionCreatePayload,
  Submission,
  SubmissionDetails,
  StudentWithScores,
} from '@/types'
import type { AssessmentType, Platform } from '@/types/generated_enums'
import { useUiStore } from '@/stores/ui'

const apiClient = axios.create({
  baseURL: 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

apiClient.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    const ui = useUiStore()

    const message = error.response?.data?.message || 'Une erreur inattendue est survenue.'

    if (!error.response) {
      ui.notify('Impossible de contacter le serveur. Vérifiez votre connexion.', 'error')
    } else {
      switch (error.response.status) {
        case 400:
          ui.notify(`Données invalides : ${message}`, 'error')
          break
        case 500:
          ui.notify('Erreur interne du serveur (500).', 'error')
          break
        default:
          ui.notify(message, 'error')
      }
    }

    return Promise.reject(error)
  },
)

type ApiData<T> = Promise<T>

export default {
  // --- PROMOTIONS. ---
  /**
   * Récupère la liste de toutes les promotions enregistrées.
   * * @async
   * @returns Une promesse contenant un tableau de promotions typées.
   */
  async getPromotions(): ApiData<Promotion[]> {
    const response = await apiClient.get<Promotion[]>('/promotions/')
    return response.data
  },

  /**
   * Récupère les détails d'une promotion spécifique par son ID.
   * * @async
   * @param promotionId - L'identifiant numérique de la promotion.
   * @returns Une promesse contenant une promotion typée.
   */
  async getPromotionById(promotionId: number): ApiData<Promotion> {
    const response = await apiClient.get<Promotion>(`/promotions/${promotionId}`)
    return response.data
  },

  /**
   * Crée une nouvelle promotion (ex: "2025 - 2026").
   * * @async
   * @param data - Le payload de la promotion.
   * @returns Une promesse contenant une promotion typée.
   */
  async createPromotion(data: PromotionCreatePayload): ApiData<Promotion> {
    const response = await apiClient.post<Promotion>('/promotions/', data)
    return response.data
  },

  /**
   * Modifie les informations d'une promotion existante.
   * * @async
   * @param promotionId - L'identifiant numérique de la promotion.
   * @param data - Le payload de la promotion.
   * @returns Une promesse contenant une promotion typée.
   */
  async updatePromotion(promotionId: number, data: PromotionUpdatePayload): ApiData<Promotion> {
    const response = await apiClient.patch<Promotion>(`/promotions/${promotionId}`, data)
    return response.data
  },

  /**
   * Supprime une promotion de la base de données.
   * * @async
   * @param promotionId - L'identifiant numérique de la promotion.
   */
  async deletePromotion(promotionId: number): ApiData<void> {
    const response = await apiClient.delete<void>(`/promotions/${promotionId}`)
    return response.data
  },

  // --- GROUPES. ---
  /**
   * Liste tous les groupes (G1, G2, etc.) sans distinction de promotion.
   * * @async
   * @returns Une promesse contenant un tableau de groupes typés.
   */
  async getGroups(): ApiData<Group[]> {
    const response = await apiClient.get<Group[]>('/groups/')
    return response.data
  },

  /**
   * Récupère un groupe spécifique.
   * * @async
   * @param groupId - L'identifiant numérique du groupe.
   * @returns Une promesse contenant un groupe typé.
   */
  async getGroupById(groupId: number): ApiData<Group> {
    const response = await apiClient.get<Group>(`/groups/${groupId}`)
    return response.data
  },

  /**
   * Créer un nouveau groupe de test.
   * * @async
   * @param data - Le payload du groupe.
   * @returns Une promesse contenant un groupe typé.
   */
  async createGroup(data: GroupCreatePayload): ApiData<Group> {
    const response = await apiClient.post<Group>('/groups/', data)
    return response.data
  },

  /**
   * Met à jour les paramètres d'un groupe.
   * * @async
   * @param groupId - L'identifiant numérique du groupe.
   * @param data - Le payload du groupe.
   * @returns Une promesse contenant un groupe typé.
   */
  async updateGroup(groupId: number, data: GroupUpdatePayload): ApiData<Group> {
    const response = await apiClient.patch<Group>(`/groups/${groupId}`, data)
    return response.data
  },

  /**
   * Supprime un groupe.
   * * @async
   * @param groupId - L'identifiant numérique du groupe.
   */
  async deleteGroup(groupId: number): ApiData<void> {
    const response = await apiClient.delete<void>(`/groups/${groupId}`)
    return response.data
  },

  // --- IMPORTATION ENQUÊTE. ---
  /**
   * Envoie un fichier CSV pour prévisualiser l'importation de l'enquête des étudiants.
   * * @async
   * @param promotionId - Promotion de destination.
   * @param file - Le fichier binaire CSV.
   * @returns Une promesse contenant une réponse de preview typée.
   */
  async previewImport(promotionId: number, file: File): ApiData<ImportPreviewResponse> {
    const formData = new FormData()
    formData.append('promotion_id', promotionId.toString())
    formData.append('file', file)

    const response = await apiClient.post<ImportPreviewResponse>('/import/preview', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  },

  /**
   * Valide et exécute l'importation des étudiants analysés lors de la preview.
   * * @async
   * @param payload - Le payload de l'importation d'enquête.
   */
  async executeImport(payload: ImportExecutePayload): ApiData<ImportSummary> {
    const response = await apiClient.post<ImportSummary>('/import/execute', payload)
    return response.data
  },

  // --- IMPORTATION RÉSULTATS (VOLTAIRE / ECRI+). ---
  /**
   * Analyse un fichier de résultats (Voltaire ou Ecri+) avant importation.
   * * @async
   * @param promotionId - L'ID de la promotion concernée.
   * @param platform - La plateforme source ('Voltaire' ou 'Ecri+').
   * @param assessmentType - Le moment de l'évaluation ('Initial' ou 'Final').
   * @param file - Le fichier CSV à analyser.
   * @returns Une promesse contenant une réponse de preview typée.
   */
  async previewAssessmentImport(
    promotionId: number,
    platform: Platform,
    assessmentType: AssessmentType,
    file: File,
  ): ApiData<AssessmentPreviewResponse> {
    const formData = new FormData()
    formData.append('promotion_id', promotionId.toString())
    formData.append('platform', platform)
    formData.append('assessment_type', assessmentType)
    formData.append('file', file)

    const response = await apiClient.post<AssessmentPreviewResponse>(
      '/import/assessments/preview',
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
      },
    )
    return response.data
  },

  /**
   * Intègre définitivement les scores des outils dans la base de données.
   * * @async
   * @param payload - Le payload de l'importation des résultats.
   */
  async executeAssessmentImport(payload: AssessmentExecuteRequest): ApiData<ImportSummary> {
    const response = await apiClient.post<ImportSummary>('/import/assessments/execute', payload)
    return response.data
  },

  // --- ÉTUDIANTS. ---
  /**
   * Récupère la liste de tous les étudiants (avec leurs relations).
   * * @async
   * @returns Une promesse contenant un tableau d'étudiants typés.
   */
  async getStudents(): ApiData<Student[]> {
    const response = await apiClient.get<Student[]>('/students/')
    return response.data
  },

  async getStudentsWithScores(): ApiData<StudentWithScores[]> {
    const response = await apiClient.get<StudentWithScores[]>('/students/with-scores')
    return response.data
  },

  /**
   * Récupère le profil complet d'un étudiant.
   * * @async
   * @param studentId - L'identifiant unique universel de l'étudiant.
   * @returns Une promesse contenant un étudiant typé.
   */
  async getStudentById(studentId: string): ApiData<Student> {
    const response = await apiClient.get<Student>(`/students/${studentId}`)
    return response.data
  },

  /**
   * Ajoute manuellement un étudiant à la base.
   * * @async
   * @param studentData - Le payload de l'étudiant.
   * @returns Une promesse contenant un étudiant typé.
   */
  async createStudent(studentData: StudentCreatePayload): ApiData<Student> {
    const response = await apiClient.post<Student>('/students/', studentData)
    return response.data
  },

  /**
   * Modifie les informations ou les scores d'un étudiant.
   * * @async
   * @param id - L'identifiant unique universel de l'étudiant.
   * @param data - Le payload de l'étudiant.
   * @returns Une promesse contenant un étudiant typé.
   */
  async updateStudent(id: string, data: StudentUpdatePayload): ApiData<Student> {
    const response = await apiClient.patch<Student>(`/students/${id}`, data)
    return response.data
  },

  /**
   * Supprime un étudiant et toutes ses données associées.
   * * @async
   * @param studentId - L'identifiant unique universel numérique de l'étudiant.
   */
  async deleteStudent(studentId: string): ApiData<void> {
    const response = await apiClient.delete<void>(`/students/${studentId}`)
    return response.data
  },

  /**
   * Récupère les données brutes de progression pour le dashboard.
   * * @async
   * @returns Une promesse contenant un tableau d'étudiants typés avec leur progression.
   */
  async getStudentProgression(): ApiData<StudentProgression[]> {
    const response = await apiClient.get<StudentProgression[]>('/students/stats/progression')
    return response.data
  },

  // --- CATÉGORIES. ---
  /**
   * Récupère la liste complète des catégories et de leurs règles.
   * * @async
   * @returns Une promesse contenant un tableau de catégories typées.
   */
  async getCategories(): ApiData<Category[]> {
    const response = await apiClient.get<Category[]>('/categories')
    return response.data
  },

  /**
   * Met à jour les paramètres d'une catégorie (type ou malus).
   * * @async
   * @param categoryId - L'identifiant numérique de la catégorie.
   * @param categoryData - Le payload de la catégorie.
   */
  async updateCategory(categoryId: number, categoryData: UpdateCategoryPayload): ApiData<void> {
    const response = await apiClient.patch<void>(`/categories/${categoryId}`, categoryData)
    return response.data
  },

  // --- RÈGLES. ---
  /**
   * Active ou désactive une règle spécifique.
   * * @async
   * @param ruleId - L'identifiant numérique de la règle.
   * @param payload - Le payload de la règle.
   */
  async updateRule(ruleId: number, payload: UpdateRulePayload): ApiData<void> {
    const response = await apiClient.patch<void>(`/rules/${ruleId}`, payload)
    return response.data
  },

  // --- DICTÉES. ---
  /**
   * Déclenche le recalcul des scores des dictées.
   * * @async
   * @returns Une promesse contenant un message.
   */
  async recalculateAllDictations(): ApiData<{ message: string }> {
    const response = await apiClient.post<{ message: string }>('/dictations/recalculate')
    return response.data
  },

  // --- STATISTIQUES. ---
  /**
   * Récupère les statistiques des étudiants pour l'étude Rousseau.
   * * @async
   * @function getRousseauStats
   * @returns {Promise<RousseauStats>} Une promesse contenant des statistiques pour les graphiques.
   * @throws {AxiosError} Propage une erreur si l'appel API échoue (401, 404, 500...).
   */
  async getRousseauStats(): ApiData<RousseauStats> {
    const response = await apiClient.get<RousseauStats>('/stats/rousseau')
    return response.data
  },
  async getEmileDashboardStats() {
    const response = await apiClient.get('/stats/emile')
    return response.data
  },

  // --- DICTÉE RÉFÉRENTE. ---
  /**
   * Récupère toutes les dictées référentes.
   * * @async
   * @function getDictations
   * @returns {Promise<Dictation[]>} Une promesse contenant un tableau de dictées référentes typées.
   * @throws {AxiosError} Propage une erreur si l'appel API échoue (401, 404, 500...).
   */
  async getDictations(): ApiData<Dictation[]> {
    const response = await apiClient.get<Dictation[]>('/dictations')
    return response.data
  },

  /**
   * Créer une dictée référente.
   * * @async
   * @function createDictation
   * @param payload Le payload de création de la dictée référente (DictationCreatePayload).
   * @returns Une promesse contenant une dictée référente typée.
   * @throws {AxiosError} Propage une erreur si l'appel API échoue (401, 404, 500...).
   */
  async createDictation(payload: DictationCreatePayload): ApiData<Dictation> {
    const response = await apiClient.post<Dictation>('/dictations', payload)
    return response.data
  },

  // --- DICTÉES. ---
  async getStudentSubmissions(studentUuid: string): ApiData<Submission[]> {
    const response = await apiClient.get<Submission[]>('/submissions', {
      params: {
        student_uuid: studentUuid,
      },
    })
    return response.data
  },
  async getSubmissionDetails(submissionId: number): ApiData<SubmissionDetails> {
    const response = await apiClient.get<SubmissionDetails>(`/submissions/${submissionId}`)
    return response.data
  },
  async createBulkSubmissions(submissions: SubmissionCreatePayload[]): ApiData<Submission[]> {
    const response = await apiClient.post<Submission[]>('/submissions/bulk', submissions)
    return response.data
  },
}
