/* API Communication Layer */

class API {
    constructor() {
        this.token = localStorage.getItem('token');
        this.studentId = localStorage.getItem('studentId');
    }

    getHeaders() {
        return {
            'Content-Type': 'application/json',
            ...(this.token && { 'Authorization': `Bearer ${this.token}` })
        };
    }

    async request(method, endpoint, data = null) {
        try {
            const url = `${CONFIG.API_BASE}${endpoint}`;
            const options = {
                method,
                headers: this.getHeaders()
            };

            if (data) {
                options.body = JSON.stringify(data);
            }

            log(`${method} ${endpoint}`, data);
            const response = await fetch(url, options);

            if (!response.ok) {
                if (response.status === 401) {
                    this.logout();
                }
                const error = await response.json().catch(() => ({}));
                throw new Error(error.detail || `HTTP ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            log('API Error:', error);
            throw error;
        }
    }

    // Auth endpoints
    async register(username, email, password) {
        const data = await this.request('POST', '/auth/register', {
            username,
            email,
            password
        });
        return data;
    }

    async login(username, password) {
        const data = await this.request('POST', '/auth/login', {
            username,
            password
        });
        
        if (data.access_token) {
            localStorage.setItem('token', data.access_token);
            localStorage.setItem('studentId', data.student_id);
            this.token = data.access_token;
            this.studentId = data.student_id;
        }
        
        return data;
    }

    logout() {
        localStorage.removeItem('token');
        localStorage.removeItem('studentId');
        this.token = null;
        this.studentId = null;
        log('Logged out');
    }

    // Diagnostic endpoints
    async getDiagnosticConcepts() {
        return this.request('GET', '/diagnostic/concepts');
    }

    async getDiagnosticQuestions(conceptId) {
        return this.request('GET', `/diagnostic/questions/${conceptId}`);
    }

    async submitDiagnostic(conceptId, answers) {
        return this.request('POST', `/diagnostic/submit/${conceptId}`, {
            answers
        });
    }

    // Exercise endpoints
    async getNextExercise() {
        return this.request('GET', '/exercise/next');
    }

    async submitExerciseAnswer(exerciseId, studentAnswer) {
        return this.request('POST', '/exercise/submit', {
            exercise_id: exerciseId,
            student_answer: studentAnswer
        });
    }

    async getExerciseHint(exerciseId, hintLevel = 1) {
        return this.request('GET', `/exercise/hint/${exerciseId}?hint_level=${hintLevel}`);
    }

    async getExerciseStats() {
        return this.request('GET', '/exercise/stats');
    }

    // Analytics endpoints
    async getDashboard() {
        return this.request('GET', '/analytics/dashboard');
    }

    async getProgress() {
        return this.request('GET', '/analytics/progress');
    }

    async getRecommendations() {
        return this.request('GET', '/analytics/recommendations');
    }

    async getProficiency() {
        return this.request('GET', '/analytics/proficiency-by-concept');
    }

    async getLearningAnalytics() {
        return this.request('GET', '/analytics/learning-analytics');
    }

    // Curriculum endpoints
    async getAllModules() {
        return this.request('GET', '/curriculum/modules');
    }

    async getModuleDetails(moduleId) {
        return this.request('GET', `/curriculum/modules/${moduleId}`);
    }

    async getSequenceDetails(sequenceId) {
        return this.request('GET', `/curriculum/sequences/${sequenceId}`);
    }

    async getConceptsBySequence(sequenceId) {
        return this.request('GET', `/curriculum/concepts-by-sequence/${sequenceId}`);
    }

    async getDiagnosticQuestionsForConcept(conceptId) {
        return this.request('GET', `/diagnostic/questions/${conceptId}`);
    }

    async submitDiagnosticTest(answers) {
        return this.request('POST', '/diagnostic/submit', { answers });
    }

    async explainAnswer(payload) {
        return this.request('POST', '/ai/explain', payload);
    }
}

const api = new API();
