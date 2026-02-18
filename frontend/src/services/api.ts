import axios from 'axios';
import type { GlobalStats, Dictation, Student } from '@/types';

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

    getDictations() {
        return apiClient.get<Dictation[]>('/dictations');
    },
    createDictation(payload: { title: string; content_reference: string}) {
        return apiClient.post('/dictations', payload);
    },

    createSubmission(payload: { 
        student_uuid: string; 
        dictation_id: string; 
        assessment_type: string;
        content_student: string;
    }) {
        return apiClient.post('/submissions', payload);
    },

    getStudents() {
        return apiClient.get<Student[]>('/students');
    },
    deleteStudent(studentId: string) {
        return apiClient.delete(`/students/${studentId}`);
    }
};