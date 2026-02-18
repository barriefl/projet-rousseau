import axios from 'axios';
import type { GlobalStats, Submission, CorrectionPayload, Student } from '@/types';

const apiClient = axios.create({
    baseURL: 'http://localhost:8000/api',
    headers: {
        'Content-Type': 'application/json',
    },
});

export default {
    getGlobalStats() {
        return apiClient.get<GlobalStats>('/stats/global');
    },

    submitDictation(payload: CorrectionPayload) {
        return apiClient.post<Submission>('/corrections/', payload);
    },
    getCorrection(submissionId: number) {
        return apiClient.get<Submission>('/corrections/${submissionId}');
    },

    getStudents() {
        return apiClient.get<Student[]>('/students');
    },
    deleteStudent(studentId: string) {
        return apiClient.delete(`/students/${studentId}`);
    }
};