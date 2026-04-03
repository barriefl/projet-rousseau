// =========================================================
// All mock data objects used across E2E specs
// =========================================================

export const mockPromotions = [
  { id: 1, name: 'BUT INFO 2024-2025' },
  { id: 2, name: 'BUT INFO 2025-2026' },
]

export const mockTools = [
  { id: 1, name: 'PV', full_name: 'Projet Voltaire' },
  { id: 2, name: 'E+', full_name: 'Ecri+' },
]

export const mockGroups = [
  { id: 1, name: 'G0', description: 'Groupe contrôle' },
  { id: 2, name: 'G1', description: 'Groupe autonomie' },
  { id: 3, name: 'G2', description: 'Groupe Voltaire' },
  { id: 4, name: 'G3', description: 'Groupe salle' },
  { id: 5, name: 'G4', description: 'Correction humaine' },
  { id: 6, name: 'G5', description: 'Groupe Ecri+' },
]

export const mockStudents = [
  {
    id: 'aaaaaaaa-0000-0000-0000-000000000001',
    first_name: 'Alice',
    last_name: 'DUPONT',
    promotion_id: 1,
    group_id: 2,
    tool_id: 1,
    promotion_name: 'BUT INFO 2024-2025',
    group_name: 'G1',
    tool_name: 'PV',
    group_display: 'G1-PV',
    appetence_level: '3',
    has_library: 'Oui',
    reading_support: 'Papier',
    reading_works: 'Romans / écrits littéraires',
    motive: 'Distraction',
    parent_1_degree: 'Bac+2 BTS Licence',
    parent_1_csp: 'Cadres, professions intellectuelles sup.',
    parent_2_degree: 'Bac',
    parent_2_csp: 'Employés / ouvriers',
    declared_level: '3',
  },
  {
    id: 'bbbbbbbb-0000-0000-0000-000000000002',
    first_name: 'Bob',
    last_name: 'MARTIN',
    promotion_id: 1,
    group_id: 3,
    tool_id: 2,
    promotion_name: 'BUT INFO 2024-2025',
    group_name: 'G2',
    tool_name: 'E+',
    group_display: 'G2-E+',
    appetence_level: '4',
    has_library: 'Non',
    reading_support: 'Ecran',
    reading_works: 'Mangas / BD',
    motive: 'Information',
    parent_1_degree: 'Bac',
    parent_1_csp: 'Agriculteurs exploitants',
    parent_2_degree: 'Aucun',
    parent_2_csp: 'Retraités',
    declared_level: '2',
  },
]

export const mockStudentsWithScores = [
  {
    id: 'aaaaaaaa-0000-0000-0000-000000000001',
    first_name: 'Alice',
    last_name: 'DUPONT',
    promotion_id: 1,
    group_id: 2,
    promotion_name: 'BUT INFO 2024-2025',
    group_name: 'G1',
    tool_name: 'PV',
    group_display: 'G1-PV',
    initial_score: 8.5,
    final_score: 4.0,
  },
  {
    id: 'bbbbbbbb-0000-0000-0000-000000000002',
    first_name: 'Bob',
    last_name: 'MARTIN',
    promotion_id: 1,
    group_id: 3,
    promotion_name: 'BUT INFO 2024-2025',
    group_name: 'G2',
    tool_name: 'E+',
    group_display: 'G2-E+',
    initial_score: 12.0,
    final_score: null,
  },
]

export const mockStudentsProgression = [
  {
    id: 'aaaaaaaa-0000-0000-0000-000000000001',
    first_name: 'Alice',
    last_name: 'DUPONT',
    group_name: 'G1',
    tool_name: 'PV',
    group_display: 'G1-PV',
    score_initial: 8.5,
    score_final: 4.0,
    progress: -4.5,
  },
  {
    id: 'bbbbbbbb-0000-0000-0000-000000000002',
    first_name: 'Bob',
    last_name: 'MARTIN',
    group_name: 'G2',
    tool_name: 'E+',
    group_display: 'G2-E+',
    score_initial: 12.0,
    score_final: null,
    progress: null,
  },
]

export const mockDictations = [
  { id: 1, title: 'Dictée Initiale 2024', content_reference: 'Le texte de référence sans faute.' },
  { id: 2, title: 'Dictée Finale 2024', content_reference: 'Un autre texte de référence.' },
]

export const mockSubmissions = [
  {
    id: 101,
    created_at: '2024-10-01T10:00:00',
    student_uuid: 'aaaaaaaa-0000-0000-0000-000000000001',
    dictation_id: 1,
    assessment_type: 'Initiale',
    content_student: 'Le texte avec des fautes.',
    final_score: 8.5,
    scores: { Grammaire: 4.5, Ponctuation: 4.0 },
  },
]

export const mockSubmissionDetails = {
  id: 101,
  student_uuid: 'aaaaaaaa-0000-0000-0000-000000000001',
  dictation_id: 1,
  assessment_type: 'Initiale',
  content_student: 'Le texte avec des fautes.',
  final_score: 8.5,
  scores: { Grammaire: 4.5, Ponctuation: 4.0 },
  html_text: 'Le texte avec <span class="faute" data-type="Règle" data-malus="1" data-corr="des" data-desc="Accord">des</span> fautes.',
  mistakes: [
    {
      student_word: 'des',
      correct_word: 'des',
      position_index: 14,
      length: 3,
      category_id: 1,
      type_rousseau: 'Règle',
      malus_applied: 1.0,
      rule_id_lt: 'FRENCH_GRAMMAR',
      message: 'Erreur grammaticale',
    },
  ],
}

export const mockCategories = [
  {
    id: 1,
    lt_category_id: 'GRAMMAR',
    name: 'Grammaire',
    type_rousseau: 'Règle',
    penalty: 1.0,
    rules: [
      { id: 1, lt_rule_id: 'FRENCH_GRAMMAR_1', description: 'Accord sujet-verbe', is_active: true, category_id: 1 },
      { id: 2, lt_rule_id: 'FRENCH_GRAMMAR_2', description: 'Accord adjectif', is_active: false, category_id: 1 },
    ],
  },
  {
    id: 2,
    lt_category_id: 'TYPOS',
    name: 'Faute de frappe',
    type_rousseau: 'Dessin',
    penalty: 0.5,
    rules: [
      { id: 3, lt_rule_id: 'TYPO_1', description: 'Faute de frappe commune', is_active: true, category_id: 2 },
    ],
  },
  {
    id: 3,
    lt_category_id: 'PUNCTUATION',
    name: 'Ponctuation',
    type_rousseau: 'Dessin',
    penalty: 0.25,
    rules: [],
  },
]

export const mockRousseauStats = {
  h1_summary: {
    labels: ['BUT INFO 2024-2025'],
    dictation_initial: [72.5],
    dictation_final: [81.0],
    tools_initial: [0.45],
    tools_final: [0.62],
    effectif: [48],
  },
  h2_equivalence: {
    labels: ['BUT INFO 2024-2025'],
    g2_final: [80.0],
    g2_progress: [12.0],
    g5_final: [78.5],
    g5_progress: [10.0],
    effectif: [48],
  },
  h2_boxplots: {
    G1: { initial: [60, 70, 75, 80, 90], final: [65, 72, 78, 85, 92], delta: [-5, 2, 3, 5, 8] },
    G2: { initial: [55, 65, 72, 78, 88], final: [62, 70, 79, 84, 94], delta: [0, 4, 7, 8, 10] },
  },
  h2_stats_test: {
    anova: { f_stat: 2.34, p_value: 0.12, is_significant: false },
    tukey: [],
  },
  h3_teacher: {
    'Accompagnement Humain (G4)': { score: 83.2, effectif: 10 },
    'Autonomie / Outils (G2/G3/G5)': { score: 78.5, effectif: 30 },
  },
  h4_sociocultural: {
    'Catégorie socio-culturelle': {
      'CSP Parents': {
        'Cadres, professions intellectuelles sup.': { Initial: 75.0, Progress: 8.0, Effectif: 12 },
        'Employés / ouvriers': { Initial: 65.0, Progress: 5.0, Effectif: 18 },
      },
      'Diplôme Parents': {
        'Bac+4 Master Doctorat': { Initial: 78.0, Progress: 9.0, Effectif: 8 },
        'Aucun': { Initial: 60.0, Progress: 4.0, Effectif: 6 },
      },
    },
    'Pratique de la lecture': {
      Appétence: {
        'Niveau 1': { Initial: 60.0, Progress: 3.0, Effectif: 5 },
        'Niveau 5': { Initial: 82.0, Progress: 10.0, Effectif: 7 },
      },
      Bibliothèque: {
        Oui: { Initial: 76.0, Progress: 8.5, Effectif: 22 },
        Non: { Initial: 64.0, Progress: 5.0, Effectif: 26 },
      },
      Support: {},
      'Œuvres lues': {},
      Motifs: {},
    },
    'Orthographe, grammaire, conjugaison': {
      'Niveau déclaré': {
        'Niveau 2': { Initial: 63.0, Progress: 4.0, Effectif: 15 },
        'Niveau 4': { Initial: 79.0, Progress: 9.0, Effectif: 11 },
      },
    },
  },
  regression_model: {
    r2: 0.65,
    coefficients: [
      { feature: 'Bibliothèque_Oui', weight: 5.2 },
      { feature: 'Appétence_5', weight: 4.8 },
      { feature: 'CSP_Cadres', weight: -2.1 },
    ],
  },
  anova_multifactorial: [
    { factor: 'Appétence Lecture', p_value: 0.03, is_significant: true, impact_percent: 12.5 },
    { factor: 'CSP', p_value: 0.14, is_significant: false, impact_percent: 5.2 },
    { factor: 'Diplôme', p_value: 0.08, is_significant: false, impact_percent: 7.1 },
    { factor: 'Niveau Déclaré', p_value: 0.01, is_significant: true, impact_percent: 18.3 },
  ],
}

export const mockEmileStats = {
  total_students: 2,
  total_submissions: 3,
  global_average: 7.5,
  group_distribution_by_promo: {
    'BUT INFO 2024-2025': { G1: 1, G2: 1 },
  },
  group_averages: {
    G1: { Initial: 8.5, Final: 4.0 },
    G2: { Initial: 12.0, Final: 0.0 },
  },
  promo_averages: {
    'BUT INFO 2024-2025': { Initial: 10.25, Final: 2.0 },
  },
  comparison_tool: {
    'Projet Voltaire (G2)': { Initial: 12.0, Final: 0.0 },
    'Écri+ (G5)': { Initial: 0.0, Final: 0.0 },
  },
  comparison_human_robot: {
    'Correction Humaine (G4)': { Initial: 0.0, Final: 0.0 },
    'Correction IA/Outil (G2, G3, G5)': { Initial: 12.0, Final: 0.0 },
  },
  comparison_motivation: {
    'Autonomie (G1)': 4.5,
    'Jalons obligatoires (G2)': 12.0,
    'Salle (G3)': 0.0,
    'Correction Humaine (G4)': 0.0,
  },
  mistakes_stats: {
    global: {
      Règle: { Grammaire: 25, 'Accord sujet-verbe': 12 },
      Dessin: { 'Faute de frappe': 8 },
    },
    promotions: {
      'BUT INFO 2024-2025': {
        Règle: { Grammaire: 25 },
      },
    },
  },
}

export const mockAuthResponse = {
  access_token: 'mock-jwt-token',
  token_type: 'bearer',
}

export const mockImportPreview = {
  promotion_id: 1,
  groups_to_create: ['G6'],
  exact_matches: [
    {
      csv_data: { first_name: 'Alice', last_name: 'DUPONT', group_name: 'G1' },
      match_type: 'exact',
      db_student_id: 1,
      db_first_name: 'Alice',
      db_last_name: 'DUPONT',
    },
  ],
  fuzzy_matches: [
    {
      csv_data: { first_name: 'Bod', last_name: 'MARTIN', group_name: 'G2' },
      match_type: 'fuzzy',
      db_student_id: 2,
      db_first_name: 'Bob',
      db_last_name: 'MARTIN',
    },
  ],
  new_students: [
    {
      csv_data: { first_name: 'Charlie', last_name: 'DURAND', group_name: 'G6' },
      match_type: 'new',
      db_student_id: null,
    },
  ],
}

export const mockAssessmentPreview = {
  tool_id: 1,
  assessment_type: 'Initiale',
  matched_results: [
    {
      csv_nom: 'DUPONT',
      csv_prenom: 'Alice',
      db_student_id: 1,
      db_first_name: 'Alice',
      db_last_name: 'DUPONT',
      match_type: 'exact',
      score: 0.72,
      details: {},
    },
  ],
  unmatched_results: [
    {
      csv_nom: 'UNKNOWN',
      csv_prenom: 'Inconnu',
      db_student_id: null,
      match_type: 'not_found',
      score: 0.55,
      details: {},
    },
  ],
}
