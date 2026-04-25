/**
 * Admin API Client
 * Handles all API calls for admin interface
 */

const adminAPI = {
    baseURL: '/admin',
    token: localStorage.getItem('adminToken'),

    // =================================================================
    // AUTHENTICATION
    // =================================================================

    async login(username, password) {
        const response = await fetch('/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Login failed');
        }

        const data = await response.json();

        // Check if user is admin using the role field from the login response
        if (data.role !== 'admin') {
            throw new Error('You must have admin role to access this page');
        }

        // Store token
        this.token = data.access_token;
        localStorage.setItem('adminToken', data.access_token);
        
        return data;
    },

    logout() {
        this.token = null;
        localStorage.removeItem('adminToken');
    },

    // =================================================================
    // STUDENT MANAGEMENT
    // =================================================================

    async createStudent(username, email, password, role = 'student') {
        const response = await fetch(`${this.baseURL}/students`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.token}`
            },
            body: JSON.stringify({
                username,
                email,
                password,
                role
            })
        });

        if (!response.ok) throw new Error(await response.text());
        return await response.json();
    },

    async listStudents(skip = 0, limit = 50) {
        const response = await fetch(
            `${this.baseURL}/students?skip=${skip}&limit=${limit}`,
            {
                headers: { 'Authorization': `Bearer ${this.token}` }
            }
        );

        if (!response.ok) throw new Error(await response.text());
        return await response.json();
    },

    async getStudentDetails(studentId) {
        const response = await fetch(
            `${this.baseURL}/students/${studentId}`,
            {
                headers: { 'Authorization': `Bearer ${this.token}` }
            }
        );

        if (!response.ok) throw new Error(await response.text());
        return await response.json();
    },

    async updateStudent(studentId, updateData) {
        const response = await fetch(
            `${this.baseURL}/students/${studentId}`,
            {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.token}`
                },
                body: JSON.stringify(updateData)
            }
        );

        if (!response.ok) throw new Error(await response.text());
        return await response.json();
    },

    async resetPassword(studentId, newPassword) {
        const response = await fetch(
            `${this.baseURL}/students/${studentId}/reset-password`,
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.token}`
                },
                body: JSON.stringify({
                    new_password: newPassword,
                    new_password_confirm: newPassword
                })
            }
        );

        if (!response.ok) throw new Error(await response.text());
        return await response.json();
    },

    async deleteStudent(studentId) {
        const response = await fetch(
            `${this.baseURL}/students/${studentId}`,
            {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${this.token}` }
            }
        );

        if (!response.ok) throw new Error(await response.text());
        return await response.json();
    },

    // =================================================================
    // EXERCISE MANAGEMENT
    // =================================================================

    async createExercise(exerciseData) {
        const response = await fetch(`${this.baseURL}/exercises`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.token}`
            },
            body: JSON.stringify(exerciseData)
        });

        if (!response.ok) throw new Error(await response.text());
        return await response.json();
    },

    async listExercises(filters = {}) {
        const params = new URLSearchParams();
        if (filters.concept_id) params.append('concept_id', filters.concept_id);
        if (filters.exercise_type) params.append('exercise_type', filters.exercise_type);
        if (filters.is_diagnostic !== undefined) params.append('is_diagnostic', filters.is_diagnostic);
        params.append('skip', filters.skip || 0);
        params.append('limit', filters.limit || 50);

        const response = await fetch(
            `${this.baseURL}/exercises?${params.toString()}`,
            {
                headers: { 'Authorization': `Bearer ${this.token}` }
            }
        );

        if (!response.ok) throw new Error(await response.text());
        return await response.json();
    },

    async getExerciseDetails(exerciseId) {
        const response = await fetch(
            `${this.baseURL}/exercises/${exerciseId}`,
            {
                headers: { 'Authorization': `Bearer ${this.token}` }
            }
        );

        if (!response.ok) throw new Error(await response.text());
        return await response.json();
    },

    async updateExercise(exerciseId, updateData) {
        const response = await fetch(
            `${this.baseURL}/exercises/${exerciseId}`,
            {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.token}`
                },
                body: JSON.stringify(updateData)
            }
        );

        if (!response.ok) throw new Error(await response.text());
        return await response.json();
    },

    async activateExercise(exerciseId) {
        const response = await fetch(
            `${this.baseURL}/exercises/${exerciseId}/activate`,
            {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${this.token}` }
            }
        );

        if (!response.ok) throw new Error(await response.text());
        return await response.json();
    },

    async deactivateExercise(exerciseId) {
        const response = await fetch(
            `${this.baseURL}/exercises/${exerciseId}/deactivate`,
            {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${this.token}` }
            }
        );

        if (!response.ok) throw new Error(await response.text());
        return await response.json();
    },

    async deleteExercise(exerciseId) {
        const response = await fetch(
            `${this.baseURL}/exercises/${exerciseId}`,
            {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${this.token}` }
            }
        );

        if (!response.ok) throw new Error(await response.text());
        return await response.json();
    },

    // =================================================================
    // ANALYTICS & LOGS
    // =================================================================

    async getDashboard() {
        const response = await fetch(`${this.baseURL}/dashboard`, {
            headers: { 'Authorization': `Bearer ${this.token}` }
        });

        if (!response.ok) throw new Error(await response.text());
        return await response.json();
    },

    async getAnalytics() {
        const response = await fetch(`${this.baseURL}/analytics`, {
            headers: { 'Authorization': `Bearer ${this.token}` }
        });

        if (!response.ok) throw new Error(await response.text());
        return await response.json();
    },

    async getLogs(skip = 0, limit = 50) {
        const response = await fetch(
            `${this.baseURL}/logs?skip=${skip}&limit=${limit}`,
            {
                headers: { 'Authorization': `Bearer ${this.token}` }
            }
        );

        if (!response.ok) throw new Error(await response.text());
        return await response.json();
    },

    // =================================================================
    // CURRICULUM DATA
    // =================================================================

    async getAllConcepts() {
        const response = await fetch(`${this.baseURL}/concepts`, {
            headers: { 'Authorization': `Bearer ${this.token}` }
        });

        if (!response.ok) throw new Error(await response.text());
        return await response.json();
    }
};
