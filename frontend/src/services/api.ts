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
  EmileStatsResponse,
  AuthResponse,
  Tool,
  ToolCreatePayload,
  ToolUpdatePayload,
} from '@/types'
import type { AssessmentType, Platform } from '@/types/generated_enums'
import { useUiStore } from '@/stores/ui'

const apiClient = axios.create({
  baseURL: 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
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
        case 401:
          localStorage.removeItem('access_token')

          if (window.location.pathname !== '/login') {
            ui.notify('Votre session a expiré, veuillez vous reconnecter.', 'error')
            window.location.href = '/login'
          }

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
  // ==========================================
  // --- AUTH ---
  // ==========================================
  /**
   * Authentifie l'utilisateur et récupère un jeton d'accès (Token JWT).
   * Cette route respecte le standard OAuth2PasswordRequestForm attendu par FastAPI.
   * * @param {string} password - Le mot de passe administrateur (défini dans le .env du backend).
   * @returns {Promise<AuthResponse>} Un objet contenant le token JWT et son type (Bearer).
   * @throws {AxiosError} En cas d'échec (ex: 401 Unauthorized), l'erreur est propagée pour être gérée par le composant ou l'intercepteur.
   */
  async login(password: string): ApiData<AuthResponse> {
    const formData = new URLSearchParams()
    formData.append('username', 'user')
    formData.append('password', password)

    const response = await apiClient.post<AuthResponse>('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    return response.data
  },

  // ==========================================
  // --- PROMOTIONS ---
  // ==========================================

  /**
   * Récupère la liste de toutes les promotions enregistrées dans le système.
   * Cette méthode effectue une requête HTTP GET vers l'endpoint `/promotions/`.
   *
   * @async
   * @function getPromotions
   * @returns {ApiData<Promotion[]>} Une promesse contenant un tableau d'objets `Promotion`.
   * @throws {AxiosError} Propage une erreur provenant d'Axios si la requête échoue :
   * - `401/403` : Erreur d'authentification ou de permissions.
   * - `500` : Erreur interne du serveur.
   * @example
   * try {
   *   isLoadingPromotions.value = true;
   *   const promos = await api.getPromotions();
   *   promotions.value = promos;
   * } catch (error) {
   *   console.error("Erreur lors du chargement des promotions :", error);
   *   ui.notify("Impossible de charger les promotions.", "error");
   * } finally {
   *   isLoadingPromotions.value = false;
   * }
   */
  async getPromotions(): ApiData<Promotion[]> {
    const response = await apiClient.get<Promotion[]>('/promotions/')
    return response.data
  },

  /**
   * Récupère les détails d'une promotion spécifique à partir de son identifiant.
   * Cette méthode effectue une requête HTTP GET vers l'endpoint `/promotions/{id}`.
   *
   * @async
   * @function getPromotionById
   * @param {number} promotionId - L'identifiant numérique unique de la promotion (ex: 1).
   * @returns {ApiData<Promotion>} Une promesse contenant l'objet `Promotion` demandé.
   * @throws {AxiosError} Propage une erreur provenant d'Axios si la requête échoue :
   * - `404` : La promotion spécifiée n'existe pas.
   * @example
   * try {
   *    const promoData = await api.getPromotionById(12);
   *    currentPromotion.value = promoData;
   * } catch (error) {
   *    ui.notify("Promotion introuvable.", "error");
   * }
   */
  async getPromotionById(promotionId: number): ApiData<Promotion> {
    const response = await apiClient.get<Promotion>(`/promotions/${promotionId}`)
    return response.data
  },

  /**
   * Crée une nouvelle promotion dans la base de données.
   * Cette méthode effectue une requête HTTP POST vers l'endpoint `/promotions/`.
   *
   * @async
   * @function createPromotion
   * @param {PromotionCreatePayload} data - Le payload contenant les données de la nouvelle promotion (ex: le nom "2025 - 2026").
   * @returns {ApiData<Promotion>} Une promesse contenant l'objet `Promotion` nouvellement créé (avec son ID généré).
   * @throws {AxiosError} Propage une erreur provenant d'Axios si la requête échoue :
   * - `400` : Données invalides ou nom de promotion déjà existant.
   * @example
   * try {
   *    const newPromo = await api.createPromotion({ name: "2024 - 2025" });
   *    ui.notify(`La promotion ${newPromo.name} a été créée.`, "success");
   * } catch (error) {
   *    ui.notify("Échec de la création de la promotion.", "error");
   * }
   */
  async createPromotion(data: PromotionCreatePayload): ApiData<Promotion> {
    const response = await apiClient.post<Promotion>('/promotions/', data)
    return response.data
  },

  /**
   * Modifie les informations d'une promotion existante (comme son nom).
   * Cette méthode effectue une requête HTTP PATCH vers l'endpoint `/promotions/{id}`.
   *
   * @async
   * @function updatePromotion
   * @param {number} promotionId - L'identifiant numérique de la promotion à modifier.
   * @param {PromotionUpdatePayload} data - Les données à mettre à jour.
   * @returns {ApiData<Promotion>} Une promesse contenant la promotion mise à jour.
   * @throws {AxiosError} Propage une erreur si la requête échoue (400, 404, 500).
   * @example
   * try {
   *    const updatedPromo = await api.updatePromotion(5, { name: "2025 - 2026 (Modifié)" });
   *    ui.notify("Promotion mise à jour.", "success");
   * } catch (error) {
   *    ui.notify("Impossible de modifier la promotion.", "error");
   * }
   */
  async updatePromotion(promotionId: number, data: PromotionUpdatePayload): ApiData<Promotion> {
    const response = await apiClient.patch<Promotion>(`/promotions/${promotionId}`, data)
    return response.data
  },

  /**
   * Supprime définitivement une promotion de la base de données.
   * Attention : Cette action peut être bloquée ou entraîner des suppressions en cascade selon les contraintes de clés étrangères.
   *
   * @async
   * @function deletePromotion
   * @param {number} promotionId - L'identifiant numérique de la promotion à supprimer.
   * @returns {ApiData<void>} Une promesse vide se résolvant en cas de succès.
   * @throws {AxiosError} Propage une erreur si la requête échoue (ex: 409 Conflict s'il y a des étudiants liés).
   * @example
   * try {
   *    await api.deletePromotion(12);
   *    ui.notify("Promotion supprimée avec succès.", "success");
   * } catch (error) {
   *    ui.notify("Cette promotion ne peut pas être supprimée car elle contient des données.", "error");
   * }
   */
  async deletePromotion(promotionId: number): ApiData<void> {
    const response = await apiClient.delete<void>(`/promotions/${promotionId}`)
    return response.data
  },

  // ==========================================
  // --- OUTILS ---
  // ==========================================

  /**
   * Récupère la liste de tous les outils enregistrées dans le système.
   * Cette méthode effectue une requête HTTP GET vers l'endpoint `/tools/`.
   *
   * @async
   * @function getTools
   * @returns {ApiData<Tool[]>} Une promesse contenant un tableau d'objets `Tool`.
   * @throws {AxiosError} Propage une erreur provenant d'Axios si la requête échoue :
   * - `401/403` : Erreur d'authentification ou de permissions.
   * - `500` : Erreur interne du serveur.
   * @example
   * try {
   *   isLoadingTools.value = true;
   *   const tools = await api.getTools();
   *   tools.value = tools;
   * } catch (error) {
   *   console.error("Erreur lors du chargement des outils :", error);
   *   ui.notify("Impossible de charger les outils.", "error");
   * } finally {
   *   isLoadingTools.value = false;
   * }
   */
  async getTools(): ApiData<Tool[]> {
    const response = await apiClient.get<Tool[]>('/tools/')
    return response.data
  },

  /**
   * Récupère les détails d'un outil spécifique à partir de son identifiant.
   * Cette méthode effectue une requête HTTP GET vers l'endpoint `/tools/{id}`.
   *
   * @async
   * @function getToolById
   * @param {number} toolId - L'identifiant numérique unique de l'outil (ex: 1).
   * @returns {ApiData<Tool>} Une promesse contenant l'objet `Tool` demandé.
   * @throws {AxiosError} Propage une erreur provenant d'Axios si la requête échoue :
   * - `404` : L'outil spécifié n'existe pas.
   * @example
   * try {
   *    const toolData = await api.getToolById(12);
   *    currentTool.value = toolData;
   * } catch (error) {
   *    ui.notify("Outil introuvable.", "error");
   * }
   */
  async getToolById(toolId: number): ApiData<Tool> {
    const response = await apiClient.get<Tool>(`/tools/${toolId}`)
    return response.data
  },

  /**
   * Crée un nouvel outil dans la base de données.
   * Cette méthode effectue une requête HTTP POST vers l'endpoint `/tools/`.
   *
   * @async
   * @function createTool
   * @param {ToolCreatePayload} data - Le payload contenant les données du nouvel outil.
   * @returns {ApiData<Tool>} Une promesse contenant l'objet `Tool` nouvellement créé (avec son ID généré).
   * @throws {AxiosError} Propage une erreur provenant d'Axios si la requête échoue :
   * - `400` : Données invalides ou nom d'outil déjà existant.
   * @example
   * try {
   *    const newTool = await api.createTool({ name: "PV" });
   *    ui.notify(`L'outil ${newTool.name} a été créé.`, "success");
   * } catch (error) {
   *    ui.notify("Échec de la création de l'outil.", "error");
   * }
   */
  async createTool(data: ToolCreatePayload): ApiData<Tool> {
    const response = await apiClient.post<Tool>('/tools/', data)
    return response.data
  },

  /**
   * Modifie les informations d'un outil existant (comme son nom).
   * Cette méthode effectue une requête HTTP PATCH vers l'endpoint `/tools/{id}`.
   *
   * @async
   * @function updateTool
   * @param {number} toolId - L'identifiant numérique de l'outil à modifier.
   * @param {ToolUpdatePayload} data - Les données à mettre à jour.
   * @returns {ApiData<Tool>} Une promesse contenant l'outil mise à jour.
   * @throws {AxiosError} Propage une erreur si la requête échoue (400, 404, 500).
   * @example
   * try {
   *    const updatedTool = await api.updateTool(5, { name: "E+ (Modifié)" });
   *    ui.notify("Outil mis à jour.", "success");
   * } catch (error) {
   *    ui.notify("Impossible de modifier l'outil.", "error");
   * }
   */
  async updateTool(toolId: number, data: ToolUpdatePayload): ApiData<Tool> {
    const response = await apiClient.patch<Tool>(`/tools/${toolId}`, data)
    return response.data
  },

  /**
   * Supprime définitivement un outil de la base de données.
   * Attention : Cette action peut être bloquée ou entraîner des suppressions en cascade selon les contraintes de clés étrangères.
   *
   * @async
   * @function deleteTool
   * @param {number} toolId - L'identifiant numérique de l'outil à supprimer.
   * @returns {ApiData<void>} Une promesse vide se résolvant en cas de succès.
   * @throws {AxiosError} Propage une erreur si la requête échoue (ex: 409 Conflict s'il y a des groupes liés).
   * @example
   * try {
   *    await api.deleteTool(12);
   *    ui.notify("Outil supprimé avec succès.", "success");
   * } catch (error) {
   *    ui.notify("Cet outil ne peut pas être supprimé car elle contient des données.", "error");
   * }
   */
  async deleteTool(toolId: number): ApiData<void> {
    const response = await apiClient.delete<void>(`/tools/${toolId}`)
    return response.data
  },

  // ==========================================
  // --- GROUPES ---
  // ==========================================

  /**
   * Récupère la liste de tous les groupes existants (G1, G2, etc.) sans distinction de promotion.
   * Cette méthode effectue une requête HTTP GET vers l'endpoint `/groups/`.
   *
   * @async
   * @function getGroups
   * @returns {ApiData<Group[]>} Une promesse contenant un tableau d'objets `Group`.
   * @throws {AxiosError} Propage une erreur Axios standard (401, 500...).
   * @example
   * try {
   *    const allGroups = await api.getGroups();
   *    groupsList.value = allGroups;
   * } catch (error) {
   *    ui.notify("Erreur lors du chargement des groupes.", "error");
   * }
   */
  async getGroups(): ApiData<Group[]> {
    const response = await apiClient.get<Group[]>('/groups/')
    return response.data
  },

  /**
   * Récupère les détails d'un groupe spécifique par son identifiant.
   *
   * @async
   * @function getGroupById
   * @param {number} groupId - L'identifiant numérique du groupe (ex: 3 pour G3).
   * @returns {ApiData<Group>} Une promesse contenant le groupe demandé.
   * @throws {AxiosError} Propage une erreur si le groupe est introuvable (404).
   * @example
   * try {
   *    const groupInfo = await api.getGroupById(3);
   *    console.log("Nom du groupe :", groupInfo.name);
   * } catch (error) {
   *    console.error("Groupe non trouvé.");
   * }
   */
  async getGroupById(groupId: number): ApiData<Group> {
    const response = await apiClient.get<Group>(`/groups/${groupId}`)
    return response.data
  },

  /**
   * Crée un nouveau groupe (utile pour initialiser les groupes de test G0, G1...).
   *
   * @async
   * @function createGroup
   * @param {GroupCreatePayload} data - Le nom et éventuellement la description du nouveau groupe.
   * @returns {ApiData<Group>} Une promesse contenant le groupe créé.
   * @throws {AxiosError} Propage une erreur de validation (400) si le nom est manquant ou dupliqué.
   * @example
   * try {
   *    const newGroup = await api.createGroup({ name: "G5", description: "Groupe Écri+" });
   *    ui.notify(`Groupe ${newGroup.name} ajouté.`, "success");
   * } catch (error) {
   *    ui.notify("Erreur de création du groupe.", "error");
   * }
   */
  async createGroup(data: GroupCreatePayload): ApiData<Group> {
    const response = await apiClient.post<Group>('/groups/', data)
    return response.data
  },

  /**
   * Met à jour les informations d'un groupe existant (nom, description).
   *
   * @async
   * @function updateGroup
   * @param {number} groupId - L'identifiant du groupe à modifier.
   * @param {GroupUpdatePayload} data - Le payload des données à modifier.
   * @returns {ApiData<Group>} Une promesse contenant le groupe mis à jour.
   * @throws {AxiosError} Propage une erreur (400, 404).
   * @example
   * try {
   *    await api.updateGroup(2, { description: "Nouveau paramétrage" });
   * } catch (error) {
   *    ui.notify("Erreur de mise à jour.", "error");
   * }
   */
  async updateGroup(groupId: number, data: GroupUpdatePayload): ApiData<Group> {
    const response = await apiClient.patch<Group>(`/groups/${groupId}`, data)
    return response.data
  },

  /**
   * Supprime un groupe de la base de données.
   *
   * @async
   * @function deleteGroup
   * @param {number} groupId - L'identifiant numérique du groupe.
   * @returns {ApiData<void>}
   * @throws {AxiosError} Propage une erreur si des étudiants sont encore liés à ce groupe (409 Conflict).
   * @example
   * try {
   *    await api.deleteGroup(5);
   *    ui.notify("Groupe supprimé.", "success");
   * } catch (error) {
   *    ui.notify("Impossible de supprimer un groupe contenant des étudiants.", "error");
   * }
   */
  async deleteGroup(groupId: number): ApiData<void> {
    const response = await apiClient.delete<void>(`/groups/${groupId}`)
    return response.data
  },

  // ==========================================
  // --- IMPORTATION ENQUÊTE ---
  // ==========================================

  /**
   * Envoie un fichier CSV d'enquête pour analyse et prévisualisation côté serveur.
   * La requête utilise `multipart/form-data`. Le backend analyse le fichier, détecte les
   * correspondances exactes/floues avec les étudiants existants, et signale les groupes manquants.
   *
   * @async
   * @function previewImport
   * @param {number} promotionId - L'identifiant de la promotion cible pour ces étudiants.
   * @param {File} file - L'objet binaire du fichier CSV de l'enquête.
   * @returns {ApiData<ImportPreviewResponse>} Une promesse contenant le détail de l'analyse (matches, erreurs).
   * @throws {AxiosError} Propage une erreur si le fichier est mal formaté ou invalide (400).
   * @example
   * try {
   *    isAnalyzing.value = true;
   *    const preview = await api.previewImport(selectedPromoId.value, uploadedFile.value);
   *    previewData.value = preview; // Affiche les tableaux de correspondances
   * } catch (error) {
   *    ui.notify("Le fichier CSV est invalide ou illisible.", "error");
   * } finally {
   *    isAnalyzing.value = false;
   * }
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
   * Valide et exécute l'importation définitive des données de l'enquête, suite à la validation
   * de la prévisualisation (`previewImport`) par l'utilisateur.
   *
   * @async
   * @function executeImport
   * @param {ImportExecutePayload} payload - L'objet contenant les décisions de l'utilisateur (créer/fusionner) et les données brutes.
   * @returns {ApiData<ImportSummary>} Un résumé de l'opération (nombre de créations, mises à jour).
   * @throws {AxiosError} Propage une erreur en cas de problème d'insertion en base (500).
   * @example
   * try {
   *    isImporting.value = true;
   *    const result = await api.executeImport(validatedPayload);
   *    ui.notify(`Import terminé : ${result.created} créés, ${result.updated} mis à jour.`, "success");
   * } catch (error) {
   *    ui.notify("L'importation finale a échoué.", "error");
   * }
   */
  async executeImport(payload: ImportExecutePayload): ApiData<ImportSummary> {
    const response = await apiClient.post<ImportSummary>('/import/execute', payload)
    return response.data
  },

  // ==========================================
  // --- IMPORTATION RÉSULTATS (OUTILS) ---
  // ==========================================

  /**
   * Analyse un fichier de résultats externe (Voltaire ou Ecri+) avant l'importation définitive.
   * Le backend cherche à lier chaque score à un étudiant existant dans la base de données
   * via des algorithmes de correspondance (nom/prénom).
   *
   * @async
   * @function previewAssessmentImport
   * @param {number} promotionId - L'ID de la promotion concernée.
   * @param {Platform} platform - La plateforme source ('Voltaire' ou 'Ecri+').
   * @param {AssessmentType} assessmentType - Le moment de l'évaluation ('INITIAL' ou 'FINAL').
   * @param {File} file - Le fichier binaire CSV ou Excel extrait de l'outil.
   * @returns {ApiData<AssessmentPreviewResponse>} Les correspondances trouvées et les cas non résolus.
   * @throws {AxiosError} Propage une erreur si les colonnes attendues sont absentes (400).
   * @example
   * try {
   *    isAnalyzing.value = true;
   *    const preview = await api.previewAssessmentImport(1, Platform.VOLTAIRE, AssessmentType.INITIAL, file);
   *    unmatchedRows.value = preview.unmatched_results;
   * } catch (error) {
   *    ui.notify("Format du fichier de résultats non reconnu.", "error");
   * }
   */
  async previewAssessmentImport(
    promotionId: number,
    toolId: number,
    assessmentType: AssessmentType,
    file: File,
  ): ApiData<AssessmentPreviewResponse> {
    const formData = new FormData()
    formData.append('promotion_id', promotionId.toString())
    formData.append('tool_id', toolId.toString())
    formData.append('assessment_type', assessmentType)
    formData.append('file', file)

    const response = await apiClient.post<AssessmentPreviewResponse>(
      '/import/assessments/preview',
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } },
    )
    return response.data
  },

  /**
   * Intègre définitivement les scores des outils externes dans la base de données.
   * Transforme la requête validée par l'utilisateur en objets d'évaluation stockés pour les étudiants.
   *
   * @async
   * @function executeAssessmentImport
   * @param {AssessmentExecuteRequest} payload - Les associations ID étudiant -> Score validées par le frontend.
   * @returns {ApiData<ImportSummary>} Résumé des insertions.
   * @throws {AxiosError} Propage une erreur interne (500).
   * @example
   * try {
   *    const result = await api.executeAssessmentImport(finalData);
   *    ui.notify(`${result.created} scores ont été importés avec succès.`, "success");
   * } catch (error) {
   *    ui.notify("Erreur lors de l'enregistrement des scores.", "error");
   * }
   */
  async executeAssessmentImport(payload: AssessmentExecuteRequest): ApiData<ImportSummary> {
    const response = await apiClient.post<ImportSummary>('/import/assessments/execute', payload)
    return response.data
  },

  // ==========================================
  // --- ÉTUDIANTS ---
  // ==========================================

  /**
   * Récupère la liste de tous les étudiants enregistrés dans la base, incluant les relations textuelles
   * (nom du groupe, nom de la promotion).
   *
   * @async
   * @function getStudents
   * @returns {ApiData<Student[]>} Une promesse contenant le tableau de tous les étudiants.
   * @throws {AxiosError} Propage une erreur (500) en cas d'échec de récupération.
   * @example
   * try {
   *    const data = await api.getStudents();
   *    students.value = data;
   * } catch (error) {
   *    ui.notify("Impossible de récupérer la liste des étudiants.", "error");
   * }
   */
  async getStudents(): ApiData<Student[]> {
    const response = await apiClient.get<Student[]>('/students/')
    return response.data
  },

  /**
   * Récupère la liste des étudiants en incluant spécifiquement leurs scores calculés (Initiaux et Finaux)
   * pour des affichages tabulaires (ex: tableau de correction).
   *
   * @async
   * @function getStudentsWithScores
   * @returns {ApiData<StudentWithScores[]>} Tableau des étudiants avec `initial_score` et `final_score`.
   * @throws {AxiosError} Propage une erreur (500) si le calcul des scores échoue côté serveur.
   * @example
   * try {
   *    const data = await api.getStudentsWithScores();
   *    studentScoresTable.value = data;
   * } catch (error) {
   *    ui.notify("Erreur lors de la récupération des scores.", "error");
   * }
   */
  async getStudentsWithScores(): ApiData<StudentWithScores[]> {
    const response = await apiClient.get<StudentWithScores[]>('/students/with-scores')
    return response.data
  },

  /**
   * Récupère toutes les informations détaillées d'un profil étudiant (socio-culturel, enquête).
   *
   * @async
   * @function getStudentById
   * @param {string} studentId - L'UUID (chaine de caractères) unique de l'étudiant.
   * @returns {ApiData<Student>} Les données complètes de l'étudiant.
   * @throws {AxiosError} Propage une erreur 404 si l'UUID est introuvable.
   * @example
   * try {
   *    const profile = await api.getStudentById(route.params.id);
   *    studentProfile.value = profile;
   * } catch (error) {
   *    ui.notify("Profil étudiant introuvable.", "error");
   * }
   */
  async getStudentById(studentId: string): ApiData<Student> {
    const response = await apiClient.get<Student>(`/students/${studentId}`)
    return response.data
  },

  /**
   * Ajoute un étudiant manuellement dans la base de données (sans passer par un import CSV).
   *
   * @async
   * @function createStudent
   * @param {StudentCreatePayload} studentData - Les informations saisies dans le formulaire.
   * @returns {ApiData<Student>} L'étudiant créé avec son UUID généré.
   * @throws {AxiosError} Propage une erreur de validation (400) si des champs requis manquent.
   * @example
   * try {
   *    const newStudent = await api.createStudent(formData);
   *    ui.notify(`Étudiant ${newStudent.last_name} ajouté.`, "success");
   * } catch (error) {
   *    ui.notify("Formulaire invalide ou incomplet.", "error");
   * }
   */
  async createStudent(studentData: StudentCreatePayload): ApiData<Student> {
    const response = await apiClient.post<Student>('/students/', studentData)
    return response.data
  },

  /**
   * Met à jour les informations d'un étudiant spécifique.
   * Supporte les modifications partielles (PATCH).
   *
   * @async
   * @function updateStudent
   * @param {string} id - L'UUID de l'étudiant.
   * @param {StudentUpdatePayload} data - L'objet contenant uniquement les champs modifiés.
   * @returns {ApiData<Student>} L'étudiant mis à jour.
   * @throws {AxiosError} Propage une erreur (400, 404).
   * @example
   * try {
   *    await api.updateStudent(student.id, { group_id: 2, appetence_level: "Très fort" });
   *    ui.notify("Profil mis à jour.", "success");
   * } catch (error) {
   *    ui.notify("Impossible de sauvegarder les modifications.", "error");
   * }
   */
  async updateStudent(id: string, data: StudentUpdatePayload): ApiData<Student> {
    const response = await apiClient.patch<Student>(`/students/${id}`, data)
    return response.data
  },

  /**
   * Supprime un étudiant ainsi que toutes ses copies, dictées, et données associées (suppression en cascade).
   * Action irréversible.
   *
   * @async
   * @function deleteStudent
   * @param {string} studentId - L'UUID de l'étudiant à supprimer.
   * @returns {ApiData<void>}
   * @throws {AxiosError} Propage une erreur 404 ou 500.
   * @example
   * try {
   *    await api.deleteStudent(studentToDelete.id);
   *    ui.notify("Étudiant supprimé définitivement.", "success");
   * } catch (error) {
   *    ui.notify("Erreur lors de la suppression.", "error");
   * }
   */
  async deleteStudent(studentId: string): ApiData<void> {
    const response = await apiClient.delete<void>(`/students/${studentId}`)
    return response.data
  },

  /**
   * Récupère un tableau allégé contenant la progression de chaque étudiant
   * (Score Initial, Score Final, et la soustraction des deux).
   * Utile pour certains dashboards spécifiques (DataGrids de progression).
   *
   * @async
   * @function getStudentProgression
   * @returns {ApiData<StudentProgression[]>}
   * @throws {AxiosError}
   * @example
   * try {
   *    const progressData = await api.getStudentProgression();
   *    tableData.value = progressData;
   * } catch (error) {
   *    ui.notify("Impossible de récupérer les progressions individuelles.", "error");
   * }
   */
  async getStudentProgression(): ApiData<StudentProgression[]> {
    const response = await apiClient.get<StudentProgression[]>('/students/stats/progression')
    return response.data
  },

  // ==========================================
  // --- CATÉGORIES & RÈGLES ---
  // ==========================================

  /**
   * Récupère la liste complète des catégories de fautes extraites de LanguageTool,
   * ainsi que les règles imbriquées (`rules[]`) associées à chaque catégorie.
   *
   * @async
   * @function getCategories
   * @returns {ApiData<Category[]>} L'arbre complet Catégories -> Règles.
   * @throws {AxiosError} Propage une erreur (500) en cas d'échec d'accès à la base.
   * @example
   * try {
   *    const rulesTree = await api.getCategories();
   *    categories.value = rulesTree;
   * } catch (error) {
   *    ui.notify("Erreur de chargement des règles LanguageTool.", "error");
   * }
   */
  async getCategories(): ApiData<Category[]> {
    const response = await apiClient.get<Category[]>('/categories')
    return response.data
  },

  /**
   * Met à jour les paramètres d'une catégorie, notamment sa Typologie Rousseau (D, S, R, A)
   * et le malus à appliquer pour chaque faute de cette catégorie.
   *
   * @async
   * @function updateCategory
   * @param {number} categoryId - L'ID numérique de la catégorie.
   * @param {UpdateCategoryPayload} categoryData - Le nouveau type et/ou penalty.
   * @returns {ApiData<void>}
   * @throws {AxiosError} Propage une erreur de validation (400) ou introuvable (404).
   * @example
   * try {
   *    await api.updateCategory(cat.id, { type_rousseau: "Sens", penalty: 1.5 });
   *    ui.notify("Barème mis à jour pour cette catégorie.", "success");
   * } catch (error) {
   *    ui.notify("Erreur lors de la sauvegarde de la catégorie.", "error");
   * }
   */
  async updateCategory(categoryId: number, categoryData: UpdateCategoryPayload): ApiData<void> {
    const response = await apiClient.patch<void>(`/categories/${categoryId}`, categoryData)
    return response.data
  },

  /**
   * Active ou désactive une règle spécifique de LanguageTool.
   * Une règle inactive sera ignorée par l'algorithme de correction et ne comptera pas dans les malus.
   *
   * @async
   * @function updateRule
   * @param {number} ruleId - L'ID numérique de la règle.
   * @param {UpdateRulePayload} payload - L'état booléen `is_active`.
   * @returns {ApiData<void>}
   * @throws {AxiosError} Propage une erreur 404 si la règle n'existe pas.
   * @example
   * try {
   *    await api.updateRule(rule.id, { is_active: false });
   *    ui.notify("Règle désactivée avec succès.", "success");
   * } catch (error) {
   *    ui.notify("Échec de la modification de la règle.", "error");
   * }
   */
  async updateRule(ruleId: number, payload: UpdateRulePayload): ApiData<void> {
    const response = await apiClient.patch<void>(`/rules/${ruleId}`, payload)
    return response.data
  },

  // ==========================================
  // --- DICTÉES & SOUMISSIONS ---
  // ==========================================

  /**
   * Force le backend à repasser sur toutes les soumissions de dictées enregistrées
   * et à recalculer leurs scores `final_score` en fonction du barème actuel (malus des catégories).
   * Fonction lourde, à appeler après avoir modifié des pénalités de catégories.
   *
   * @async
   * @function recalculateAllDictations
   * @returns {ApiData<{ message: string }>} Un message de confirmation de fin de traitement.
   * @throws {AxiosError} Propage une erreur (500) si le processus échoue.
   * @example
   * try {
   *    isRecalculating.value = true;
   *    await api.recalculateAllDictations();
   *    ui.notify("Tous les scores ont été recalculés selon le nouveau barème.", "success");
   * } catch (error) {
   *    ui.notify("Le recalcul a échoué. Vérifiez l'état du serveur.", "error");
   * } finally {
   *    isRecalculating.value = false;
   * }
   */
  async recalculateAllDictations(): ApiData<{ message: string }> {
    const response = await apiClient.post<{ message: string }>('/dictations/recalculate')
    return response.data
  },

  /**
   * Récupère la liste des dictées (soumissions) effectuées par un étudiant spécifique,
   * ordonnées chronologiquement ou par type (Initiale/Finale).
   *
   * @async
   * @function getStudentSubmissions
   * @param {string} studentUuid - L'UUID de l'étudiant.
   * @returns {ApiData<Submission[]>} Les métadonnées de soumissions pour l'étudiant.
   * @throws {AxiosError} Propage une erreur 404 si l'étudiant n'est pas trouvé.
   * @example
   * try {
   *    const submissions = await api.getStudentSubmissions(selectedStudent.id);
   *    studentDictations.value = submissions;
   * } catch (error) {
   *    ui.notify("Impossible de récupérer les dictées de l'étudiant.", "error");
   * }
   */
  async getStudentSubmissions(studentUuid: string): ApiData<Submission[]> {
    const response = await apiClient.get<Submission[]>('/submissions', {
      params: { student_uuid: studentUuid },
    })
    return response.data
  },

  /**
   * Récupère l'analyse détaillée d'une copie corrigée par le système É.M.I.L.E.
   * Contient le texte HTML avec les spans de surlignage, les fautes détectées (`mistakes`),
   * et le détail des pénalités appliquées.
   *
   * @async
   * @function getSubmissionDetails
   * @param {number} submissionId - L'identifiant de la copie.
   * @returns {ApiData<SubmissionDetails>} L'objet lourd contenant tout le détail de correction.
   * @throws {AxiosError} Propage une erreur 404 si la soumission n'existe pas.
   * @example
   * try {
   *    isLoadingDetails.value = true;
   *    const details = await api.getSubmissionDetails(subId);
   *    activeSubmissionContent.value = details;
   * } catch (error) {
   *    ui.notify("Impossible de charger la copie corrigée.", "error");
   * } finally {
   *    isLoadingDetails.value = false;
   * }
   */
  async getSubmissionDetails(submissionId: number): ApiData<SubmissionDetails> {
    const response = await apiClient.get<SubmissionDetails>(`/submissions/${submissionId}`)
    return response.data
  },

  /**
   * Intègre un lot (bulk) de copies étudiants (souvent issues de fichiers Word/Zip).
   * Le backend traite les textes de manière asynchrone ou séquentielle, génère les entités
   * `Submission` et déclenche l'analyse de fautes LanguageTool.
   *
   * @async
   * @function createBulkSubmissions
   * @param {SubmissionCreatePayload[]} submissions - Le tableau contenant l'ID étudiant, la dictée référente, et le texte brut.
   * @returns {ApiData<Submission[]>} Les copies fraîchement créées.
   * @throws {AxiosError} Propage une erreur (400, 500) en cas d'échec du traitement de lot.
   * @example
   * try {
   *    isUploading.value = true;
   *    await api.createBulkSubmissions(parsedWordDocuments);
   *    ui.notify("L'importation et l'analyse des dictées sont terminées.", "success");
   * } catch (error) {
   *    ui.notify("L'importation en masse a rencontré un problème.", "error");
   * } finally {
   *    isUploading.value = false;
   * }
   */
  async createBulkSubmissions(submissions: SubmissionCreatePayload[]): ApiData<Submission[]> {
    const response = await apiClient.post<Submission[]>('/submissions/bulk', submissions)
    return response.data
  },

  // ==========================================
  // --- STATISTIQUES (DASHBOARDS) ---
  // ==========================================

  /**
   * Récupère les données statistiques globales relatives à l'étude Rousseau.
   * Les données retournées sont destinées à alimenter les graphiques (Chart.js)
   * mesurant l'impact pédagogique, les corrélations socioculturelles, et la comparaison des outils.
   *
   * @async
   * @function getRousseauStats
   * @returns {ApiData<RousseauStats>} Les données agrégées H1, H2, H3, H4.
   * @throws {AxiosError} Propage une erreur 500 en cas d'échec de l'agrégation en base.
   * @example
   * try {
   *    isLoading.value = true;
   *    const rousseauData = await api.getRousseauStats();
   *    stats.value = rousseauData;
   * } catch (error) {
   *    ui.notify("Erreur lors du chargement des statistiques Rousseau.", "error");
   * } finally {
   *    isLoading.value = false;
   * }
   */
  async getRousseauStats(): ApiData<RousseauStats> {
    const response = await apiClient.get<RousseauStats>('/stats/rousseau')
    return response.data
  },

  /**
   * Récupère les statistiques spécifiques au fonctionnement et à l'efficacité de l'outil É.M.I.L.E.
   * Fournit des données agrégées pour les bar charts et pie charts (Répartition groupes,
   * moyenne globale, statistiques de typologie d'erreurs).
   *
   * @async
   * @function getEmileDashboardStats
   * @returns {ApiData<EmileStatsResponse>} L'objet complet alimentant la vue `EmileDashboardView`.
   * @throws {AxiosError} Propage une erreur 500 en cas de problème de requête analytique.
   * @example
   * try {
   *    const emileStats = await api.getEmileDashboardStats();
   *    dashboardData.value = emileStats;
   * } catch (error) {
   *    ui.notify("Données du tableau de bord indisponibles.", "error");
   * }
   */
  async getEmileDashboardStats(): ApiData<EmileStatsResponse> {
    const response = await apiClient.get<EmileStatsResponse>('/stats/emile')
    return response.data
  },

  // ==========================================
  // --- TEXTES DE DICTÉES RÉFÉRENTES ---
  // ==========================================

  /**
   * Récupère la liste des textes de dictées de référence (le texte parfait sur lequel
   * le professeur ou LanguageTool se base pour corriger).
   *
   * @async
   * @function getDictations
   * @returns {ApiData<Dictation[]>} Un tableau contenant les dictées modèles.
   * @throws {AxiosError} Propage une erreur (500) en cas d'échec réseau.
   * @example
   * try {
   *    const referenceTexts = await api.getDictations();
   *    availableDictations.value = referenceTexts;
   * } catch (error) {
   *    ui.notify("Impossible de charger les textes de référence.", "error");
   * }
   */
  async getDictations(): ApiData<Dictation[]> {
    const response = await apiClient.get<Dictation[]>('/dictations')
    return response.data
  },

  /**
   * Crée un nouveau texte de dictée de référence (modèle parfait).
   *
   * @async
   * @function createDictation
   * @param {DictationCreatePayload} payload - Le titre (ex: "Initiale 2025") et le texte correct.
   * @returns {ApiData<Dictation>} La dictée modèle créée avec son ID.
   * @throws {AxiosError} Propage une erreur de validation (400) ou serveur (500).
   * @example
   * try {
   *    const newDict = await api.createDictation({
   *    title: "Test de Rentrée",
   *    content_reference: "Texte sans aucune faute..."
   * });
   *    ui.notify("Dictée modèle ajoutée.", "success");
   * } catch (error) {
   *    ui.notify("Erreur lors de la création de la dictée modèle.", "error");
   * }
   */
  async createDictation(payload: DictationCreatePayload): ApiData<Dictation> {
    const response = await apiClient.post<Dictation>('/dictations', payload)
    return response.data
  },
}
