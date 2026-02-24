import axios from 'axios';
import type { Dictation, Student, StudentCreate, SubmissionCreate } from '@/types';

const apiClient = axios.create({
    baseURL: 'http://localhost:8000/api',
    headers: {
        'Content-Type': 'application/json',
    },
});

export default {
    getRousseauStats() {
        return apiClient.get('/stats/rousseau');
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
    async createBulkSubmissions(submissions: SubmissionCreate[]) {
        const response = await apiClient.post('/submissions/bulk', submissions);
        return response.data;
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
    async updateGradingScale(scaleId: number, scaleData: any) {
        const response = await apiClient.patch(`/grading-scales/${scaleId}`, scaleData); 
        return response.data;
    },

    getUnclassifiedRules() {
        return apiClient.get('/rules/unclassified');
    },
    
    updateRule(ruleId: number, payload: any) {
        return apiClient.patch(`/rules/${ruleId}`, payload);
    },
    updateDictationRules(dictationId: number, rulesConfig: Record<string, number>) {
        return apiClient.patch(`/dictations/${dictationId}/rules`, { rules_config: rulesConfig });
    },

    getStudents() {
        return apiClient.get<Student[]>('/students');
    },
    getStudentProgression() {
        return apiClient.get('/students/stats/progression');
    },
    async createStudent(studentData: StudentCreate) {
        const response = await apiClient.post('/students/', studentData);
        return response.data;
    },
    async updateStudent(studentId: string, studentData: any) {
        const response = await apiClient.patch(`/students/${studentId}`, studentData);
        return response.data;
    },
    deleteStudent(studentId: string) {
        return apiClient.delete(`/students/${studentId}`);
    }
};