import axios from 'axios';
import type { GlobalStats, Student } from '@/types';

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

    createDictation(payload: { title: string; content_reference: string}) {
        return apiClient.post('/dictations', payload);
    },

    getStudents() {
        return apiClient.get<Student[]>('/students');
    },
    deleteStudent(studentId: string) {
        return apiClient.delete(`/students/${studentId}`);
    }
};