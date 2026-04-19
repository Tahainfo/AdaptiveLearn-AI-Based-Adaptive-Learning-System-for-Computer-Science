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

    try {
        diagnosticQuestions = await api.getDiagnosticQuestions(conceptId);
        
        const html = diagnosticQuestions.map((q, idx) => `
            <div class="question-item">
                <h4>Question ${idx + 1}</h4>
                <p>${q.question}</p>
                <div class="options">
                    ${q.options.map((opt, optIdx) => `
                        <label class="option-input">
                            <input type="radio" name="q${idx}" value="${optIdx}" required>
                            ${opt}
                        </label>
                    `).join('')}
                </div>
            </div>
        `).join('');

        document.getElementById('questionsContainer').innerHTML = html;
        document.getElementById('diagnosticStep1').style.display = 'none';
        document.getElementById('diagnosticStep2').style.display = 'block';

    } catch (error) {
        alert('Failed to load questions: ' + error.message);
    }
}

async function submitDiagnostic() {
    const answers = [];

    diagnosticQuestions.forEach((q, idx) => {
        const selected = document.querySelector(`input[name="q${idx}"]:checked`);
        if (selected) {
            answers.push({
                question_id: idx,
                selected_index: parseInt(selected.value)
            });
        }
    });

    if (answers.length !== diagnosticQuestions.length) {
        alert('Please answer all questions');
        return;
    }

    try {
        const results = await api.submitDiagnostic(currentDiagnosticConcept, answers);
        
        const html = `
            <h3>${results.concept_name}</h3>
            <p><strong>Score:</strong> ${Math.round(results.score)}%</p>
            <p><strong>Mastery Level:</strong> ${Math.round(results.mastery_level * 100)}%</p>
            <p style="margin-top: 1rem; color: #666;">
                Your mastery level has been recorded. You can now proceed with exercises for this concept.
            </p>
        `;

        document.getElementById('resultsContent').innerHTML = html;
        document.getElementById('diagnosticStep2').style.display = 'none';
        document.getElementById('diagnosticResults').style.display = 'block';

    } catch (error) {
        alert('Failed to submit test: ' + error.message);
    }
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
        
        // Get diagnostic questions for all concepts in this sequence
        const allQuestions = [];
        
        for (const concept of sequence.concepts) {
            try {
                const questions = await api.getDiagnosticQuestionsForConcept(concept.id);
                allQuestions.push(...questions.map(q => ({ ...q, concept_id: concept.id, concept_name: concept.name })));
            } catch (e) {
                console.warn('No questions for concept:', concept.name);
            }
        }
        
        if (allQuestions.length === 0) {
            alert('No diagnostic questions available for this sequence');
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
    const questionHtml = `
        <div class="question-item">
            <h4>Question ${index + 1} - ${question.concept_name}</h4>
            <p>${question.question}</p>
            <div class="options">
                ${question.options.map((opt, optIdx) => {
                    const isChecked = fullscreenDiagnosticAnswers[index] === optIdx ? 'checked' : '';
                    return `
                        <label class="option-input">
                            <input type="radio" name="currentQuestion" value="${optIdx}" ${isChecked} 
                                   onchange="fullscreenDiagnosticAnswers[${index}] = ${optIdx}">
                            ${opt}
                        </label>
                    `;
                }).join('')}
            </div>
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
        if (fullscreenDiagnosticAnswers[i] === undefined) {
            unanswered.push(i + 1);
        }
    }
    
    if (unanswered.length > 0) {
        alert(`Please answer all questions. Unanswered: Question(s) ${unanswered.join(', ')}`);
        return;
    }
    
    // Prepare answers
    const answers = diagnosticQuestions.map((q, idx) => ({
        question_id: q.id || idx,
        selected_index: fullscreenDiagnosticAnswers[idx],
        concept_id: q.concept_id
    }));
    
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
    // Show navbar again
    document.querySelector('.navbar').style.display = '';
    
    // Navigate back to dashboard
    setTimeout(() => {
        navigateTo('dashboard');
        loadDashboard();
        
        // Show results message
        let resultMessage = '✅ Diagnostic Test Completed!\n\nResults:\n';
        if (Array.isArray(results)) {
            results.forEach(result => {
                resultMessage += `\n${result.concept_name}: ${Math.round(result.score)}%`;
            });
        } else {
            resultMessage += `\nOverall Score: ${Math.round(results.score)}%`;
        }
        
        alert(resultMessage);
    }, 500);
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
