/* Main Application Logic */

let currentExercise = null;
let currentDiagnosticConcept = null;
let diagnosticQuestions = [];
let hintLevel = 0;

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    if (api.token) {
        showPage('dashboard');
        loadDashboard();
    } else {
        showPage('login');
    }
});

// ======================
// PAGE NAVIGATION
// ======================

function showPage(pageId) {
    document.querySelectorAll('.page').forEach(page => {
        page.classList.remove('active');
    });
    
    const page = document.getElementById(pageId);
    if (page) {
        page.classList.add('active');
        
        // Hide/show nav menu based on page type
        const navbar = document.getElementById('navMenu');
        if (pageId === 'login') {
            navbar.style.display = 'none';
            document.querySelector('.navbar').style.display = 'none';
        } else if (pageId === 'sequenceDiagnosticTest') {
            navbar.style.display = 'none';
            document.querySelector('.navbar').style.display = 'none';
        } else {
            navbar.style.display = 'flex';
            document.querySelector('.navbar').style.display = '';
        }
    }
}

function navigateTo(pageId) {
    if (pageId === 'dashboard') {
        loadDashboard();
    } else if (pageId === 'exercise') {
        loadExercise();
    } else if (pageId === 'diagnostic') {
        loadDiagnosticConcepts();
    }
    showPage(pageId);
}

// ======================
// AUTHENTICATION
// ======================

function showRegister() {
    document.getElementById('loginForm').style.display = 'none';
    document.getElementById('registerForm').style.display = 'block';
}

function showLogin() {
    document.getElementById('loginForm').style.display = 'block';
    document.getElementById('registerForm').style.display = 'none';
}

async function handleLogin() {
    const username = document.getElementById('loginUsername').value.trim();
    const password = document.getElementById('loginPassword').value.trim();

    if (!username || !password) {
        alert('Please fill in all fields');
        return;
    }

    try {
        await api.login(username, password);
        showPage('dashboard');
        loadDashboard();
    } catch (error) {
        alert('Login failed: ' + error.message);
    }
}

async function handleRegister() {
    const username = document.getElementById('regUsername').value.trim();
    const email = document.getElementById('regEmail').value.trim();
    const password = document.getElementById('regPassword').value.trim();

    if (!username || !email || !password) {
        alert('Please fill in all fields');
        return;
    }

    try {
        await api.register(username, email, password);
        alert('Registration successful! Please login.');
        showLogin();
    } catch (error) {
        alert('Registration failed: ' + error.message);
    }
}

function logout() {
    if (confirm('Are you sure you want to logout?')) {
        api.logout();
        showPage('login');
        showLogin();
    }
}

// ======================
// DASHBOARD
// ======================

async function loadDashboard() {
    try {
        const dashboard = await api.getDashboard();
        const stats = await api.getExerciseStats();

        // Update statistics
        const avgMastery = dashboard.statistics.average_mastery;
        document.getElementById('overallMastery').textContent = 
            Math.round(avgMastery * 100) + '%';
        document.getElementById('totalAttempts').textContent = 
            stats.total_attempts;
        document.getElementById('accuracyRate').textContent = 
            Math.round(stats.overall_accuracy) + '%';

        // Mastery message
        updateMasteryMessage(avgMastery);

        // Load modules mastery
        await loadModulesMastery();

        // Recommendations
        const recommendations = await api.getRecommendations();
        loadRecommendations(recommendations);

    } catch (error) {
        console.error('Dashboard load error:', error);
        alert('Failed to load dashboard: ' + error.message);
    }
}

async function loadModulesMastery() {
    try {
        // Fetch all modules
        const modules = await api.getAllModules();
        
        let treeHtml = '';
        let moduleIndex = 0;
        
        for (const module of modules) {
            let moduleMasteryScore = 0;
            let totalConcepts = 0;
            let sequencesHtml = '';
            
            if (module.sequences && module.sequences.length > 0) {
                for (const sequence of module.sequences) {
                    try {
                        const sequenceDetails = await api.getSequenceDetails(sequence.id);
                        
                        let sequenceMastery = 0;
                        let conceptsHtml = '';
                        
                        if (sequenceDetails.concepts && sequenceDetails.concepts.length > 0) {
                            let totalMastery = 0;
                            for (const concept of sequenceDetails.concepts) {
                                const conceptMastery = (concept.mastery_level || 0) * 100;
                                totalMastery += (concept.mastery_level || 0);
                                totalConcepts++;
                                
                                // Create concept item
                                conceptsHtml += `
                                    <div class="tree-item level-3">
                                        <div class="tree-item-header">
                                            <div class="tree-toggle no-children">▶</div>
                                            <span class="tree-item-title">🔹 ${concept.name}</span>
                                            <span class="tree-item-percentage">${Math.round(conceptMastery)}%</span>
                                            <div class="tree-item-bar-container">
                                                <div class="tree-item-bar level-3">
                                                    <div class="tree-item-bar-fill" style="width: ${conceptMastery}%"></div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                `;
                            }
                            sequenceMastery = (totalMastery / sequenceDetails.concepts.length) * 100;
                            moduleMasteryScore += totalMastery;
                        }
                        
                        const sequenceId = `seq-${module.id}-${sequence.id}`;
                        sequencesHtml += `
                            <div class="tree-item level-2">
                                <div class="tree-item-header" onclick="toggleTreeItem('${sequenceId}')">
                                    <div class="tree-toggle expanded">▶</div>
                                    <span class="tree-item-title">📋 ${sequence.title}</span>
                                    <span class="tree-item-percentage">${Math.round(sequenceMastery)}%</span>
                                    <div class="tree-item-bar-container">
                                        <div class="tree-item-bar level-2">
                                            <div class="tree-item-bar-fill" style="width: ${sequenceMastery}%"></div>
                                        </div>
                                    </div>
                                </div>
                                <div class="tree-children" id="children-${sequenceId}">
                                    ${conceptsHtml}
                                </div>
                            </div>
                        `;
                    } catch (e) {
                        console.warn('Failed to load sequence details:', sequence.id);
                    }
                }
                
                // Calculate average mastery for module
                if (totalConcepts > 0) {
                    moduleMasteryScore = (moduleMasteryScore / totalConcepts) * 100;
                }
            }
            
            const moduleId = `mod-${module.id}`;
            treeHtml += `
                <div class="tree-item level-1">
                    <div class="tree-item-header" onclick="toggleTreeItem('${moduleId}')">
                        <div class="tree-toggle expanded">▶</div>
                        <span class="tree-item-title">📚 ${module.title}</span>
                        <span class="tree-item-percentage">${Math.round(moduleMasteryScore)}%</span>
                        <div class="tree-item-bar-container">
                            <div class="tree-item-bar level-1">
                                <div class="tree-item-bar-fill" style="width: ${moduleMasteryScore}%"></div>
                            </div>
                        </div>
                    </div>
                    <div class="tree-children" id="children-${moduleId}">
                        ${sequencesHtml}
                    </div>
                </div>
            `;
            
            moduleIndex++;
        }
        
        document.getElementById('masteryByModules').innerHTML = treeHtml || 
            '<p>Start taking exercises to build your mastery profile!</p>';
            
    } catch (error) {
        console.error('Failed to load modules mastery:', error);
        document.getElementById('masteryByModules').innerHTML = 
            '<p>Unable to load mastery data. Please try again.</p>';
    }
}

function toggleTreeItem(itemId) {
    const childrenDiv = document.getElementById(`children-${itemId}`);
    const headerDiv = event.currentTarget;
    const toggleBtn = headerDiv.querySelector('.tree-toggle');
    
    if (childrenDiv.classList.contains('collapsed')) {
        // Expand
        childrenDiv.classList.remove('collapsed');
        toggleBtn.classList.add('expanded');
    } else {
        // Collapse
        childrenDiv.classList.add('collapsed');
        toggleBtn.classList.remove('expanded');
    }
}

function updateMasteryMessage(mastery) {
    let message = '';
    if (mastery < 0.2) {
        message = 'You\'re just getting started! Keep learning.';
    } else if (mastery < 0.4) {
        message = 'Good progress! Keep practicing.';
    } else if (mastery < 0.6) {
        message = 'You\'re developing well. Stay consistent!';
    } else if (mastery < 0.8) {
        message = 'Great mastery! You\'re doing excellent.';
    } else {
        message = 'Outstanding! You\'ve mastered most concepts!';
    }
    document.getElementById('masteryMessage').textContent = message;
}

function loadRecommendations(recommendations) {
    const next = recommendations.next_action;
    
    let html = `
        <div class="recommendation-item" style="margin-bottom: 1rem;">
            <div class="recommendation-text">
                <h4>Your Next Step</h4>
                <p><strong>${next.recommended_action || next.action}</strong>: ${next.reason}</p>
            </div>
        </div>
    `;

    if (recommendations.algorithmics_path) {
        html += '<h3>Algorithmics Path</h3>';
        recommendations.algorithmics_path.forEach(item => {
            const statusColor = item.status === 'mastered' ? '#16a34a' : 
                               item.status === 'developing' ? '#2563eb' : '#f59e0b';
            html += `
                <div class="recommendation-item">
                    <div class="recommendation-text">
                        <h4>${item.concept_name}</h4>
                        <p>Status: <span style="color: ${statusColor}; font-weight: bold;">${item.status}</span></p>
                    </div>
                </div>
            `;
        });
    }

    document.getElementById('recommendations').innerHTML = html;
}

// ======================
// EXERCISE MODE
// ======================

async function loadExercise() {
    const loading = document.getElementById('exerciseLoading');
    const content = document.getElementById('exerciseContent');
    
    loading.style.display = 'block';
    content.style.display = 'none';
    document.getElementById('feedbackContainer').style.display = 'none';
    document.getElementById('studentAnswer').value = '';
    hintLevel = 0;
    document.getElementById('hintDisplay').style.display = 'none';

    try {
        const response = await api.getNextExercise();
        
        if (response.type === 'diagnostic') {
            alert('Please complete a diagnostic test first!');
            navigateTo('diagnostic');
            return;
        }

        currentExercise = response;
        
        document.getElementById('exerciseTitle').textContent = 
            `Exercise: ${response.concept_name} (${response.difficulty})`;
        document.getElementById('exercisePrompt').innerHTML = 
            response.exercise.replace(/\n/g, '<br>');

        loading.style.display = 'none';
        content.style.display = 'block';

    } catch (error) {
        loading.textContent = 'Error loading exercise: ' + error.message;
    }
}

async function submitAnswer() {
    const answer = document.getElementById('studentAnswer').value.trim();
    
    if (!answer) {
        alert('Please enter your answer');
        return;
    }

    try {
        const result = await api.submitExerciseAnswer(currentExercise.exercise_id, answer);
        
        const container = document.getElementById('feedbackContainer');
        const content = document.getElementById('feedbackContent');
        
        const isCorrect = result.is_correct;
        container.className = 'feedback-box ' + (isCorrect ? 'correct' : 'incorrect');
        
        content.innerHTML = `
            <h3>${isCorrect ? '✅ Correct!' : '❌ Not Quite Right'}</h3>
            <p><strong>Feedback:</strong> ${result.feedback}</p>
            <p><strong>Hint:</strong> ${result.hint}</p>
            <p><strong>Your New Mastery:</strong> ${Math.round(result.new_mastery * 100)}%</p>
        `;
        
        container.style.display = 'block';
        document.getElementById('studentAnswer').disabled = true;
        document.querySelector('button[onclick="submitAnswer()"]').disabled = true;

    } catch (error) {
        alert('Error submitting answer: ' + error.message);
    }
}

async function getNextExercise() {
    loadExercise();
}

async function showHint() {
    if (hintLevel >= 3) {
        alert('No more hints available');
        return;
    }

    hintLevel++;

    try {
        const hint = await api.getExerciseHint(currentExercise.exercise_id, hintLevel);
        const display = document.getElementById('hintDisplay');
        display.innerHTML = `<strong>Hint ${hintLevel}:</strong> ${hint.hint || currentExercise.hints[hintLevel - 1]}`;
        display.style.display = 'block';

    } catch (error) {
        if (currentExercise.hints && currentExercise.hints[hintLevel - 1]) {
            const display = document.getElementById('hintDisplay');
            display.innerHTML = `<strong>Hint ${hintLevel}:</strong> ${currentExercise.hints[hintLevel - 1]}`;
            display.style.display = 'block';
        } else {
            alert('Could not load hint: ' + error.message);
        }
    }
}

// ======================
// DIAGNOSTIC TEST
// ======================

async function loadDiagnosticConcepts() {
    try {
        const concepts = await api.getDiagnosticConcepts();
        
        const html = concepts.map(concept => `
            <div class="concept-card" onclick="selectDiagnosticConcept(${concept.id}, this)">
                <h4>${concept.name}</h4>
                <p style="font-size: 0.9rem; color: #666;">${concept.domain}</p>
            </div>
        `).join('');

        document.getElementById('conceptList').innerHTML = html;

    } catch (error) {
        alert('Failed to load concepts: ' + error.message);
    }
}

async function selectDiagnosticConcept(conceptId, element) {
    currentDiagnosticConcept = conceptId;

    document.querySelectorAll('.concept-card').forEach(card => {
        card.classList.remove('selected');
    });
    element.classList.add('selected');

    const submitBtn = document.querySelector('#diagnosticStep2 button[onclick="submitDiagnostic()"]');

    try {
        diagnosticQuestions = await api.getDiagnosticQuestions(conceptId);

        if (diagnosticQuestions.length === 0) {
            document.getElementById('questionsContainer').innerHTML = `
                <div style="text-align:center; padding: 2rem; color: #64748b;">
                    <p style="font-size: 2rem; margin-bottom: 0.5rem;">📭</p>
                    <p style="font-size: 1.1rem; font-weight: 600; color: #334155; margin-bottom: 0.5rem;">
                        No diagnostic exercises available yet
                    </p>
                    <p>The administrator has not added any diagnostic exercises for this concept.<br>
                       Please select a different concept or check back later.</p>
                </div>`;
            if (submitBtn) submitBtn.style.display = 'none';
            document.getElementById('diagnosticStep1').style.display = 'none';
            document.getElementById('diagnosticStep2').style.display = 'block';
            return;
        }

        const html = diagnosticQuestions.map((q, idx) => {
            const inputHtml = q.input_type === 'text'
                ? `<input type="text" name="q${idx}" class="text-answer-input"
                          placeholder="Type your answer here" autocomplete="off">`
                : (q.options || []).map((opt, optIdx) => `
                        <label class="option-input">
                            <input type="radio" name="q${idx}" value="${optIdx}" required>
                            ${opt}
                        </label>`).join('');

            return `
            <div class="question-item">
                <h4>Question ${idx + 1}</h4>
                <p>${q.question}</p>
                <div class="options">${inputHtml}</div>
            </div>`;
        }).join('');

        document.getElementById('questionsContainer').innerHTML = html;
        if (submitBtn) submitBtn.style.display = '';
        document.getElementById('diagnosticStep1').style.display = 'none';
        document.getElementById('diagnosticStep2').style.display = 'block';

    } catch (error) {
        alert('Failed to load questions: ' + error.message);
    }
}

async function submitDiagnostic() {
    const answers = [];

    diagnosticQuestions.forEach((q, idx) => {
        if (q.input_type === 'text') {
            const input = document.querySelector(`input[name="q${idx}"]`);
            if (input && input.value.trim()) {
                answers.push({
                    question_id: q.id,
                    selected_index: -1,
                    text_answer: input.value.trim()
                });
            }
        } else {
            const selected = document.querySelector(`input[name="q${idx}"]:checked`);
            if (selected) {
                answers.push({
                    question_id: q.id,
                    selected_index: parseInt(selected.value)
                });
            }
        }
    });

    if (answers.length !== diagnosticQuestions.length) {
        alert('Please answer all questions');
        return;
    }

    try {
        const results = await api.submitDiagnostic(currentDiagnosticConcept, answers);
        document.getElementById('diagnosticStep2').style.display = 'none';
        showDiagnosticReview(diagnosticQuestions, answers, results);
    } catch (error) {
        alert('Failed to submit test: ' + error.message);
    }
}

function retakeDiagnostic() {
    document.getElementById('diagnosticReview').style.display = 'none';
    document.getElementById('diagnosticStep1').style.display = 'block';
    diagnosticQuestions = [];
    currentDiagnosticConcept = null;
}

// ======================
// MODULES & CURRICULUM
// ======================

async function loadModules() {
    try {
        const modules = await api.getAllModules();
        
        const modulesHtml = modules.map(module => `
            <div class="module-card" onclick="openModuleModal(${module.id})">
                <h3>${module.title}</h3>
                <p>${module.description || ''}</p>
                <div class="module-sequences-count">
                    ${module.sequences ? module.sequences.length : 0} sequences
                </div>
            </div>
        `).join('');

        document.getElementById('modulesList').innerHTML = modulesHtml;

    } catch (error) {
        console.error('Failed to load modules:', error);
        document.getElementById('modulesList').innerHTML = '<p>Error loading modules</p>';
    }
}

async function openModuleModal(moduleId) {
    try {
        const module = await api.getModuleDetails(moduleId);
        
        document.getElementById('moduleTitle').textContent = module.title;
        document.getElementById('moduleDescription').textContent = module.description || '';
        
        const sequencesHtml = module.sequences.map(sequence => `
            <div class="sequence-item">
                <h4>${sequence.title}</h4>
                <p class="concepts-count">${sequence.concepts ? sequence.concepts.length : 0} concepts/notions</p>
                <button onclick="startSequenceDiagnostic(${sequence.id}, '${sequence.title.replace(/'/g, "\\'")}')">
                    📝 Start Diagnostic Test
                </button>
            </div>
        `).join('');

        document.getElementById('sequencesList').innerHTML = sequencesHtml;
        document.getElementById('moduleModal').style.display = 'block';

    } catch (error) {
        alert('Failed to load module: ' + error.message);
    }
}

function closeModuleModal() {
    document.getElementById('moduleModal').style.display = 'none';
}

async function startSequenceDiagnostic(sequenceId, sequenceTitle) {
    try {
        const sequence = await api.getSequenceDetails(sequenceId);
        
        // Fetch admin-created diagnostic exercises for every concept in this sequence
        const allQuestions = [];

        for (const concept of sequence.concepts) {
            try {
                const questions = await api.getDiagnosticQuestionsForConcept(concept.id);
                if (questions.length > 0) {
                    allQuestions.push(...questions.map(q => ({
                        ...q,
                        concept_id: concept.id,
                        concept_name: concept.name
                    })));
                }
            } catch (e) {
                console.warn('Could not load questions for concept:', concept.name);
            }
        }

        if (allQuestions.length === 0) {
            closeModuleModal();
            // Build a friendly modal-style message
            const overlay = document.createElement('div');
            overlay.style.cssText = `
                position:fixed; inset:0; background:rgba(0,0,0,.5);
                display:flex; align-items:center; justify-content:center; z-index:9999;`;
            overlay.innerHTML = `
                <div style="background:#fff; border-radius:12px; padding:2rem 2.5rem;
                            max-width:420px; text-align:center; box-shadow:0 8px 32px rgba(0,0,0,.2);">
                    <p style="font-size:2.5rem; margin:0 0 .5rem;">📭</p>
                    <h3 style="margin:0 0 .75rem; color:#1e293b;">No Diagnostic Exercises Yet</h3>
                    <p style="color:#64748b; margin:0 0 1.5rem; line-height:1.6;">
                        The administrator has not added any diagnostic exercises
                        for the <strong>${sequenceTitle}</strong> sequence yet.<br><br>
                        Please ask your teacher to create diagnostic exercises before
                        this test becomes available.
                    </p>
                    <button onclick="this.closest('div[style*=fixed]').remove()"
                            style="background:#2563eb; color:#fff; border:none; border-radius:8px;
                                   padding:.65rem 1.5rem; font-size:1rem; cursor:pointer;">
                        OK
                    </button>
                </div>`;
            document.body.appendChild(overlay);
            return;
        }
        
        diagnosticQuestions = allQuestions;
        currentSequenceDiagnosticId = sequenceId;
        currentSequenceDiagnosticTitle = sequenceTitle;
        currentFullscreenDiagnosticIndex = 0;
        
        // Store answers for each question
        fullscreenDiagnosticAnswers = {};
        
        // Close module modal and open fullscreen page
        closeModuleModal();
        
        // Set header
        document.getElementById('testSequenceName').textContent = sequenceTitle;
        document.getElementById('testSequenceDesc').textContent = `Test covering ${sequence.concepts.length} concepts`;
        
        // Display first question
        showFullscreenQuestion(0);
        
        // Navigate to fullscreen test
        navigateToFullscreenDiagnostic();
        
        // Request fullscreen after a short delay
        setTimeout(() => {
            requestFullscreen();
        }, 300);

    } catch (error) {
        alert('Failed to load diagnostic: ' + error.message);
    }
}

function closeSequenceDiagnosticModal() {
    document.getElementById('sequenceDiagnosticModal').style.display = 'none';
}

// ===== FULLSCREEN DIAGNOSTIC TEST FUNCTIONS =====

let currentSequenceDiagnosticId = null;
let currentSequenceDiagnosticTitle = null;
let currentFullscreenDiagnosticIndex = 0;
let fullscreenDiagnosticAnswers = {};

function navigateToFullscreenDiagnostic() {
    // Hide navbar
    document.querySelector('.navbar').style.display = 'none';
    
    // Show fullscreen test page
    showPage('sequenceDiagnosticTest');
}

function showFullscreenQuestion(index) {
    if (index < 0 || index >= diagnosticQuestions.length) return;
    
    currentFullscreenDiagnosticIndex = index;
    const question = diagnosticQuestions[index];
    
    // Update progress
    document.getElementById('questionProgress').textContent = 
        `${index + 1}/${diagnosticQuestions.length}`;
    
    const progressPercent = ((index + 1) / diagnosticQuestions.length) * 100;
    document.getElementById('progressFill').style.width = progressPercent + '%';
    
    // Display question
    let inputHtml;
    if (question.input_type === 'text') {
        const savedText = fullscreenDiagnosticAnswers[index] || '';
        inputHtml = `<input type="text" class="text-answer-input" id="fsTextAnswer"
                            value="${savedText}" autocomplete="off"
                            placeholder="Type your answer here"
                            oninput="fullscreenDiagnosticAnswers[${index}] = this.value">`;
    } else {
        inputHtml = (question.options || []).map((opt, optIdx) => {
            const isChecked = fullscreenDiagnosticAnswers[index] === optIdx ? 'checked' : '';
            return `
                <label class="option-input">
                    <input type="radio" name="currentQuestion" value="${optIdx}" ${isChecked}
                           onchange="fullscreenDiagnosticAnswers[${index}] = ${optIdx}">
                    ${opt}
                </label>`;
        }).join('');
    }

    const questionHtml = `
        <div class="question-item">
            <h4>Question ${index + 1} - ${question.concept_name}</h4>
            <p>${question.question}</p>
            <div class="options">${inputHtml}</div>
        </div>
    `;
    
    document.getElementById('fullscreenQuestionsContent').innerHTML = questionHtml;
    
    // Update button states
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const submitBtn = document.getElementById('submitBtn');
    
    // Show/hide previous button
    if (index === 0) {
        prevBtn.style.display = 'none';
    } else {
        prevBtn.style.display = 'block';
    }
    
    // Show next or submit button
    if (index === diagnosticQuestions.length - 1) {
        nextBtn.style.display = 'none';
        submitBtn.style.display = 'block';
    } else {
        nextBtn.style.display = 'block';
        submitBtn.style.display = 'none';
    }
}

function previousQuestion() {
    if (currentFullscreenDiagnosticIndex > 0) {
        showFullscreenQuestion(currentFullscreenDiagnosticIndex - 1);
    }
}

function nextQuestion() {
    if (currentFullscreenDiagnosticIndex < diagnosticQuestions.length - 1) {
        showFullscreenQuestion(currentFullscreenDiagnosticIndex + 1);
    }
}

function requestFullscreen() {
    const container = document.querySelector('.fullscreen-diagnostic-container');
    
    if (container.requestFullscreen) {
        container.requestFullscreen().catch(err => {
            console.log('Fullscreen request failed:', err);
        });
    } else if (container.webkitRequestFullscreen) {
        container.webkitRequestFullscreen();
    } else if (container.mozRequestFullScreen) {
        container.mozRequestFullScreen();
    } else if (container.msRequestFullscreen) {
        container.msRequestFullscreen();
    }
    
    // Prevent exiting fullscreen by intercepting ESC key
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    document.addEventListener('webkitfullscreenchange', handleFullscreenChange);
    document.addEventListener('mozfullscreenchange', handleFullscreenChange);
    document.addEventListener('msfullscreenchange', handleFullscreenChange);
    
    // Disable F11
    document.addEventListener('keydown', preventExitFullscreen);
}

function handleFullscreenChange() {
    // If user tries to exit fullscreen before submission, re-request it
    const isFullscreen = document.fullscreenElement || 
                        document.webkitFullscreenElement || 
                        document.mozFullScreenElement || 
                        document.msFullscreenElement;
    
    if (!isFullscreen && currentFullscreenDiagnosticIndex < diagnosticQuestions.length - 1) {
        // User tried to exit early - re-request fullscreen
        setTimeout(() => {
            const container = document.querySelector('.fullscreen-diagnostic-container');
            if (container) {
                if (container.requestFullscreen) {
                    container.requestFullscreen().catch(err => {
                        console.log('Fullscreen re-request failed:', err);
                    });
                }
            }
        }, 100);
    }
}

function preventExitFullscreen(e) {
    // Prevent F11 and other exit keys during test
    if ((e.key === 'F11' || e.keyCode === 122) && 
        currentFullscreenDiagnosticIndex < diagnosticQuestions.length - 1) {
        e.preventDefault();
    }
}

function exitFullscreen() {
    if (document.exitFullscreen) {
        document.exitFullscreen();
    } else if (document.webkitExitFullscreen) {
        document.webkitExitFullscreen();
    } else if (document.mozCancelFullScreen) {
        document.mozCancelFullScreen();
    } else if (document.msExitFullscreen) {
        document.msExitFullscreen();
    }
    
    // Remove event listeners
    document.removeEventListener('fullscreenchange', handleFullscreenChange);
    document.removeEventListener('webkitfullscreenchange', handleFullscreenChange);
    document.removeEventListener('mozfullscreenchange', handleFullscreenChange);
    document.removeEventListener('msfullscreenchange', handleFullscreenChange);
    document.removeEventListener('keydown', preventExitFullscreen);
}

async function submitFullscreenDiagnostic() {
    // Check if all questions are answered
    const unanswered = [];
    for (let i = 0; i < diagnosticQuestions.length; i++) {
        const val = fullscreenDiagnosticAnswers[i];
        const isText = diagnosticQuestions[i].input_type === 'text';
        if (val === undefined || (isText && String(val).trim() === '')) {
            unanswered.push(i + 1);
        }
    }

    if (unanswered.length > 0) {
        alert(`Please answer all questions. Unanswered: Question(s) ${unanswered.join(', ')}`);
        return;
    }

    // Prepare answers — text vs radio
    const answers = diagnosticQuestions.map((q, idx) => {
        const isText = q.input_type === 'text';
        return {
            question_id: q.id || idx,
            selected_index: isText ? -1 : fullscreenDiagnosticAnswers[idx],
            text_answer: isText ? String(fullscreenDiagnosticAnswers[idx] || '') : null,
            concept_id: q.concept_id
        };
    });
    
    try {
        // Submit diagnostic
        const results = await api.submitDiagnosticTest(answers);
        
        // Exit fullscreen
        exitFullscreen();
        
        // Show results
        showFullscreenResults(results);
        
    } catch (error) {
        alert('Failed to submit diagnostic: ' + error.message);
    }
}

function showFullscreenResults(results) {
    // Restore navbar and navigate to the diagnostic page review
    document.querySelector('.navbar').style.display = '';
    exitFullscreen();

    // Build the answers array from global state so the review can use it
    const answers = diagnosticQuestions.map((q, idx) => {
        const isText = q.input_type === 'text';
        return {
            question_id: q.id || idx,
            selected_index: isText ? -1 : (fullscreenDiagnosticAnswers[idx] ?? -1),
            text_answer: isText ? String(fullscreenDiagnosticAnswers[idx] || '') : null,
            concept_id: q.concept_id
        };
    });

    // Navigate to the diagnostic page and show the review
    navigateTo('diagnostic');
    showDiagnosticReview(diagnosticQuestions, answers, results);
}

async function submitSequenceDiagnostic() {
    const answers = [];

    diagnosticQuestions.forEach((q, idx) => {
        const selected = document.querySelector(`input[name="q${idx}"]:checked`);
        if (selected) {
            answers.push({
                question_id: q.id,
                selected_index: parseInt(selected.value),
                concept_id: q.concept_id
            });
        }
    });

    if (answers.length !== diagnosticQuestions.length) {
        alert('Please answer all questions');
        return;
    }

    try {
        const results = await api.submitDiagnosticTest(answers);
        
        let resultHtml = '<h3>Diagnostic Results</h3>';
        resultHtml += '<div class="results-summary">';
        
        if (Array.isArray(results)) {
            results.forEach(result => {
                resultHtml += `
                    <div class="result-item">
                        <h4>${result.concept_name}</h4>
                        <p><strong>Score:</strong> ${Math.round(result.score)}%</p>
                    </div>
                `;
            });
        } else {
            resultHtml += `
                <p><strong>Score:</strong> ${Math.round(results.score)}%</p>
                <p>Mastery recorded for this sequence.</p>
            `;
        }
        
        resultHtml += '</div>';
        resultHtml += '<button onclick="closeSequenceDiagnosticModal(); loadDashboard(); showPage(\'dashboard\')" class="btn-primary">Back to Dashboard</button>';

        document.getElementById('diagnosticQuestionsContainer').innerHTML = resultHtml;
        document.querySelector('#sequenceDiagnosticModal .modal-content button').style.display = 'none';

    } catch (error) {
        alert('Failed to submit diagnostic: ' + error.message);
    }
}

// Auto-load modules when dashboard loads
const originalLoadDashboard = loadDashboard;
loadDashboard = async function() {
    await originalLoadDashboard();
    await loadModules();
};

// =================================================================
// DIAGNOSTIC REVIEW  (shown after any diagnostic submit)
// =================================================================

// Cache so clicking "Explain" twice doesn't re-call the API
const _explanationCache = {};

/**
 * Resolve a student's answer for a question to human-readable text.
 */
function _resolveStudentAnswer(question, answer) {
    if (question.input_type === 'text') {
        return answer.text_answer || '(no answer)';
    }
    const idx = answer.selected_index;
    if (idx < 0) return '(not answered)';
    return (question.options && question.options[idx]) || `Option ${idx}`;
}

/**
 * Resolve the correct answer to human-readable text.
 */
function _resolveCorrectAnswer(question) {
    if (question.input_type === 'text') {
        return question.correct_answer || '';
    }
    const idx = question.correct_index ?? 0;
    return (question.options && question.options[idx]) || `Option ${idx}`;
}

/**
 * Determine if a student answer is correct.
 */
function _isAnswerCorrect(question, answer) {
    if (question.input_type === 'text') {
        const student = (answer.text_answer || '').trim().toLowerCase();
        const expected = (question.correct_answer || '').trim().toLowerCase();
        const alts = (question.alternative_answers || []).map(a => a.trim().toLowerCase());
        return student === expected || alts.includes(student);
    }
    return answer.selected_index === (question.correct_index ?? -99);
}

/**
 * Render the diagnostic review screen.
 * @param {Array}  questions  - diagnosticQuestions array
 * @param {Array}  answers    - answers array built at submit time
 * @param {Object|Array} results - backend scoring result(s)
 */
function showDiagnosticReview(questions, answers, results) {
    // Hide all other diagnostic sections
    ['diagnosticStep1', 'diagnosticStep2', 'diagnosticResults'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.style.display = 'none';
    });

    // --- Score banner ---
    let totalCorrect = 0;
    const answerMap = {};
    answers.forEach(a => { answerMap[a.question_id] = a; });

    questions.forEach(q => {
        const a = answerMap[q.id];
        if (a && _isAnswerCorrect(q, a)) totalCorrect++;
    });

    const pct = questions.length ? Math.round((totalCorrect / questions.length) * 100) : 0;
    let conceptLabel = '';
    if (Array.isArray(results)) {
        conceptLabel = results.map(r => r.concept_name).join(', ');
    } else if (results && results.concept_name) {
        conceptLabel = results.concept_name;
    }

    const masteryColor = pct >= 80 ? '#22c55e' : pct >= 50 ? '#f59e0b' : '#ef4444';

    document.getElementById('reviewScoreBanner').innerHTML = `
        <div class="score-left">
            <h2>${conceptLabel || 'Diagnostic Review'}</h2>
            <p>${totalCorrect} correct out of ${questions.length} questions</p>
        </div>
        <div class="score-right">
            <div class="score-circle" style="border-color:${masteryColor};">
                <span class="score-num" style="color:${masteryColor};">${pct}%</span>
                <span class="score-label">Score</span>
            </div>
        </div>`;

    // --- Question cards ---
    const cardsHtml = questions.map((q, idx) => {
        const answer = answerMap[q.id] || { selected_index: -1, text_answer: '' };
        const correct = _isAnswerCorrect(q, answer);
        const studentText = _resolveStudentAnswer(q, answer);
        const correctText = _resolveCorrectAnswer(q);

        const studentPillClass = correct ? 'student-correct' : 'student-wrong';
        const studentIcon = correct ? '✓' : '✗';

        const correctPillHtml = correct ? '' : `
            <span class="answer-pill correct-answer">
                <span class="pill-icon">✓</span> ${correctText}
            </span>`;

        return `
        <div class="review-card ${correct ? 'correct' : 'incorrect'}" id="review-card-${idx}">
            <div class="review-card-header">
                <span style="font-size:0.85rem;color:#64748b;font-weight:500;">
                    ${q.concept_name ? `<em>${q.concept_name}</em> · ` : ''}Q${idx + 1}
                </span>
                <span class="question-meta">${q.input_type === 'text' ? 'Short Answer' : q.options?.length === 2 ? 'True / False' : 'MCQ'}</span>
            </div>
            <div class="review-card-body">
                <p class="review-question-text">${q.question}</p>
                <div class="answer-row">
                    <span class="answer-pill ${studentPillClass}">
                        <span class="pill-icon">${studentIcon}</span> ${studentText}
                    </span>
                    ${correctPillHtml}
                </div>
                <button class="explain-btn" id="explain-btn-${idx}"
                        onclick="explainAnswer(${idx})">
                    ✨ Explain the correct answer
                </button>
                <div id="explanation-box-${idx}"></div>
            </div>
        </div>`;
    }).join('');

    document.getElementById('reviewQuestionsContainer').innerHTML = cardsHtml;

    // Show review section
    const reviewEl = document.getElementById('diagnosticReview');
    reviewEl.style.display = 'block';
    reviewEl.scrollIntoView({ behavior: 'smooth', block: 'start' });

    // Auto-generate the learning guide (async, non-blocking)
    _fetchAndRenderLearningGuide(questions, answers, conceptLabel);
}

/**
 * Called when a student clicks "Explain the correct answer" on a review card.
 * Calls the backend AI proxy, caches the result, renders it in the card.
 */
async function explainAnswer(questionIndex) {
    const cacheKey = questionIndex;
    const btn = document.getElementById(`explain-btn-${questionIndex}`);
    const box = document.getElementById(`explanation-box-${questionIndex}`);

    // Use cached explanation if already fetched
    if (_explanationCache[cacheKey]) {
        box.innerHTML = `
            <div class="explanation-box">
                <div class="explain-label">AI Explanation</div>
                ${_explanationCache[cacheKey]}
            </div>`;
        btn.style.display = 'none';
        return;
    }

    // Loading state
    btn.disabled = true;
    btn.innerHTML = `<span class="btn-spinner"></span> Generating…`;

    const q = diagnosticQuestions[questionIndex];
    if (!q) {
        btn.disabled = false;
        btn.innerHTML = '✨ Explain the correct answer';
        return;
    }

    // Build answer maps from DOM (review-card still holds the original question data)
    const studentText = q._reviewStudentAnswer || btn.closest('.review-card-body')
        .querySelector('.answer-pill:first-child')?.textContent?.trim().replace(/^[✓✗]\s*/, '') || '';
    const correctText = _resolveCorrectAnswer(q);

    // Determine if the student was correct by checking card class
    const card = document.getElementById(`review-card-${questionIndex}`);
    const isCorrect = card?.classList.contains('correct') ?? false;

    try {
        const data = await api.explainAnswer({
            concept_name: q.concept_name || 'Computer Science',
            question_text: q.question,
            exercise_type: q.input_type === 'text' ? 'short_answer' : 'mcq',
            student_answer: studentText,
            correct_answer: correctText,
            is_correct: isCorrect
        });

        _explanationCache[cacheKey] = data.explanation;

        box.innerHTML = `
            <div class="explanation-box">
                <div class="explain-label">AI Explanation</div>
                ${data.explanation}
            </div>`;
        btn.style.display = 'none';

    } catch (err) {
        box.innerHTML = `
            <div class="explanation-box explanation-error">
                Could not load explanation: ${err.message}
            </div>`;
        btn.disabled = false;
        btn.innerHTML = '✨ Explain the correct answer';
    }
}

// =================================================================
// LEARNING GUIDE  ("What to Learn From This Test")
// =================================================================

async function _fetchAndRenderLearningGuide(questions, answers, testTitle) {
    const skeleton = document.getElementById('learningGuideSkeleton');
    const guideEl  = document.getElementById('learningGuide');
    const contentEl = document.getElementById('learningGuideContent');

    if (!skeleton || !guideEl || !contentEl) return;

    // Show skeleton while loading
    skeleton.style.display = 'block';
    guideEl.style.display  = 'none';

    // Build payload: one entry per question
    const answerMap = {};
    answers.forEach(a => { answerMap[a.question_id] = a; });

    const questionResults = questions.map(q => {
        const answer  = answerMap[q.id] || {};
        const correct = _isAnswerCorrect(q, answer);
        return {
            question:       q.question,
            student_answer: _resolveStudentAnswer(q, answer),
            correct_answer: _resolveCorrectAnswer(q),
            is_correct:     correct,
            concept_name:   q.concept_name || ''
        };
    });

    try {
        const guide = await api.getLearningGuide({
            test_title:  testTitle || 'Diagnostic Test',
            questions:   questionResults
        });

        contentEl.innerHTML = _buildGuideHTML(guide);

        skeleton.style.display = 'none';
        guideEl.style.display  = 'block';

    } catch (err) {
        skeleton.style.display = 'none';
        // Show a quiet fallback — don't block the review page
        guideEl.style.display  = 'block';
        contentEl.innerHTML = `
            <div style="padding:1.5rem 2rem; color:#64748b; font-size:0.9rem; text-align:center;">
                ⚠️ Could not generate learning guide right now — ${err.message}<br>
                <button onclick="_retryLearningGuide()" style="margin-top:0.75rem;padding:0.4rem 1rem;
                    border:1.5px solid #6366f1;border-radius:6px;color:#6366f1;background:none;cursor:pointer;font-size:0.85rem;">
                    Try again
                </button>
            </div>`;
        // store for retry
        window._lastGuideArgs = [questions, answers, testTitle];
    }
}

function _retryLearningGuide() {
    const args = window._lastGuideArgs;
    if (args) _fetchAndRenderLearningGuide(...args);
}

function _buildGuideHTML(guide) {
    const sections = [];

    /* ── 1. Summary ── */
    if (guide.summary) {
        sections.push(`
        <div>
            <p class="lg-block-title">📊 Your Performance</p>
            <div class="lg-summary">${_esc(guide.summary)}</div>
        </div>`);
    }

    /* ── 2. Weak areas ── */
    if (guide.weak_areas && guide.weak_areas.length) {
        const chips = guide.weak_areas.map(w => `
            <div class="lg-chip">
                <div class="lg-chip-concept">⚠️ ${_esc(w.concept)}</div>
                <div class="lg-chip-gap">${_esc(w.gap)}</div>
            </div>`).join('');

        sections.push(`
        <div>
            <p class="lg-block-title">🎯 Areas to Focus On</p>
            <div class="lg-chips">${chips}</div>
        </div>`);
    }

    /* ── 3. Key lessons ── */
    if (guide.key_lessons && guide.key_lessons.length) {
        const lessons = guide.key_lessons.map((l, i) => `
            <div class="lg-lesson">
                <div class="lg-lesson-num">${i + 1}</div>
                <div class="lg-lesson-body">
                    <p class="lg-lesson-title">${_esc(l.title)}</p>
                    <p class="lg-lesson-content">${_esc(l.content)}</p>
                    ${l.tip ? `<span class="lg-lesson-tip">${_esc(l.tip)}</span>` : ''}
                </div>
            </div>`).join('');

        sections.push(`
        <div>
            <p class="lg-block-title">💡 Key Lessons</p>
            <div class="lg-lessons">${lessons}</div>
        </div>`);
    }

    /* ── 4. Action plan ── */
    if (guide.action_plan && guide.action_plan.length) {
        const items = guide.action_plan.map(s => `<li>${_esc(s)}</li>`).join('');
        sections.push(`
        <div>
            <p class="lg-block-title">✅ Your Action Plan</p>
            <ul class="lg-action-list">${items}</ul>
        </div>`);
    }

    /* ── 5. Strengths ── */
    if (guide.strengths) {
        sections.push(`
        <div>
            <p class="lg-block-title">⭐ What You Did Well</p>
            <div class="lg-strengths">
                <span class="lg-strengths-icon">🌟</span>
                <p class="lg-strengths-text">${_esc(guide.strengths)}</p>
            </div>
        </div>`);
    }

    return sections.join('');
}

/** Minimal HTML-escape to prevent XSS from AI output. */
function _esc(str) {
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}
