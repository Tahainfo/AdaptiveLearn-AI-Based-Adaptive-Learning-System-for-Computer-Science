/**
 * Admin Dashboard Application Logic
 */

let currentPage = 'dashboard';
let conceptsList = [];

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    checkAdminAuthentication();
});

// =================================================================
// AUTHENTICATION
// =================================================================

function checkAdminAuthentication() {
    if (!adminAPI.token) {
        // Show login page
        document.getElementById('loginPage').style.display = 'flex';
        document.getElementById('dashboardArea').style.display = 'none';
    } else {
        // Show dashboard
        document.getElementById('loginPage').style.display = 'none';
        document.getElementById('dashboardArea').style.display = 'block';
        loadDashboard();
    }
}

async function handleAdminLogin(event) {
    event.preventDefault();
    
    const username = document.getElementById('adminUsername').value;
    const password = document.getElementById('adminPassword').value;
    const errorElement = document.getElementById('loginError');
    
    try {
        errorElement.style.display = 'none';
        errorElement.textContent = '';
        
        // Clear fields
        document.getElementById('adminUsername').value = '';
        document.getElementById('adminPassword').value = '';
        
        // Attempt login
        await adminAPI.login(username, password);
        
        // On success, show dashboard
        document.getElementById('loginPage').style.display = 'none';
        document.getElementById('dashboardArea').style.display = 'block';
        loadDashboard();
        
    } catch (error) {
        errorElement.textContent = error.message;
        errorElement.style.display = 'block';
    }
}

function logout() {
    if (confirm('Are you sure you want to logout?')) {
        adminAPI.logout();
        document.getElementById('loginPage').style.display = 'flex';
        document.getElementById('dashboardArea').style.display = 'none';
        document.getElementById('adminUsername').value = '';
        document.getElementById('adminPassword').value = '';
    }
}

// =================================================================
// NAVIGATION
// =================================================================

function navigateTo(pageId) {
    document.querySelectorAll('.admin-page').forEach(page => {
        page.classList.remove('active');
    });

    const page = document.getElementById(pageId);
    if (page) {
        page.classList.add('active');
    }

    currentPage = pageId;

    // Load page-specific data
    if (pageId === 'dashboard') {
        loadDashboard();
    } else if (pageId === 'students') {
        loadStudents();
    } else if (pageId === 'exercises') {
        loadExercises();
    } else if (pageId === 'analytics') {
        loadAnalytics();
    } else if (pageId === 'logs') {
        loadLogs();
    }
}

// =================================================================
// DASHBOARD
// =================================================================

async function loadDashboard() {
    try {
        const dashboard = await adminAPI.getDashboard();

        // Update stats
        document.getElementById('totalStudents').textContent = dashboard.total_students;
        document.getElementById('activeStudents').textContent = dashboard.active_students;
        document.getElementById('totalExercises').textContent = dashboard.total_exercises;
        document.getElementById('adminExercises').textContent = dashboard.admin_exercises_count;

        // Update mastery distribution
        const dist = dashboard.student_mastery_distribution;
        const total = dist.excellent + dist.good + dist.weak;
        
        document.querySelector('.bar .excellent').style.width = total ? (dist.excellent / total * 100) + '%' : '0%';
        document.querySelector('.bar .good').style.width = total ? (dist.good / total * 100) + '%' : '0%';
        document.querySelector('.bar .weak').style.width = total ? (dist.weak / total * 100) + '%' : '0%';
        
        document.getElementById('excellentCount').textContent = dist.excellent;
        document.getElementById('goodCount').textContent = dist.good;
        document.getElementById('weakCount').textContent = dist.weak;

        // Recent logs
        const logsHtml = dashboard.recent_logs.map(log => `
            <div class="log-item">
                <strong>${log.admin_username}</strong> - ${log.action_type.replace(/_/g, ' ')}
                <small>${new Date(log.timestamp).toLocaleString()}</small>
            </div>
        `).join('');
        
        document.getElementById('recentLogs').innerHTML = logsHtml || '<p>No recent actions</p>';

    } catch (error) {
        console.error('Dashboard error:', error);
        alert('Error loading dashboard: ' + error.message);
    }
}

// =================================================================
// STUDENTS MANAGEMENT
// =================================================================

async function loadStudents() {
    try {
        const data = await adminAPI.listStudents();
        
        const tableBody = document.getElementById('studentsTableBody');
        tableBody.innerHTML = data.students.map(student => `
            <tr>
                <td>${student.id}</td>
                <td>${student.username}</td>
                <td>${student.email}</td>
                <td><span class="badge ${student.role === 'admin' ? 'admin' : 'student'}">${student.role}</span></td>
                <td><span class="badge ${student.is_active ? 'active' : 'inactive'}">${student.is_active ? 'Active' : 'Inactive'}</span></td>
                <td>${new Date(student.created_at).toLocaleDateString()}</td>
                <td>
                    <button class="btn-small" onclick="viewStudentDetails(${student.id})">View</button>
                    <button class="btn-small btn-danger" onclick="deleteStudentConfirm(${student.id})">Delete</button>
                </td>
            </tr>
        `).join('');

    } catch (error) {
        console.error('Students load error:', error);
        alert('Error loading students: ' + error.message);
    }
}

function showCreateStudentForm() {
    document.getElementById('createStudentForm').style.display = 'flex';
}

function hideCreateStudentForm() {
    document.getElementById('createStudentForm').style.display = 'none';
    document.getElementById('newUsername').value = '';
    document.getElementById('newEmail').value = '';
    document.getElementById('newPassword').value = '';
    document.getElementById('newRole').value = 'student';
}

async function handleCreateStudent(event) {
    event.preventDefault();

    const username = document.getElementById('newUsername').value.trim();
    const email = document.getElementById('newEmail').value.trim();
    const password = document.getElementById('newPassword').value.trim();
    const role = document.getElementById('newRole').value;

    if (!username || !email || !password) {
        alert('Please fill in all fields');
        return;
    }

    try {
        await adminAPI.createStudent(username, email, password, role);
        alert('Student created successfully');
        hideCreateStudentForm();
        loadStudents();
    } catch (error) {
        alert('Error creating student: ' + error.message);
    }
}

async function viewStudentDetails(studentId) {
    try {
        const student = await adminAPI.getStudentDetails(studentId);
        alert(`Student: ${student.username}\nEmail: ${student.email}\nAvg Mastery: ${Math.round(student.average_mastery * 100)}%\nExercises Completed: ${student.total_exercises_completed}`);
    } catch (error) {
        alert('Error loading student: ' + error.message);
    }
}

async function deleteStudentConfirm(studentId) {
    if (confirm('Are you sure? This will deactivate the student account.')) {
        try {
            await adminAPI.deleteStudent(studentId);
            alert('Student deleted successfully');
            loadStudents();
        } catch (error) {
            alert('Error deleting student: ' + error.message);
        }
    }
}

// =================================================================
// EXERCISES MANAGEMENT
// =================================================================

async function loadConcepts() {
    try {
        conceptsList = await adminAPI.getAllConcepts();
        populateConceptSelect();
    } catch (error) {
        console.error('Failed to load concepts:', error);
    }
}

async function loadExercises() {
    // Always refresh concepts when the exercises page loads
    await loadConcepts();

    try {
        const data = await adminAPI.listExercises();
        
        const tableBody = document.getElementById('exercisesTableBody');
        tableBody.innerHTML = data.exercises.map(ex => `
            <tr>
                <td>${ex.id}</td>
                <td>${ex.title}</td>
                <td>${ex.concept_name || '—'}</td>
                <td><span class="badge">${ex.exercise_type}</span></td>
                <td>${ex.difficulty}</td>
                <td>${ex.is_diagnostic ? '✓' : '—'}</td>
                <td>${ex.error_type_targeted || '—'}</td>
                <td><span class="badge ${ex.is_active ? 'active' : 'inactive'}">${ex.is_active ? 'Yes' : 'No'}</span></td>
                <td>
                    <button class="btn-small" onclick="editExercise(${ex.id})">Edit</button>
                    ${ex.is_active ?
                        `<button class="btn-small" onclick="deactivateExerciseConfirm(${ex.id})">Deactivate</button>` :
                        `<button class="btn-small" onclick="activateExerciseConfirm(${ex.id})">Activate</button>`
                    }
                    <button class="btn-small btn-danger" onclick="deleteExerciseConfirm(${ex.id})">Delete</button>
                </td>
            </tr>
        `).join('');

    } catch (error) {
        console.error('Exercises load error:', error);
        alert('Error loading exercises: ' + error.message);
    }
}

function populateConceptSelect() {
    const select = document.getElementById('exConcept');
    select.innerHTML = '<option value="">-- Select Concept --</option>' +
        conceptsList.map(c =>
            `<option value="${c.id}"
                     data-module-id="${c.module_id}"
                     data-sequence-id="${c.sequence_id}">
                ${c.sequence_title} → ${c.name}
             </option>`
        ).join('');
}

async function showCreateExerciseForm() {
    if (conceptsList.length === 0) {
        await loadConcepts();
    }
    if (conceptsList.length === 0) {
        alert('Could not load concepts. Please refresh the page and try again.');
        return;
    }
    document.getElementById('createExerciseForm').style.display = 'flex';
}

function hideCreateExerciseForm() {
    document.getElementById('createExerciseForm').style.display = 'none';
}

function updateExerciseForm() {
    const type = document.getElementById('exType').value;
    const fieldsDiv = document.getElementById('dynamicExerciseFields');
    
    fieldsDiv.innerHTML = '';

    if (type === 'mcq') {
        fieldsDiv.innerHTML = `
            <div class="form-group">
                <label>Question *</label>
                <input type="text" id="exMCQQuestion" placeholder="Enter the question" required>
            </div>
            <div class="form-group">
                <label>Options (comma separated) *</label>
                <textarea id="exMCQOptions" placeholder="Option 1, Option 2, Option 3" required></textarea>
            </div>
            <div class="form-group">
                <label>Correct Option Index (0-based) *</label>
                <input type="number" id="exMCQCorrect" min="0" required>
            </div>
        `;
    } else if (type === 'short_answer') {
        fieldsDiv.innerHTML = `
            <div class="form-group">
                <label>Question *</label>
                <input type="text" id="exSAQuestion" placeholder="Enter the question" required>
            </div>
            <div class="form-group">
                <label>Correct Answer *</label>
                <input type="text" id="exSAAnswer" placeholder="Expected answer" required>
            </div>
            <div class="form-group">
                <label>Alternative Accepted Answers <small>(comma-separated, optional)</small></label>
                <input type="text" id="exSAAlternatives" placeholder="alt1, alt2, alt3">
            </div>
        `;
    } else if (type === 'true_false') {
        fieldsDiv.innerHTML = `
            <div class="form-group">
                <label>Statement *</label>
                <input type="text" id="exTFStatement" placeholder="Enter the statement" required>
            </div>
            <div class="form-group">
                <label>Correct Answer *</label>
                <select id="exTFAnswer" required>
                    <option value="">-- Select --</option>
                    <option value="true">True</option>
                    <option value="false">False</option>
                </select>
            </div>
        `;
    }
}

async function handleCreateExercise(event) {
    event.preventDefault();

    const type = document.getElementById('exType').value;
    const conceptSelect = document.getElementById('exConcept');
    const conceptId = parseInt(conceptSelect.value);
    const title = document.getElementById('exTitle').value;
    const difficulty = document.getElementById('exDifficulty').value;
    const errorType = document.getElementById('exErrorType').value || null;
    const isDiagnostic = document.getElementById('exDiagnostic').checked;

    if (!type || !conceptId || !title || !difficulty) {
        alert('Please fill in all required fields');
        return;
    }

    // Only mcq, true_false, and short_answer are supported in the diagnostic flow
    if (isDiagnostic && !['mcq', 'true_false', 'short_answer'].includes(type)) {
        alert('Diagnostic exercises must be MCQ, True/False, or Short Answer.\nPlease change the type or uncheck Diagnostic.');
        return;
    }

    // Derive module_id and sequence_id from the selected concept option
    const selectedOption = conceptSelect.options[conceptSelect.selectedIndex];
    const moduleId = parseInt(selectedOption.dataset.moduleId) || 1;
    const sequenceId = parseInt(selectedOption.dataset.sequenceId) || 1;

    let contentJson = {};

    if (type === 'mcq') {
        const question = document.getElementById('exMCQQuestion').value;
        const options = document.getElementById('exMCQOptions').value.split(',').map(o => o.trim());
        const correctIdx = parseInt(document.getElementById('exMCQCorrect').value);
        contentJson = { question, options, correct_option: correctIdx, explanation: '' };
    } else if (type === 'short_answer') {
        const altsRaw = document.getElementById('exSAAlternatives')?.value || '';
        const alternatives = altsRaw ? altsRaw.split(',').map(a => a.trim()).filter(Boolean) : [];
        contentJson = {
            question: document.getElementById('exSAQuestion').value,
            correct_answer: document.getElementById('exSAAnswer').value,
            alternative_answers: alternatives
        };
    } else if (type === 'true_false') {
        contentJson = {
            statement: document.getElementById('exTFStatement').value,
            correct_answer: document.getElementById('exTFAnswer').value === 'true'
        };
    }

    try {
        await adminAPI.createExercise({
            title,
            description: '',
            module_id: moduleId,
            sequence_id: sequenceId,
            concept_id: conceptId,
            difficulty,
            exercise_type: type,
            is_diagnostic: isDiagnostic,
            error_type_targeted: errorType,
            content_json: contentJson
        });

        alert('Exercise created successfully');
        hideCreateExerciseForm();
        loadExercises();
    } catch (error) {
        alert('Error creating exercise: ' + error.message);
    }
}

async function editExercise(exerciseId) {
    try {
        const ex = await adminAPI.getExerciseDetails(exerciseId);

        document.getElementById('editExId').value = ex.id;
        document.getElementById('editExTitle').value = ex.title;
        document.getElementById('editExDifficulty').value = ex.difficulty;
        document.getElementById('editExDiagnostic').checked = ex.is_diagnostic;

        const errorSelect = document.getElementById('editExErrorType');
        errorSelect.value = ex.error_type_targeted || '';

        document.getElementById('editExContentJson').value =
            ex.content_json ? JSON.stringify(ex.content_json, null, 2) : '';

        document.getElementById('editExerciseForm').style.display = 'flex';
    } catch (error) {
        alert('Error loading exercise: ' + error.message);
    }
}

function hideEditExerciseForm() {
    document.getElementById('editExerciseForm').style.display = 'none';
}

async function handleEditExercise(event) {
    event.preventDefault();

    const exerciseId = document.getElementById('editExId').value;
    const contentRaw = document.getElementById('editExContentJson').value.trim();

    let contentJson = null;
    if (contentRaw) {
        try {
            contentJson = JSON.parse(contentRaw);
        } catch (e) {
            alert('Invalid JSON in Content JSON field: ' + e.message);
            return;
        }
    }

    const updateData = {
        title: document.getElementById('editExTitle').value,
        difficulty: document.getElementById('editExDifficulty').value,
        is_diagnostic: document.getElementById('editExDiagnostic').checked,
        error_type_targeted: document.getElementById('editExErrorType').value || null,
        content_json: contentJson,
    };

    try {
        await adminAPI.updateExercise(exerciseId, updateData);
        alert('Exercise updated successfully');
        hideEditExerciseForm();
        loadExercises();
    } catch (error) {
        alert('Error updating exercise: ' + error.message);
    }
}

async function deleteExerciseConfirm(exerciseId) {
    if (confirm('Permanently delete this exercise and all its attempt records? This cannot be undone.')) {
        try {
            await adminAPI.deleteExercise(exerciseId);
            alert('Exercise deleted');
            loadExercises();
        } catch (error) {
            alert('Error deleting exercise: ' + error.message);
        }
    }
}

async function activateExerciseConfirm(exerciseId) {
    try {
        await adminAPI.activateExercise(exerciseId);
        alert('Exercise activated');
        loadExercises();
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

async function deactivateExerciseConfirm(exerciseId) {
    try {
        await adminAPI.deactivateExercise(exerciseId);
        alert('Exercise deactivated');
        loadExercises();
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

// =================================================================
// ANALYTICS
// =================================================================

async function loadAnalytics() {
    try {
        const analytics = await adminAPI.getAnalytics();

        document.getElementById('analyticsStudents').textContent = analytics.total_students;
        document.getElementById('analyticsAvgMastery').textContent = Math.round(analytics.average_student_mastery * 100) + '%';
        document.getElementById('analyticsExercises').textContent = analytics.total_exercises;
        document.getElementById('analyticsDiagnostic').textContent = Math.round(analytics.diagnostic_completion_rate) + '%';

        // Weakest concepts
        const weakestHtml = analytics.weakest_concepts.map(c => `
            <div class="concept-stat">
                <strong>${c.concept_name}</strong>
                <div class="stat-bar"><div style="width: ${c.average_mastery * 100}%"></div></div>
                <small>${Math.round(c.average_mastery * 100)}% avg mastery</small>
            </div>
        `).join('');
        document.getElementById('weakestConceptsList').innerHTML = weakestHtml || '<p>No data</p>';

        // Common errors
        const errorsHtml = analytics.most_common_errors.map(e => `
            <div class="error-stat">
                <strong>${e.error_type}</strong>
                <span class="count">${e.frequency} occurrences</span>
            </div>
        `).join('');
        document.getElementById('commonErrorsList').innerHTML = errorsHtml || '<p>No data</p>';

    } catch (error) {
        console.error('Analytics error:', error);
        alert('Error loading analytics: ' + error.message);
    }
}

// =================================================================
// LOGS
// =================================================================

async function loadLogs() {
    try {
        const data = await adminAPI.getLogs();

        const tableBody = document.getElementById('logsTableBody');
        tableBody.innerHTML = data.logs.map(log => `
            <tr>
                <td>${log.id}</td>
                <td>${log.admin_username}</td>
                <td>${log.action_type.replace(/_/g, ' ')}</td>
                <td>${log.entity}</td>
                <td>${log.entity_id || '—'}</td>
                <td>${new Date(log.timestamp).toLocaleString()}</td>
                <td><small>${JSON.stringify(log.details || {})}</small></td>
            </tr>
        `).join('');

    } catch (error) {
        console.error('Logs error:', error);
        alert('Error loading logs: ' + error.message);
    }
}

function filterLogs() {
    // Implement log filtering
    loadLogs();
}

// =================================================================
// LOGOUT
// =================================================================
