export interface Mistake {
    id?: number
    student_word: string;
    correct_word: string;
    position_index: number;
    length: number;
    category_code: string;
    type_rousseau: 'D' | 'S' | 'R' | 'A';
    malus_applied: number;
    message: string;
}

export interface Submission {
    id: number;
    final_score: number;
    scores: Record<string, number>;
    content_student?: string;
    mistakes: Mistake[];
}

export interface GlobalStats {
    total_students: number;
    submissions: {
        avg_init: number;
        avg_final: number;
        progression: number;
    };
    voltaire: {
        avg_init: number;
        avg_final: number;
        progression: number;
    };
    ecriplus: {
        avg_init: number;
        avg_final: number;
        progression: number;
    };
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