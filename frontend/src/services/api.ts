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
    getEmileDashboardStats() {
        return apiClient.get('/stats/emile');
    },

    getDictations() {
        return apiClient.get<Dictation[]>('/dictations');
    },
    createDictation(payload: { title: string; content_reference: string}) {
        return apiClient.post('/dictations', payload);
    },

    getStudentSubmissions(studentUuid: string) {
        return apiClient.get('/submissions', {
        params: {
            student_uuid: studentUuid
        }
        });
    },
    getSubmissionDetails(submissionId: number | string) {
        return apiClient.get(`/submissions/${submissionId}`);
    },
    createSubmission(payload: { 
        student_uuid: string; 
        dictation_id: string; 
        assessment_type: string;
        content_student: string;
    }) {
        return apiClient.post('/submissions', payload);
    },

    getGradingScales() {
        return apiClient.get('/grading-scales');
    },
    createGradingScale(payload: any) {
        return apiClient.post('/grading-scales', payload);
    },   
    deleteGradingScale(scaleId: number) {
        return apiClient.delete(`/grading-scales/${scaleId}`);
    },

    getUnclassifiedRules() {
        return apiClient.get('/rules/unclassified');
    },
    
    updateRule(ruleId: number, payload: any) {
        return apiClient.patch(`/rules/${ruleId}`, payload);
    },

    getStudents() {
        return apiClient.get<Student[]>('/students');
    },
    getStudentProgression() {
        return apiClient.get('/students/stats/progression');
    },
    deleteStudent(studentId: string) {
        return apiClient.delete(`/students/${studentId}`);
    }
};