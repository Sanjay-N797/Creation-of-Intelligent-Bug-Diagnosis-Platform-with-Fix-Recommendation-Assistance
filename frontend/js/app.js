// ============================================================
// Main Application Controller — Bug Mission Control Edition
// Orchestrates UI elements and interacts via REST APIs
// ============================================================

class SmartBugAnalyzerApp {
  constructor() {
    this.currentSection = 'dashboard';
    this.currentAnalysis = null;
    this.currentBugId = null;
    this.activeChatBugId = null;
    this.lastSubmittedBugData = null;
    this.isMentorMode = false;
    this.recentBugsList = [];

    this._bindEvents();
    this._renderDashboard();
    this._renderKnowledgeBase();
    this._loadCategories();
  }

  // ========================
  // Event Binding
  // ========================
  _bindEvents() {
    // Sidebar navigation tabs
    document.querySelectorAll('.nav-tab').forEach(tab => {
      tab.addEventListener('click', (e) => {
        const target = e.currentTarget.dataset.section;
        if (target) this._switchSection(target);
      });
    });

    // Sidebar collapse toggle
    const toggleBtn = document.getElementById('sidebarToggleBtn');
    if (toggleBtn) {
      toggleBtn.addEventListener('click', () => {
        const sidebar = document.getElementById('appSidebar');
        const mainWrapper = document.getElementById('appMainWrapper');
        if (sidebar && mainWrapper) {
          sidebar.classList.toggle('collapsed');
          mainWrapper.classList.toggle('expanded');
        }
      });
    }

    // Top quick search focus shortcut
    const quickSearch = document.getElementById('topQuickSearch');
    if (quickSearch) {
      quickSearch.addEventListener('input', (e) => {
        const val = e.target.value.trim();
        if (val) {
          this._switchSection('knowledge-base');
          const kbSearch = document.getElementById('kbSearch');
          if (kbSearch) {
            kbSearch.value = val;
            this._filterKnowledgeBase();
          }
        }
      });
    }

    document.addEventListener('keydown', (e) => {
      if (e.key === '/' && document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'TEXTAREA') {
        e.preventDefault();
        const searchInput = document.getElementById('topQuickSearch');
        if (searchInput) searchInput.focus();
      }
      if (e.key === 'Escape') {
        this._closeModal();
        this._closeChatDrawer();
      }
    });

    const form = document.getElementById('bugForm');
    if (form) {
      form.addEventListener('submit', (e) => {
        e.preventDefault();
        this._handleBugSubmission();
      });
    }

    const clearBtn = document.getElementById('clearFormBtn');
    if (clearBtn) {
      clearBtn.addEventListener('click', () => this._clearForm());
    }

    const sampleBtn = document.getElementById('loadSampleBtn');
    if (sampleBtn) {
      sampleBtn.addEventListener('click', () => this._loadSampleBug());
    }

    const modalOverlay = document.getElementById('modalOverlay');
    if (modalOverlay) {
      modalOverlay.addEventListener('click', (e) => {
        if (e.target === modalOverlay) this._closeModal();
      });
    }

    const modalClose = document.getElementById('modalCloseBtn');
    if (modalClose) {
      modalClose.addEventListener('click', () => this._closeModal());
    }

    const kbSearch = document.getElementById('kbSearch');
    if (kbSearch) {
      kbSearch.addEventListener('input', (e) => this._filterKnowledgeBase());
    }

    const kbCategory = document.getElementById('kbCategoryFilter');
    if (kbCategory) {
      kbCategory.addEventListener('change', () => this._filterKnowledgeBase());
    }

    const kbSeverity = document.getElementById('kbSeverityFilter');
    if (kbSeverity) {
      kbSeverity.addEventListener('change', () => this._filterKnowledgeBase());
    }

    const resetBtn = document.getElementById('resetKbBtn');
    if (resetBtn) {
      resetBtn.addEventListener('click', async () => {
        if (confirm('Reset SQL database to sample data? This will reset all your added bugs.')) {
          try {
            await api.resetDatabase();
            await this._renderDashboard();
            await this._renderKnowledgeBase();
            await this._loadCategories();
            this._showToast('Database reset to sample data', 'info');
          } catch (err) {
            this._showToast('Failed to reset database: ' + err.message, 'error');
          }
        }
      });
    }

    document.querySelectorAll('.result-tab').forEach(tab => {
      tab.addEventListener('click', (e) => {
        this._switchResultTab(e.target.dataset.agent);
      });
    });

    // Code Doctor events
    const codeDoctorForm = document.getElementById('codeDoctorForm');
    if (codeDoctorForm) {
      codeDoctorForm.addEventListener('submit', (e) => {
        e.preventDefault();
        this._handleCodeReview();
      });
    }

    const loadSampleCodeBtn = document.getElementById('loadSampleCodeBtn');
    if (loadSampleCodeBtn) {
      loadSampleCodeBtn.addEventListener('click', () => this._loadSampleCode());
    }

    const clearCodeBtn = document.getElementById('clearCodeBtn');
    if (clearCodeBtn) {
      clearCodeBtn.addEventListener('click', () => {
        const input = document.getElementById('codeSnippetInput');
        if (input) input.value = '';
        const container = document.getElementById('codeReviewResultsContainer');
        if (container) container.style.display = 'none';
      });
    }

    const mentorToggle = document.getElementById('mentorModeToggle');
    if (mentorToggle) {
      mentorToggle.addEventListener('change', (e) => {
        this.isMentorMode = e.target.checked;
        this._showToast(`Mentor Mode ${this.isMentorMode ? 'Enabled' : 'Disabled'}`, 'info');
        if (this.currentAnalysis) {
          this._renderAnalysisResults(this.currentAnalysis, this.lastSubmittedBugData);
        }
      });
    }

    // Chat drawer events
    const chatForm = document.getElementById('chatForm');
    if (chatForm) {
      chatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        this._handleSendMessage();
      });
    }

    const closeChatBtn = document.getElementById('closeChatBtn');
    if (closeChatBtn) {
      closeChatBtn.addEventListener('click', () => this._closeChatDrawer());
    }

    const chatOverlay = document.getElementById('chatDrawerOverlay');
    if (chatOverlay) {
      chatOverlay.addEventListener('click', (e) => {
        if (e.target === chatOverlay) this._closeChatDrawer();
      });
    }
  }

  // ========================
  // Section Navigation
  // ========================
  _switchSection(section) {
    this.currentSection = section;

    document.querySelectorAll('.nav-tab').forEach(tab => {
      tab.classList.toggle('active', tab.dataset.section === section);
    });

    document.querySelectorAll('.section').forEach(sec => {
      sec.classList.toggle('active', sec.id === `section-${section}`);
    });

    if (section === 'dashboard') this._renderDashboard();
    if (section === 'knowledge-base') this._renderKnowledgeBase();
  }

  // ========================
  // Dashboard Rendering
  // ========================
  async _renderDashboard() {
    try {
      const stats = await api.getStats();
      this._updateElement('statTotal', stats.total);
      this._updateElement('statResolved', stats.resolved);
      this._updateElement('statOpen', stats.open);
      this._updateElement('statAvgTime', `${stats.avgResolutionDays}d`);
      this._updateElement('statRate', `${stats.resolutionRate}%`);

      // Fetch recent bugs list for the dashboard recent defects stream
      const bugs = await api.getBugs();
      this.recentBugsList = bugs || [];
      this._renderDashboardRecentBugs(this.recentBugsList.slice(0, 5));

      // Populate AI Inspector and Code Preview with top bug if available
      if (this.recentBugsList.length > 0) {
        this._inspectDashboardBug(this.recentBugsList[0]);
      }

      // Load Defect Intelligence Hub Analytics
      const analytics = await api.getAnalytics();
      this._renderDefectIntelligence(analytics);
    } catch (err) {
      console.error('Failed to load stats or analytics:', err);
    }
  }

  _renderDashboardRecentBugs(bugs) {
    const tbody = document.getElementById('dashboardRecentBugsBody');
    if (!tbody) return;

    if (!bugs || bugs.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="5" style="text-align: center; color: var(--text-muted); padding: 16px;">
            No bugs indexed yet. Submit a bug report in the Analyzer tab!
          </td>
        </tr>
      `;
      return;
    }

    tbody.innerHTML = bugs.map(bug => `
      <tr>
        <td style="font-family: var(--font-mono); font-size: 11px; color: var(--text-muted);">${bug.id}</td>
        <td class="bug-title-cell" onclick="app._showBugDetail('${bug.id}')">${this._escapeHtml(bug.title)}</td>
        <td><span class="badge badge-${bug.severity.toLowerCase()}">${bug.severity}</span></td>
        <td style="font-size: 11px;">${bug.category}</td>
        <td>
          <button class="btn btn-secondary btn-sm" style="padding: 2px 8px; font-size: 10px;" onclick="app._selectDashboardBug('${bug.id}')">
            INSPECT
          </button>
        </td>
      </tr>
    `).join('');
  }

  _selectDashboardBug(bugId) {
    const bug = this.recentBugsList.find(b => b.id === bugId);
    if (bug) {
      this._inspectDashboardBug(bug);
      this._showToast(`Loaded ${bug.id} into AI Inspector & Code Terminal`, 'info');
    }
  }

  _inspectDashboardBug(bug) {
    if (!bug) return;

    this.currentBugId = bug.id;

    // Update AI Diagnosis Inspector Panel
    const bugBadge = document.getElementById('dashboardSelectedBugId');
    if (bugBadge) {
      bugBadge.textContent = bug.id;
      bugBadge.className = `badge badge-${bug.severity.toLowerCase()}`;
    }

    const titleEl = document.getElementById('dashboardDiagnosisTitle');
    if (titleEl) titleEl.textContent = bug.title;

    const summaryEl = document.getElementById('dashboardDiagnosisSummary');
    if (summaryEl) summaryEl.textContent = bug.rootCause || bug.description || 'Defect indexed in SQLite DB. Ready for agent remediation.';

    // Update Terminal Code Preview Panel
    const codeLang = document.getElementById('dashboardCodeLang');
    if (codeLang) codeLang.textContent = (bug.category || 'STACK').toUpperCase();

    const codeFile = document.getElementById('dashboardCodeFilename');
    if (codeFile) codeFile.textContent = `${bug.id} // ${bug.category || 'ErrorTrace'}`;

    const codeBody = document.getElementById('dashboardCodeBody');
    if (codeBody) {
      if (bug.stackTrace) {
        codeBody.innerHTML = this._escapeHtml(bug.stackTrace);
      } else {
        codeBody.innerHTML = `[STACK TRACE FOR ${bug.id}]\nTitle: ${this._escapeHtml(bug.title)}\nCategory: ${bug.category}\nSeverity: ${bug.severity}\nStatus: ${bug.status}`;
      }
    }
  }

  _renderDefectIntelligence(analytics) {
    const riskGrid = document.getElementById('componentRiskGrid');
    const antiList = document.getElementById('antiPatternList');
    const recList = document.getElementById('teamRecommendationsList');

    if (riskGrid && analytics.categoryRisks) {
      riskGrid.innerHTML = analytics.categoryRisks.map(c => `
        <div style="background: var(--bg-terminal); border: 1px solid var(--border-subtle); padding: 12px; border-radius: var(--radius-sm);">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <span style="font-weight: 700; font-size: 13px; font-family: var(--font-mono);">${this._escapeHtml(c.category)}</span>
            <span class="badge ${c.riskScore >= 60 ? 'badge-critical' : c.riskScore >= 30 ? 'badge-medium' : 'badge-resolved'}" style="font-size: 10px;">
              ${c.riskLevel} (${c.riskScore})
            </span>
          </div>
          <div style="font-size: 11px; color: var(--text-secondary); font-family: var(--font-mono);">
            Total: <strong>${c.totalBugs}</strong> | Open: <strong style="color: var(--severity-critical);">${c.openBugs}</strong>
          </div>
        </div>
      `).join('');
    }

    if (antiList && analytics.antiPatterns) {
      antiList.innerHTML = analytics.antiPatterns.map(ap => `
        <div class="result-item warning" style="padding: 8px 12px; margin-bottom: 4px;">
          <div style="font-weight: 600; font-size: 12px; margin-bottom: 2px;">
            ${this._escapeHtml(ap.pattern)} <span class="badge badge-high" style="margin-left: 6px;">${ap.impact}</span>
          </div>
          <div style="font-size: 11px; color: var(--text-secondary);">
            <strong>Fix:</strong> ${this._escapeHtml(ap.recommendation)}
          </div>
        </div>
      `).join('');
    }

    if (recList && analytics.teamRecommendations) {
      recList.innerHTML = analytics.teamRecommendations.map(rec => `
        <div class="result-item success" style="font-size: 11px; padding: 6px 10px; margin-bottom: 4px;">
          + ${this._escapeHtml(rec)}
        </div>
      `).join('');
    }
  }

  // ========================
  // Categories
  // ========================
  async _loadCategories() {
    try {
      const categories = await api.getCategories();
      const catFilter = document.getElementById('kbCategoryFilter');
      if (catFilter) {
        catFilter.innerHTML = `<option value="All">All Categories</option>` + categories.map(cat =>
          `<option value="${cat}">${cat}</option>`
        ).join('');
      }
    } catch (err) {
      console.error('Failed to load categories:', err);
    }
  }

  // ========================
  // Bug Submission & Analysis Pipeline
  // ========================
  async _handleBugSubmission() {
    const title = document.getElementById('bugTitle').value.trim();
    const description = document.getElementById('bugDescription').value.trim();
    const stackTrace = document.getElementById('bugStackTrace').value.trim();
    const category = document.getElementById('bugCategory').value;

    const logFileInput = document.getElementById('bugLogFile');
    let logFileName = '';
    let logContent = '';
    if (logFileInput && logFileInput.files && logFileInput.files[0]) {
      const file = logFileInput.files[0];
      logFileName = file.name;
      try {
        logContent = await file.text();
      } catch (err) {
        console.error("Error reading attached file:", err);
      }
    }

    if (!title) {
      this._showToast('Please enter a bug title', 'error');
      return;
    }
    if (!description && !stackTrace && !logContent) {
      this._showToast('Please enter a description, stack trace, or attach a log file', 'error');
      return;
    }

    const bugReport = {
      title,
      description,
      stackTrace,
      category,
      logFileName,
      logContent
    };

    this._showPipeline();
    await this._runAnalysisPipeline(bugReport);
  }

  async _runAnalysisPipeline(bugReport) {
    this.lastSubmittedBugData = { ...bugReport };
    const pipeline = document.getElementById('pipelineContainer');
    const results = document.getElementById('resultsContainer');

    pipeline.classList.add('active');
    results.classList.remove('active');

    const steps = ['triage', 'log-analysis', 'root-cause', 'duplicate', 'remediation'];

    for (let i = 0; i < steps.length; i++) {
      const stepId = steps[i];
      this._updatePipelineStep(stepId, 'processing');
      for (let j = 0; j < i; j++) this._updatePipelineStep(steps[j], 'completed');
      for (let j = i + 1; j < steps.length; j++) this._updatePipelineStep(steps[j], 'pending');
      await this._delay(300);
    }

    try {
      const responseBug = await api.analyzeBug(bugReport);
      const analysisResults = responseBug.analysisResults || {};

      for (let i = 0; i < steps.length; i++) {
        this._updatePipelineStep(steps[i], 'completed');
      }

      const statusEl = document.getElementById('pipelineStatus');
      if (statusEl) {
        statusEl.innerHTML = '<span style="color: var(--severity-resolved)">✓ Python Agents pipeline completed</span>';
      }

      this.currentBugId = responseBug.id;
      this.currentAnalysis = analysisResults;

      await this._delay(300);
      this._renderAnalysisResults(analysisResults, bugReport);
      results.classList.add('active');

      await this._renderDashboard();
      await this._renderKnowledgeBase();

      this._showToast(`Bug ${responseBug.id} analyzed and stored in SQL DB!`, 'success');
    } catch (err) {
      this._showToast(`Analysis failed: ${err.message}`, 'error');
      const statusEl = document.getElementById('pipelineStatus');
      if (statusEl) {
        statusEl.innerHTML = '<span style="color: var(--severity-critical)">Analysis failed</span>';
      }
    }
  }

  // Pipeline UI Step Updater
  _showPipeline() {
    const pipeline = document.getElementById('pipelineContainer');
    pipeline.classList.add('active');

    const statusEl = document.getElementById('pipelineStatus');
    if (statusEl) {
      statusEl.innerHTML = '<span class="spinner"></span> Processing 5-agent pipeline...';
    }
  }

  _updatePipelineStep(stepId, status) {
    const step = document.getElementById(`step-${stepId}`);
    if (!step) return;

    step.className = `pipeline-step ${status}`;

    const statusEl = step.querySelector('.step-status');
    if (statusEl) {
      statusEl.className = `step-status ${status}`;
      switch (status) {
        case 'processing':
          statusEl.textContent = 'Processing...';
          break;
        case 'completed':
          statusEl.textContent = 'Complete';
          break;
        case 'pending':
          statusEl.textContent = 'Waiting...';
          break;
      }
    }
  }

  // ========================
  // Render Analysis Results
  // ========================
  _renderAnalysisResults(results, bugReport) {
    this._renderTriageResults(results.triage || {});
    this._renderLogAnalysisResults(results.logAnalysis || {});
    this._renderRootCauseResults(results.rootCause || {});
    this._renderAutoFixResults(results.autoFix || {});
    this._renderTestGeneratorResults(results.testGenerator || {});
    this._renderFixVerificationResults(results.fixVerification || {});
    this._renderSecurityScanResults(results.securityScan || {});
    this._renderDuplicateResults(results.duplicate || {});
    this._renderRagResults(results.ragRetrieval || {});
    this._renderRemediationResults(results.remediation || {});

    this._switchResultTab('triage');
  }

  _renderTriageResults(result) {
    const panel = document.getElementById('panel-triage');
    if (!panel || !result.agent) return;

    const severityClass = (result.severity || 'medium').toLowerCase();
    const d = result.details || {};
    const questions = result.clarificationQuestions || [];
    const ps = result.priorityScore || {};

    let priorityGaugeHtml = '';
    if (ps.score !== undefined) {
      const levelClass = (ps.level || 'medium').toLowerCase();
      priorityGaugeHtml = `
        <div class="priority-gauge-card">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <span style="font-family: var(--font-mono); font-size: 12px; font-weight: 700; color: var(--text-primary);">
              ⚡ BUG PRIORITY SCORE (COMPOSITE METRIC)
            </span>
            <span class="priority-score-badge ${levelClass}">
              SCORE: ${ps.score}/100 — ${ps.level.toUpperCase()} PRIORITY
            </span>
          </div>
          <div style="font-size: 11px; color: var(--text-muted); margin-bottom: 10px;">
            Formula: ${ps.formula || '35% Severity + 30% Impact + 20% Frequency + 15% Affected Module'}
          </div>

          <div class="priority-bar-wrapper">
            <div class="priority-bar-label"><span>Severity Impact (35%)</span><span>${ps.breakdown?.severity || 0}/100</span></div>
            <div class="priority-bar-track"><div class="priority-bar-fill" style="width:${ps.breakdown?.severity || 0}%; background: var(--severity-critical);"></div></div>
          </div>
          <div class="priority-bar-wrapper">
            <div class="priority-bar-label"><span>System Impact (30%)</span><span>${ps.breakdown?.impact || 0}/100</span></div>
            <div class="priority-bar-track"><div class="priority-bar-fill" style="width:${ps.breakdown?.impact || 0}%; background: var(--severity-high);"></div></div>
          </div>
          <div class="priority-bar-wrapper">
            <div class="priority-bar-label"><span>Frequency Cadence (20%)</span><span>${ps.breakdown?.frequency || 0}/100</span></div>
            <div class="priority-bar-track"><div class="priority-bar-fill" style="width:${ps.breakdown?.frequency || 0}%; background: var(--accent-cyan);"></div></div>
          </div>
          <div class="priority-bar-wrapper">
            <div class="priority-bar-label"><span>Affected Module Risk (15%)</span><span>${ps.breakdown?.module || 0}/100</span></div>
            <div class="priority-bar-track"><div class="priority-bar-fill" style="width:${ps.breakdown?.module || 0}%; background: var(--severity-medium);"></div></div>
          </div>
        </div>
      `;
    }

    let clarificationHtml = '';
    if (questions.length > 0) {
      clarificationHtml = `
        <div class="result-section" style="border: 1px solid var(--severity-high); border-radius: var(--radius-md); padding: 16px; background: rgba(255, 183, 3, 0.08); margin-bottom: 20px;">
          <div style="font-weight: 700; font-size: 14px; color: var(--severity-high); margin-bottom: 6px;">
            AI Advisor Needs Clarification (Confidence: ${result.confidence}%)
          </div>
          <p style="font-size: 12px; color: var(--text-secondary); margin-bottom: 12px;">
            Your bug report had limited context. Answer these quick questions to refine the multi-agent analysis:
          </p>

          ${questions.map((q, idx) => `
            <div style="margin-bottom: 10px;">
              <div style="font-size: 12px; font-weight: 600; margin-bottom: 4px;">${idx + 1}. ${q.question}</div>
              <select class="form-select clarification-answer-select" data-qid="${q.id}" style="font-size: 12px; padding: 6px 10px;">
                ${q.options.map(opt => `<option value="${this._escapeHtml(opt)}">${this._escapeHtml(opt)}</option>`).join('')}
              </select>
            </div>
          `).join('')}

          <button class="btn btn-primary btn-sm" onclick="app._refineWithClarifications()" style="margin-top: 6px;">
            Refine Analysis
          </button>
        </div>
      `;
    }

    panel.innerHTML = `
      <div class="result-header">
        <span class="result-title">${result.agent}</span>
      </div>
      <div class="result-summary">${result.summary || ''}</div>

      ${priorityGaugeHtml}

      ${clarificationHtml}

      <div class="result-section" style="margin-top: 16px;">
        <div class="result-section-title">Classification & Priority</div>
        <div class="result-item ${severityClass === 'critical' ? 'danger' : severityClass === 'high' ? 'warning' : 'highlight'}">
          ${d.classification || ''}
        </div>
        ${d.priorityScore ? `<div class="result-item highlight">${d.priorityScore}</div>` : ''}
        <div class="result-item">${d.category || ''}</div>
      </div>

      <div class="result-section">
        <div class="result-section-title">Confidence Score</div>
        <div style="display: flex; align-items: center; gap: 12px;">
          <div class="progress-bar" style="flex: 1;">
            <div class="progress-fill" style="width: ${result.confidence || 0}%;"></div>
          </div>
          <span style="font-family: var(--font-mono); font-size: 12px; font-weight: 700; color: var(--accent-cyan);">${result.confidence || 0}%</span>
        </div>
      </div>

      <div class="result-section">
        <div class="result-section-title">Tags</div>
        <div style="display: flex; gap: 6px; flex-wrap: wrap;">
          ${(result.tags || []).map(tag => `<span class="badge badge-${severityClass}">${tag}</span>`).join('')}
        </div>
      </div>

      <div class="result-section">
        <div class="result-section-title">Recommendation</div>
        <div class="result-item success">${d.recommendation || ''}</div>
      </div>
    `;
  }

  async _refineWithClarifications() {
    if (!this.lastSubmittedBugData) return;

    const selects = document.querySelectorAll('.clarification-answer-select');
    const clarifications = {};
    selects.forEach(s => {
      clarifications[s.dataset.qid] = s.value;
    });

    this.lastSubmittedBugData.clarifications = clarifications;
    this._showToast('Refining analysis with your clarifications...', 'info');
    await this._runAnalysisPipeline(this.lastSubmittedBugData);
  }

  _renderLogAnalysisResults(result) {
    const panel = document.getElementById('panel-log-analysis');
    if (!panel || !result.agent) return;

    const d = result.details || {};
    const errMsg = result.errorMessage || d.error || 'N/A';
    const excType = result.exceptionType || result.errorType || 'Unknown';
    const progLang = (result.programmingLanguage || result.language || 'generic').toUpperCase();
    const methName = result.methodName || 'N/A';
    const lineNum = result.lineNumber || 'N/A';

    let framesHtml = '';
    if (d.frames && d.frames.length > 0) {
      framesHtml = `
        <div class="result-section">
          <div class="result-section-title">Stack Frames (Top ${d.frames.length})</div>
          ${d.frames.map((f, i) => `
            <div class="result-item ${i === 0 ? 'danger' : ''}" style="font-family: var(--font-mono); font-size: 11px;">
              ${i === 0 ? '→ ' : '  '}${f}
            </div>
          `).join('')}
        </div>
      `;
    }

    let insightsHtml = '';
    if (d.logInsights && d.logInsights.length > 0) {
      insightsHtml = `
        <div class="result-section">
          <div class="result-section-title">Log Insights</div>
          ${d.logInsights.map(insight => `
            <div class="result-item highlight">${insight}</div>
          `).join('')}
        </div>
      `;
    }

    panel.innerHTML = `
      <div class="result-header">
        <span class="result-title">${result.agent} — Extracted Log Parameters</span>
      </div>
      <div class="result-summary">${result.summary || ''}</div>

      <div class="result-section" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; margin-bottom: 16px;">
        <div class="result-item danger" style="margin: 0;">
          <div style="font-size: 10px; color: var(--text-muted);">EXCEPTION TYPE</div>
          <div style="font-weight: 700; font-family: var(--font-mono); font-size: 13px;">${this._escapeHtml(excType)}</div>
        </div>
        <div class="result-item highlight" style="margin: 0;">
          <div style="font-size: 10px; color: var(--text-muted);">PROGRAMMING LANGUAGE</div>
          <div style="font-weight: 700; font-family: var(--font-mono); font-size: 13px;">${this._escapeHtml(progLang)}</div>
        </div>
        <div class="result-item warning" style="margin: 0;">
          <div style="font-size: 10px; color: var(--text-muted);">FAILING METHOD</div>
          <div style="font-weight: 700; font-family: var(--font-mono); font-size: 13px;">${this._escapeHtml(methName)}()</div>
        </div>
        <div class="result-item highlight" style="margin: 0;">
          <div style="font-size: 10px; color: var(--text-muted);">LINE NUMBER</div>
          <div style="font-weight: 700; font-family: var(--font-mono); font-size: 13px;">Line ${this._escapeHtml(String(lineNum))}</div>
        </div>
      </div>

      <div class="result-section">
        <div class="result-section-title">Extracted Error Message</div>
        <div class="result-item danger" style="font-family: var(--font-mono);">${this._escapeHtml(errMsg)}</div>
      </div>

      <div class="result-section">
        <div class="result-section-title">Failure Point</div>
        <div class="result-item warning">${d.failurePoint || ''}</div>
        <div class="result-item">${d.stackDepth || ''}</div>
      </div>

      ${framesHtml}
      ${insightsHtml}
    `;
  }

  _renderRootCauseResults(result) {
    const panel = document.getElementById('panel-root-cause');
    if (!panel || !result.agent) return;

    const d = result.details || {};
    const beginner = result.beginnerExplanation || {};

    let beginnerHtml = '';
    if (this.isMentorMode && beginner.analogy) {
      beginnerHtml = `
        <div class="result-section" style="border: 1px solid var(--severity-low); border-radius: var(--radius-md); padding: 16px; background: rgba(168, 85, 247, 0.08); margin-bottom: 20px;">
          <div style="font-weight: 700; font-size: 14px; color: var(--severity-low); margin-bottom: 6px;">
            Mentor Mode — Beginner Learning Guide
          </div>
          <div style="font-size: 12px; color: var(--text-primary); margin-bottom: 8px;">
            <strong>Real-World Analogy:</strong> ${this._escapeHtml(beginner.analogy)}
          </div>
          <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 10px;">
            <strong>Simplified Summary:</strong> ${this._escapeHtml(beginner.simplifiedSummary)}
          </div>
          <div style="font-size: 11px; font-weight: 600; color: var(--severity-low); margin-bottom: 6px;">Key Concepts & Dictionary:</div>
          <div style="display: flex; flex-direction: column; gap: 4px; margin-bottom: 10px;">
            ${(beginner.keyConcepts || []).map(c => `
              <div style="font-size: 11px; background: var(--bg-terminal); padding: 4px 8px; border-radius: var(--radius-xs);">
                <strong>${this._escapeHtml(c.term)}:</strong> ${this._escapeHtml(c.definition)}
              </div>
            `).join('')}
          </div>
        </div>
      `;
    }

    panel.innerHTML = `
      <div class="result-header">
        <span class="result-title">${result.agent}</span>
      </div>
      <div class="result-summary">${result.summary || ''}</div>

      ${beginnerHtml}

      <div class="result-section">
        <div class="result-section-title">Top Probable Cause</div>
        <div class="result-item danger">${d.topCause || ''}</div>
      </div>

      <div class="result-section">
        <div class="result-section-title">All Causes (Ranked)</div>
        ${(d.allCauses || []).map((cause, i) => `
          <div class="result-item ${i === 0 ? 'warning' : ''}">${cause}</div>
        `).join('')}
      </div>

      <div class="result-section">
        <div class="result-section-title">Patterns Matched</div>
        ${(d.patternsMatched || []).map(p => `
          <div class="result-item highlight">${p}</div>
        `).join('')}
      </div>
    `;
  }

  _renderAutoFixResults(result) {
    const panel = document.getElementById('panel-auto-fix');
    if (!panel) return;

    if (!result || !result.fixedCode) {
      panel.innerHTML = `
        <div class="empty-state" style="padding: 20px;">
          <div class="empty-state-text">No AI Auto-Fix suggestion generated yet</div>
        </div>
      `;
      return;
    }

    const diffLines = (result.diff || '').split('\n');
    const formattedDiff = diffLines.map(line => {
      if (line.startsWith('---') || line.startsWith('+++')) {
        return `<div class="diff-header">${this._escapeHtml(line)}</div>`;
      } else if (line.startsWith('-')) {
        return `<div class="diff-line diff-del">${this._escapeHtml(line)}</div>`;
      } else if (line.startsWith('+')) {
        return `<div class="diff-line diff-add">${this._escapeHtml(line)}</div>`;
      } else {
        return `<div class="diff-line">${this._escapeHtml(line)}</div>`;
      }
    }).join('');

    panel.innerHTML = `
      <div class="result-header">
        <span class="result-title">${result.agent || 'AI Auto-Fix Agent'}</span>
        <span class="badge badge-resolved">${(result.language || 'code').toUpperCase()} AUTO-FIX</span>
      </div>
      <div class="result-summary">${this._escapeHtml(result.explanation || '')}</div>

      <div class="result-section">
        <div class="result-section-title">UNIFIED CODE FIX DIFF</div>
        <div class="diff-box">${formattedDiff}</div>
      </div>

      <div class="result-section">
        <div class="result-section-title">CORRECTED CODE SNIPPET</div>
        <div class="code-block">${this._escapeHtml(result.fixedCode || '')}</div>
        <div style="margin-top: 10px; display: flex; gap: 10px;">
          <button class="btn btn-secondary btn-sm" onclick="navigator.clipboard.writeText(app.currentAnalysis?.autoFix?.fixedCode || ''); app._showToast('Fixed code copied to clipboard!', 'success');">
            📋 Copy Fixed Code
          </button>
          <button class="btn btn-primary btn-sm" onclick="app._switchResultTab('fix-verification')">
            ✅ Verify Fix With Tests
          </button>
        </div>
      </div>

      <div class="result-section" style="display: grid; grid-template-columns: 1fr 1fr; gap: 14px;">
        <div>
          <div class="result-section-title">Changes Made</div>
          ${(result.changesMade || []).map(c => `<div class="result-item success">• ${this._escapeHtml(c)}</div>`).join('')}
        </div>
        <div>
          <div class="result-section-title">Safety Guarantees</div>
          ${(result.safetyGuarantees || []).map(s => `<div class="result-item highlight">🛡️ ${this._escapeHtml(s)}</div>`).join('')}
        </div>
      </div>
    `;
  }

  _renderTestGeneratorResults(result) {
    const panel = document.getElementById('panel-test-generator');
    if (!panel) return;

    if (!result || !result.testCode) {
      panel.innerHTML = `
        <div class="empty-state" style="padding: 20px;">
          <div class="empty-state-text">No unit tests generated</div>
        </div>
      `;
      return;
    }

    const testCases = result.testCases || [];

    panel.innerHTML = `
      <div class="result-header">
        <span class="result-title">${result.agent || 'Auto Test Generator Agent'}</span>
        <span class="badge badge-medium">${result.testFramework || 'Pytest'}</span>
      </div>
      <div class="result-summary">Generated ${result.testCount || testCases.length} automated unit & regression tests targeting reproduction, fix verification, and boundary edge cases.</div>

      <div class="result-section">
        <div class="result-section-title">GENERATED TEST SUITE (${result.fileName || 'test_suite'})</div>
        <div class="code-block">${this._escapeHtml(result.testCode || '')}</div>
        <div style="margin-top: 10px; display: flex; gap: 10px;">
          <button class="btn btn-secondary btn-sm" onclick="navigator.clipboard.writeText(app.currentAnalysis?.testGenerator?.testCode || ''); app._showToast('Test suite copied to clipboard!', 'success');">
            📋 Copy Unit Tests
          </button>
          <button class="btn btn-primary btn-sm" onclick="app._switchResultTab('fix-verification')">
            ▶ Run Test Runner
          </button>
        </div>
      </div>

      <div class="result-section">
        <div class="result-section-title">Test Coverage Breakdown</div>
        <div style="display: flex; flex-direction: column; gap: 8px;">
          ${testCases.map(tc => `
            <div class="result-item highlight" style="display: flex; justify-content: space-between; align-items: center;">
              <div>
                <strong>${this._escapeHtml(tc.name)}</strong>
                <div style="font-size: 11px; color: var(--text-muted);">${tc.type} Test | Target: ${tc.target}</div>
              </div>
              <span class="badge badge-resolved">${tc.expected}</span>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }

  _renderFixVerificationResults(result) {
    const panel = document.getElementById('panel-fix-verification');
    if (!panel) return;

    if (!result || !result.status) {
      panel.innerHTML = `
        <div class="empty-state" style="padding: 20px;">
          <div class="empty-state-text">Fix Verification output pending</div>
        </div>
      `;
      return;
    }

    const isPass = result.status === 'PASS';
    const checks = result.checks || [];

    panel.innerHTML = `
      <div class="verification-hero ${isPass ? 'pass' : 'fail'}">
        <div>
          <div style="font-family: var(--font-mono); font-weight: 700; font-size: 18px; color: ${isPass ? '#10b981' : '#ff4a4a'}; margin-bottom: 4px;">
            ${isPass ? '✅ FIX VERIFICATION: PASSED' : '❌ FIX VERIFICATION: FAILED'}
          </div>
          <div style="font-size: 12px; color: var(--text-secondary);">${this._escapeHtml(result.summary || '')}</div>
        </div>
        <div>
          <span class="${isPass ? 'badge-pass' : 'badge-fail'}">
            SCORE: ${result.score}/100
          </span>
        </div>
      </div>

      <div class="result-section">
        <div class="result-section-title">VERIFICATION CHECKS BREAKDOWN (${result.executionTimeMs || 0}ms)</div>
        <div class="check-list">
          ${checks.map(c => `
            <div class="check-item ${c.status.toLowerCase()}">
              <div>
                <div style="font-weight: 700; font-size: 13px;">${this._escapeHtml(c.name)}</div>
                <div style="font-size: 11px; color: var(--text-secondary);">${this._escapeHtml(c.details)}</div>
              </div>
              <span class="badge badge-${c.status === 'PASS' ? 'resolved' : 'critical'}">${c.status}</span>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }

  _renderSecurityScanResults(result) {
    const panel = document.getElementById('panel-security-scan');
    if (!panel) return;

    if (!result || result.score === undefined) {
      panel.innerHTML = `
        <div class="empty-state" style="padding: 20px;">
          <div class="empty-state-text">No security scan performed</div>
        </div>
      `;
      return;
    }

    const findings = result.findings || [];
    const riskLevel = result.riskLevel || 'Clean';
    const riskClass = riskLevel.toLowerCase();

    panel.innerHTML = `
      <div class="result-header">
        <span class="result-title">${result.agent || 'Security Scanner Agent'} — SAST Engine</span>
        <span class="badge badge-${riskClass === 'clean' ? 'resolved' : (riskClass === 'critical' ? 'critical' : 'high')}">
          RISK: ${riskLevel.toUpperCase()} (${result.score}/100)
        </span>
      </div>
      <div class="result-summary">${this._escapeHtml(result.summary || '')}</div>

      <div class="result-section">
        <div class="result-section-title">Vulnerability Category Breakdown</div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 8px;">
          ${Object.entries(result.categoryCounts || {}).map(([cat, count]) => `
            <div class="result-item highlight" style="text-align: center; margin: 0;">
              <div style="font-size: 16px; font-weight: 700; color: ${count > 0 ? 'var(--severity-critical)' : 'var(--severity-resolved)'};">${count}</div>
              <div style="font-size: 10px; color: var(--text-muted); font-family: var(--font-mono);">${cat}</div>
            </div>
          `).join('')}
        </div>
      </div>

      <div class="result-section">
        <div class="result-section-title">Detected Vulnerabilities (${findings.length})</div>
        ${findings.length === 0 ? `
          <div class="result-item success">🛡️ Zero security vulnerabilities (SQLi, XSS, Secrets, Unsafe APIs) detected.</div>
        ` : findings.map(f => `
          <div class="vuln-card ${f.severity.toLowerCase()}">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
              <div>
                <span class="badge badge-${f.severity.toLowerCase()}">${f.severity}</span>
                <span class="cwe-tag">${f.cwe}</span>
                <strong style="font-size: 13px; margin-left: 6px;">${this._escapeHtml(f.category)}</strong>
              </div>
              <span style="font-family: var(--font-mono); font-size: 11px; color: var(--text-muted);">Line ${f.line}</span>
            </div>
            <div style="font-size: 12px; color: var(--text-primary); margin-bottom: 6px;">${this._escapeHtml(f.message)}</div>
            <div class="code-block" style="margin-bottom: 8px; font-size: 11px;">${this._escapeHtml(f.lineContent)}</div>
            <div style="font-size: 11px; color: var(--accent-cyan); background: rgba(0, 240, 255, 0.05); padding: 6px 10px; border-radius: var(--radius-xs); border: 1px solid rgba(0,240,255,0.2);">
              💡 <strong>Remediation:</strong> ${this._escapeHtml(f.recommendation)}
            </div>
          </div>
        `).join('')}
      </div>
    `;
  }

  _renderDuplicateResults(result) {
    const panel = document.getElementById('panel-duplicate');
    if (!panel || !result.agent) return;

    const d = result.details || {};

    let duplicatesHtml = '';
    if (d.duplicates && d.duplicates.length > 0) {
      duplicatesHtml = d.duplicates.map(dup => `
        <div class="result-item highlight" style="margin-bottom: 10px;">
          <div style="display: flex; justify-content: space-between; font-weight: 700; font-size: 12px; margin-bottom: 4px;">
            <span>${dup.display}</span>
            <span style="color: var(--accent-cyan);">${dup.similarity}</span>
          </div>
          ${dup.resolution ? `<div style="font-size: 11px; color: var(--text-secondary);">Resolution: ${dup.resolution}</div>` : ''}
        </div>
      `).join('');
    } else {
      duplicatesHtml = `
        <div class="empty-state" style="padding: 20px;">
          <div class="empty-state-text">No duplicate issues surfaced</div>
          <div class="empty-state-hint">This defect vector appears unique in the SQL database</div>
        </div>
      `;
    }

    panel.innerHTML = `
      <div class="result-header">
        <span class="result-title">${result.agent}</span>
      </div>
      <div class="result-summary">${result.summary || ''}</div>

      <div class="result-section">
        <div class="result-section-title">Similar Defects Found</div>
        ${duplicatesHtml}
      </div>

      <div class="result-section">
        <div class="result-section-title">Recommendation</div>
        <div class="result-item highlight">${d.recommendation || ''}</div>
      </div>
    `;
  }

  _renderRagResults(result) {
    const panel = document.getElementById('panel-rag');
    if (!panel) return;

    if (!result || !result.agent) {
      panel.innerHTML = `
        <div class="empty-state" style="padding: 20px;">
          <div class="empty-state-text">No RAG retrieval data available</div>
        </div>
      `;
      return;
    }

    const items = result.items || [];
    let itemsHtml = '';
    if (items.length > 0) {
      itemsHtml = items.map(item => `
        <div class="result-item highlight" style="margin-bottom: 12px; border-left: 3px solid var(--accent-cyan); padding: 12px; background: rgba(0, 242, 254, 0.05);">
          <div style="display: flex; justify-content: space-between; font-weight: 700; font-size: 13px; margin-bottom: 4px;">
            <span>📌 ${this._escapeHtml(item.id)}: ${this._escapeHtml(item.title)}</span>
            <span style="color: var(--accent-cyan); font-family: var(--font-mono);">${item.similarityScore}% Vector Relevance</span>
          </div>
          <div style="font-size: 11px; color: var(--text-muted); margin-bottom: 6px;">Category: ${this._escapeHtml(item.category || 'General')}</div>
          <div style="font-size: 11px; color: var(--text-secondary); margin-bottom: 6px;"><strong>Diagnosed Root Cause:</strong> ${this._escapeHtml(item.rootCause || 'N/A')}</div>
          <div style="font-size: 12px; color: var(--severity-resolved); background: rgba(34, 197, 94, 0.1); padding: 8px; border-radius: var(--radius-xs); border: 1px solid rgba(34, 197, 94, 0.3);">
            <strong>Confirmed Historical Resolution:</strong> ${this._escapeHtml(item.confirmedResolution || 'N/A')}
          </div>
        </div>
      `).join('');
    } else {
      itemsHtml = `
        <div class="empty-state" style="padding: 20px;">
          <div class="empty-state-text">No matching historical resolutions retrieved</div>
        </div>
      `;
    }

    panel.innerHTML = `
      <div class="result-header">
        <span class="result-title">${result.agent} — Sentence Transformers + FAISS</span>
      </div>
      <div class="result-summary">${result.summary || ''}</div>

      <div class="result-section">
        <div class="result-section-title">Vector Search Engine</div>
        <div class="result-item highlight">${result.details?.vectorEngine || 'SentenceTransformers (all-MiniLM-L6-v2) + FAISS IndexFlatIP'}</div>
      </div>

      <div class="result-section">
        <div class="result-section-title">Retrieved Historical Solutions (${items.length})</div>
        ${itemsHtml}
      </div>
    `;
  }

  _renderRemediationResults(result) {
    const panel = document.getElementById('panel-remediation');
    if (!panel || !result.agent) return;

    const d = result.details || {};
    const strategies = result.strategies || [];
    const historicalFixes = d.historicalFixes || [];

    let strategyHtml = '';
    if (strategies.length > 0) {
      const colors = ['var(--severity-resolved)', 'var(--accent-cyan)', 'var(--severity-low)'];

      strategyHtml += `
        <div class="result-section">
          <div class="result-section-title">Fix Strategy Matrix — Choose Approach</div>
          <div class="strategy-tabs" style="display:flex; gap:8px; margin-bottom:16px;">
            ${strategies.map((s, i) => `
              <button class="btn ${i === 0 ? 'btn-primary' : 'btn-secondary'} btn-sm strategy-tab-btn"
                data-strategy-idx="${i}"
                onclick="app._switchStrategy(${i})"
                style="flex:1; text-align:center; font-size:11px;">
                ${s.name}
              </button>
            `).join('')}
          </div>

          ${strategies.map((s, i) => `
            <div class="strategy-card ${i === 0 ? 'active' : ''}" id="strategy-card-${i}"
              style="display:${i === 0 ? 'block' : 'none'}; border:1px solid var(--border-subtle); border-radius:var(--radius-md); padding:16px; margin-bottom:16px; background:var(--bg-terminal);">

              <div style="display:flex; align-items:center; gap:10px; margin-bottom:12px;">
                <div>
                  <div style="font-weight:700; font-size:14px; color:${colors[i]}; font-family: var(--font-mono);">${s.name}</div>
                  <div style="font-size:12px; color:var(--text-secondary);">${s.approach}</div>
                </div>
              </div>

              <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-bottom:14px;">
                <div class="result-item highlight" style="margin:0;">Effort: ${s.effort}</div>
                <div class="result-item ${s.risk.toLowerCase().includes('critical') ? 'danger' : s.risk.toLowerCase().includes('high') ? 'warning' : 'success'}" style="margin:0;">Risk: ${s.risk}</div>
              </div>

              <div style="margin-bottom:14px;">
                <div style="font-weight:600; font-size:12px; margin-bottom:6px; color: var(--text-muted);">EXECUTION STEPS</div>
                ${(s.steps || []).map((step, si) => `
                  <div class="result-item success" style="margin-bottom:4px;">${si + 1}. ${step}</div>
                `).join('')}
              </div>

              ${s.codeExample ? `
                <div style="margin-bottom:14px;">
                  <div style="font-weight:600; font-size:12px; margin-bottom:6px; color: var(--text-muted);">CODE REMEDIATION SNIPPET</div>
                  <div class="code-block">${this._escapeHtml(s.codeExample)}</div>
                </div>
              ` : ''}

              <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
                <div>
                  <div style="font-weight:600; font-size:11px; color:var(--severity-resolved); margin-bottom:4px;">PROS</div>
                  ${(s.pros || []).map(p => `<div style="font-size:11px; padding:2px 0; color:var(--text-secondary);">+ ${p}</div>`).join('')}
                </div>
                <div>
                  <div style="font-weight:600; font-size:11px; color:var(--severity-critical); margin-bottom:4px;">CONS</div>
                  ${(s.cons || []).map(c => `<div style="font-size:11px; padding:2px 0; color:var(--text-secondary); font-family: var(--font-mono);">− ${c}</div>`).join('')}
                </div>
              </div>
            </div>
          `).join('')}
        </div>
      `;
    }

    panel.innerHTML = `
      <div class="result-header">
        <span class="result-title">${result.agent}</span>
      </div>
      <div class="result-summary">${result.summary || ''}</div>

      ${strategyHtml}

      <div class="result-section">
        <div class="result-section-title">Historical Resolutions</div>
        ${historicalFixes.map(fix => `<div class="result-item">${fix}</div>`).join('')}
      </div>

      ${this.currentBugId ? `
        <div style="margin-top: 20px; padding-top: 16px; border-top: 1px solid var(--border-subtle);">
          <button class="btn btn-success" onclick="app._showResolveForm()">
            MARK DEFECT AS RESOLVED
          </button>
        </div>
      ` : ''}

      <div id="resolveFormInline" class="resolve-form">
        <h3 style="margin-bottom: 12px; font-size: 14px; font-family: var(--font-mono);">RESOLVE DEFECT ${this.currentBugId || ''}</h3>
        <div class="form-group" style="margin-bottom: 10px;">
          <label class="form-label">Confirmed Root Cause</label>
          <textarea id="resolveRootCause" class="form-textarea" rows="2"
            placeholder="Enter confirmed root cause...">${result.summary || ''}</textarea>
        </div>
        <div class="form-group" style="margin-bottom: 14px;">
          <label class="form-label">Resolution Applied</label>
          <textarea id="resolveResolution" class="form-textarea" rows="2"
            placeholder="Describe the fix patch applied..."></textarea>
        </div>
        <div style="display: flex; gap: 10px;">
          <button class="btn btn-success btn-sm" onclick="app._resolveBug()">Confirm Resolution</button>
          <button class="btn btn-secondary btn-sm" onclick="app._hideResolveForm()">Cancel</button>
        </div>
      </div>
    `;
  }

  _switchStrategy(idx) {
    document.querySelectorAll('.strategy-card').forEach((card, i) => {
      card.style.display = i === idx ? 'block' : 'none';
    });
    document.querySelectorAll('.strategy-tab-btn').forEach((btn, i) => {
      btn.className = `btn ${i === idx ? 'btn-primary' : 'btn-secondary'} btn-sm strategy-tab-btn`;
    });
  }

  _switchResultTab(agentId) {
    document.querySelectorAll('.result-tab').forEach(tab => {
      tab.classList.toggle('active', tab.dataset.agent === agentId);
    });

    document.querySelectorAll('.result-panel').forEach(panel => {
      panel.classList.toggle('active', panel.id === `panel-${agentId}`);
    });
  }

  // ========================
  // Knowledge Base Table
  // ========================
  async _renderKnowledgeBase() {
    const tbody = document.getElementById('kbTableBody');
    if (!tbody) return;

    const q = document.getElementById('kbSearch')?.value.trim() || '';
    const category = document.getElementById('kbCategoryFilter')?.value || 'All';
    const severity = document.getElementById('kbSeverityFilter')?.value || 'All';
    const status = document.getElementById('kbStatusFilter')?.value || 'All';

    try {
      const bugs = await api.getBugs({ q, category, severity, status });

      if (!bugs || bugs.length === 0) {
        tbody.innerHTML = `
          <tr>
            <td colspan="6">
              <div class="empty-state">
                <div class="empty-state-text">No defects match filter criteria</div>
                <div class="empty-state-hint">Submit a bug report or reset database</div>
              </div>
            </td>
          </tr>
        `;
        return;
      }

      tbody.innerHTML = bugs.map(bug => `
        <tr>
          <td style="font-family: var(--font-mono); font-size: 11px; color: var(--text-muted);">${bug.id}</td>
          <td class="bug-title-cell" onclick="app._showBugDetail('${bug.id}')">${this._escapeHtml(bug.title)}</td>
          <td><span class="badge badge-${bug.severity.toLowerCase()}">${bug.severity}</span></td>
          <td>${bug.category}</td>
          <td><span class="badge badge-${bug.status === 'Resolved' ? 'resolved' : (bug.status === 'In-Progress' ? 'high' : 'open')}">${bug.status}</span></td>
          <td style="font-size: 11px; color: var(--text-muted); font-family: var(--font-mono);">${bug.dateSubmitted || ''}</td>
        </tr>
      `).join('');
    } catch (err) {
      console.error('Error fetching bugs:', err);
    }
  }

  _filterKnowledgeBase() {
    this._renderKnowledgeBase();
  }

  // ========================
  // Bug Detail Modal
  // ========================
  async _showBugDetail(bugId) {
    try {
      const bug = await api.getBugById(bugId);
      const modal = document.getElementById('modalOverlay');
      const content = document.getElementById('modalBody');

      const ps = bug.analysisResults?.triage?.priorityScore || {};
      let priorityBadge = '';
      if (ps.score !== undefined) {
        priorityBadge = `<span class="priority-score-badge ${ps.level.toLowerCase()}">⚡ Priority Score: ${ps.score}/100 [${ps.level}]</span>`;
      }

      const autoFix = bug.analysisResults?.autoFix;
      const testGen = bug.analysisResults?.testGenerator;

      content.innerHTML = `
        <div class="modal-title">${this._escapeHtml(bug.title)}</div>
        <div class="modal-meta" style="flex-wrap: wrap;">
          <span class="badge badge-${bug.severity.toLowerCase()}">${bug.severity}</span>
          <span class="badge badge-${bug.status === 'Resolved' ? 'resolved' : (bug.status === 'In-Progress' ? 'high' : 'open')}">${bug.status}</span>
          ${priorityBadge}
          <span style="font-size: 11px; color: var(--text-muted); font-family: var(--font-mono);">${bug.id} | ${bug.category} | ${bug.priority}</span>
        </div>

        <div class="modal-section">
          <div class="modal-section-title">Description</div>
          <div class="modal-section-content">${this._escapeHtml(bug.description) || 'No description provided.'}</div>
        </div>

        ${bug.logFileName ? `
          <div class="modal-section">
            <div class="modal-section-title">Log File</div>
            <div class="modal-section-content" style="font-family: var(--font-mono); font-size: 12px; color: var(--accent-cyan);">📁 ${this._escapeHtml(bug.logFileName)}</div>
          </div>
        ` : ''}

        ${bug.stackTrace ? `
          <div class="modal-section">
            <div class="modal-section-title">Stack Trace / Console Output</div>
            <div class="modal-stack-trace">${this._escapeHtml(bug.stackTrace)}</div>
          </div>
        ` : ''}

        ${autoFix && autoFix.fixedCode ? `
          <div class="modal-section">
            <div class="modal-section-title">🪄 AI Auto-Fix Corrected Code</div>
            <div class="code-block">${this._escapeHtml(autoFix.fixedCode)}</div>
          </div>
        ` : ''}

        ${testGen && testGen.testCode ? `
          <div class="modal-section">
            <div class="modal-section-title">🧪 Auto-Generated Unit Tests (${testGen.testFramework || 'Pytest'})</div>
            <div class="code-block">${this._escapeHtml(testGen.testCode)}</div>
          </div>
        ` : ''}

        ${bug.rootCause ? `
          <div class="modal-section">
            <div class="modal-section-title">Confirmed Root Cause</div>
            <div class="modal-section-content">${this._escapeHtml(bug.rootCause)}</div>
          </div>
        ` : ''}

        ${bug.resolution ? `
          <div class="modal-section">
            <div class="modal-section-title">Resolution Patch</div>
            <div class="modal-section-content">${this._escapeHtml(bug.resolution)}</div>
          </div>
        ` : ''}

        ${bug.resolutionNotes ? `
          <div class="modal-section">
            <div class="modal-section-title">Resolution Notes</div>
            <div class="modal-section-content">${this._escapeHtml(bug.resolutionNotes)}</div>
          </div>
        ` : ''}

        <div class="modal-meta" style="margin-top: 16px; padding-top: 12px; border-top: 1px solid var(--border-subtle);">
          <span style="font-size: 11px; color: var(--text-muted); font-family: var(--font-mono);">Submitted: ${bug.dateSubmitted}</span>
          ${bug.dateResolved ? `<span style="font-size: 11px; color: var(--text-muted); font-family: var(--font-mono);">Resolved: ${bug.dateResolved}</span>` : ''}
        </div>

        ${bug.status !== 'Resolved' ? `
          <div class="modal-actions">
            <button class="btn btn-primary btn-sm" onclick="app._toggleChatDrawer('${bug.id}')">Ask AI Mentor</button>
            <button class="btn btn-success btn-sm" onclick="app._showModalResolve('${bug.id}')">Resolve Defect</button>
            <button class="btn btn-danger btn-sm" onclick="app._deleteBug('${bug.id}')">Delete</button>
          </div>

          <div id="modalResolveForm" class="resolve-form">
            <h4 style="margin-bottom: 10px; font-family: var(--font-mono);">Resolve Defect ${bug.id}</h4>
            <div class="form-group" style="margin-bottom: 10px;">
              <label class="form-label">Root Cause *</label>
              <textarea id="modalRootCause" class="form-textarea" rows="2" placeholder="Enter identified root cause...">${this._escapeHtml(bug.rootCause || '')}</textarea>
            </div>
            <div class="form-group" style="margin-bottom: 10px;">
              <label class="form-label">Applied Fix / Resolution *</label>
              <textarea id="modalResolution" class="form-textarea" rows="2" placeholder="Enter applied fix code or configuration change...">${this._escapeHtml(bug.resolution || '')}</textarea>
            </div>
            <div class="form-group" style="margin-bottom: 10px;">
              <label class="form-label">Resolution Notes</label>
              <textarea id="modalResolutionNotes" class="form-textarea" rows="2" placeholder="Enter testing/deployment notes..."></textarea>
            </div>
            <button class="btn btn-success btn-sm" onclick="app._resolveFromModal('${bug.id}')">Confirm Resolution</button>
          </div>
        ` : `
          <div class="modal-actions">
            <button class="btn btn-primary btn-sm" onclick="app._toggleChatDrawer('${bug.id}')">Ask AI Mentor</button>
            <button class="btn btn-danger btn-sm" onclick="app._deleteBug('${bug.id}')">Delete</button>
          </div>
        `}
      `;

      modal.classList.add('active');
    } catch (err) {
      this._showToast('Error loading bug details: ' + err.message, 'error');
    }
  }

  _closeModal() {
    const modal = document.getElementById('modalOverlay');
    if (modal) modal.classList.remove('active');
  }

  _showModalResolve(bugId) {
    const form = document.getElementById('modalResolveForm');
    if (form) form.classList.toggle('active');
  }

  async _resolveFromModal(bugId) {
    const rootCause = document.getElementById('modalRootCause').value.trim();
    const resolution = document.getElementById('modalResolution').value.trim();
    const resolutionNotes = document.getElementById('modalResolutionNotes')?.value.trim() || '';

    if (!rootCause || !resolution) {
      this._showToast('Please fill in both root cause and resolution', 'error');
      return;
    }

    try {
      await api.resolveBug(bugId, rootCause, resolution, resolutionNotes);
      this._closeModal();
      await this._renderDashboard();
      await this._renderKnowledgeBase();
      this._showToast(`Bug ${bugId} resolved successfully in database!`, 'success');
    } catch (err) {
      this._showToast('Error resolving bug: ' + err.message, 'error');
    }
  }

  async _deleteBug(bugId) {
    if (!confirm(`Delete bug ${bugId}? This cannot be undone.`)) return;
    try {
      await api.deleteBug(bugId);
      this._closeModal();
      await this._renderDashboard();
      await this._renderKnowledgeBase();
      this._showToast(`Bug ${bugId} deleted successfully`, 'info');
    } catch (err) {
      this._showToast('Error deleting bug: ' + err.message, 'error');
    }
  }

  _showResolveForm() {
    const form = document.getElementById('resolveFormInline');
    if (form) form.classList.add('active');
  }

  _hideResolveForm() {
    const form = document.getElementById('resolveFormInline');
    if (form) form.classList.remove('active');
  }

  async _resolveBug() {
    if (!this.currentBugId) return;
    const rootCause = document.getElementById('resolveRootCause').value.trim();
    const resolution = document.getElementById('resolveResolution').value.trim();

    if (!rootCause || !resolution) {
      this._showToast('Please enter both root cause and resolution', 'error');
      return;
    }

    try {
      await api.resolveBug(this.currentBugId, rootCause, resolution);
      this._hideResolveForm();
      await this._renderDashboard();
      await this._renderKnowledgeBase();
      this._showToast(`Bug ${this.currentBugId} resolved and updated in database!`, 'success');
    } catch (err) {
      this._showToast('Error resolving bug: ' + err.message, 'error');
    }
  }

  // ========================
  // Utilities & Samples
  // ========================
  _loadSampleBug() {
    const samples = [
      {
        title: "NullPointerException in UserService.getProfile()",
        description: "Application crashes when trying to view a user profile that has been recently deleted. The getProfile method does not check for null before accessing user properties.",
        stackTrace: `java.lang.NullPointerException\n    at com.app.service.UserService.getProfile(UserService.java:142)\n    at com.app.controller.UserController.showProfile(UserController.java:85)`,
        category: "Backend"
      },
      {
        title: "Memory leak in WebSocket connection handler",
        description: "Server memory usage increases continuously over time. After 48 hours of operation, the application becomes unresponsive and needs to be restarted.",
        stackTrace: `java.lang.OutOfMemoryError: Java heap space\n    at com.app.websocket.ConnectionManager.addConnection(ConnectionManager.java:67)`,
        category: "Backend"
      },
      {
        title: "SQL Injection vulnerability in search endpoint",
        description: "The search API endpoint directly concatenates user input into SQL queries without parameterization, allowing potential SQL injection attacks.",
        stackTrace: `org.springframework.jdbc.BadSqlGrammarException: PreparedStatementCallback;\nbad SQL grammar [SELECT * FROM products WHERE name LIKE '%' OR '1'='1'--%]`,
        category: "Security"
      }
    ];

    const randomSample = samples[Math.floor(Math.random() * samples.length)];
    document.getElementById('bugTitle').value = randomSample.title;
    document.getElementById('bugDescription').value = randomSample.description;
    document.getElementById('bugStackTrace').value = randomSample.stackTrace;
    document.getElementById('bugCategory').value = randomSample.category;

    this._showToast('Sample bug loaded into Analyzer console', 'info');
  }

  _clearForm() {
    document.getElementById('bugTitle').value = '';
    document.getElementById('bugDescription').value = '';
    document.getElementById('bugStackTrace').value = '';
    document.getElementById('bugCategory').value = 'Auto-detect';

    const pipeline = document.getElementById('pipelineContainer');
    const results = document.getElementById('resultsContainer');
    if (pipeline) pipeline.classList.remove('active');
    if (results) results.classList.remove('active');

    this.currentAnalysis = null;
    this.currentBugId = null;
  }

  _updateElement(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
  }

  _delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  _escapeHtml(str) {
    if (!str) return '';
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  _showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span class="toast-message">${message}</span>`;

    container.appendChild(toast);
    setTimeout(() => {
      toast.style.animation = 'toastSlideOut 0.3s ease forwards';
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  }

  // ========================
  // AI Mentor Chat Drawer Methods
  // ========================
  async _toggleChatDrawer(bugId) {
    if (!bugId) {
      this._showToast('Please submit or select a bug first', 'warning');
      return;
    }

    this.activeChatBugId = bugId;
    const overlay = document.getElementById('chatDrawerOverlay');
    const badge = document.getElementById('chatBugBadge');
    if (badge) badge.textContent = bugId;

    if (overlay) overlay.classList.add('active');

    try {
      const history = await api.getChatHistory(bugId);
      this._renderChatMessages(history);
    } catch (err) {
      console.error('Failed to load chat history:', err);
      this._renderChatMessages([]);
    }
  }

  _closeChatDrawer() {
    const overlay = document.getElementById('chatDrawerOverlay');
    if (overlay) overlay.classList.remove('active');
  }

  _renderChatMessages(messages) {
    const container = document.getElementById('chatMessages');
    if (!container) return;

    if (!messages || messages.length === 0) {
      container.innerHTML = `
        <div class="chat-bubble advisor">
          Hello! I am your <strong>AI Coding Mentor</strong>.<br><br>
          Ask me anything about <strong>${this.activeChatBugId || 'this bug'}</strong> — for example:<br>
          - <em>"Why did line 142 fail?"</em><br>
          - <em>"How do I write a unit test for this fix?"</em><br>
          - <em>"Show me the recommended code fix snippet."</em>
        </div>
      `;
      return;
    }

    container.innerHTML = messages.map(m => `
      <div class="chat-bubble ${m.sender}">
        ${this._formatChatMessage(m.message)}
      </div>
    `).join('');

    container.scrollTop = container.scrollHeight;
  }

  _formatChatMessage(text) {
    if (!text) return '';
    let escaped = this._escapeHtml(text);
    escaped = escaped.replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>');
    escaped = escaped.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    escaped = escaped.replace(/\*(.*?)\*/g, '<em>$1</em>');
    escaped = escaped.replace(/\n/g, '<br>');
    return escaped;
  }

  async _handleSendMessage() {
    const input = document.getElementById('chatInput');
    if (!input || !this.activeChatBugId) return;

    const message = input.value.trim();
    if (!message) return;

    input.value = '';

    const container = document.getElementById('chatMessages');
    if (container) {
      container.innerHTML += `
        <div class="chat-bubble user">
          ${this._escapeHtml(message)}
        </div>
        <div class="chat-bubble advisor" id="tempAdvisorLoading">
          <span class="spinner"></span> AI Mentor is analyzing your prompt...
        </div>
      `;
      container.scrollTop = container.scrollHeight;
    }

    try {
      const responseMsg = await api.sendChatMessage(this.activeChatBugId, message);
      const loading = document.getElementById('tempAdvisorLoading');
      if (loading) loading.remove();

      if (container) {
        container.innerHTML += `
          <div class="chat-bubble advisor">
            ${this._formatChatMessage(responseMsg.message)}
          </div>
        `;
        container.scrollTop = container.scrollHeight;
      }
    } catch (err) {
      const loading = document.getElementById('tempAdvisorLoading');
      if (loading) loading.remove();
      this._showToast('Failed to send message: ' + err.message, 'error');
    }
  }

  // ========================
  // Code Doctor (Code Review) Methods
  // ========================
  async _handleCodeReview() {
    const input = document.getElementById('codeSnippetInput');
    const btn = document.getElementById('auditCodeBtn');
    if (!input || !input.value.trim()) {
      this._showToast('Please enter a code snippet to review', 'warning');
      return;
    }

    const code = input.value.trim();
    if (btn) btn.disabled = true;

    try {
      this._showToast('Running Code Doctor static analysis rules...', 'info');
      const report = await api.auditCode(code);
      this._renderCodeReviewResults(report);
      this._showToast(`Code Audit Complete — Score: ${report.score}/100 (Grade ${report.grade})`, report.score >= 75 ? 'success' : 'warning');
    } catch (err) {
      this._showToast('Code review failed: ' + err.message, 'error');
    } finally {
      if (btn) btn.disabled = false;
    }
  }

  _loadSampleCode() {
    const sampleCode = `// Vulnerable & Risky Code Sample for Code Doctor Audit
function processUserData(req, res) {
  let userInput = req.query.username;
  let secretKey = "secret_api_key_12345"; // Hardcoded secret

  // Unsafe SQL query concatenation
  let query = "SELECT * FROM users WHERE username = '" + userInput + "'";
  let conn = openDbConnection();
  let results = conn.execute(query); // Resource opened without try-finally

  // Potential XSS
  document.getElementById("output").innerHTML = "Welcome " + userInput;

  // Magic number & loose equality
  if (req.query.role == 100) {
    eval("grantAdminAccess()");
  }

  // Silent error swallowing
  try {
    saveLog(results);
  } catch (err) {
    // TODO: implement error logging
  }
}`;

    const input = document.getElementById('codeSnippetInput');
    if (input) input.value = sampleCode;
    this._showToast('Vulnerable sample code loaded into Code Doctor', 'info');
  }

  _renderCodeReviewResults(report) {
    const container = document.getElementById('codeReviewResultsContainer');
    const badge = document.getElementById('codeHealthBadge');
    const summary = document.getElementById('codeReviewSummary');
    const list = document.getElementById('codeReviewFindingsList');

    if (!container || !report) return;

    container.style.display = 'block';

    let badgeClass = 'badge-open';
    if (report.score >= 90) badgeClass = 'badge-resolved';
    else if (report.score >= 75) badgeClass = 'badge-medium';
    else if (report.score >= 50) badgeClass = 'badge-high';
    else badgeClass = 'badge-critical';

    if (badge) {
      badge.className = `badge ${badgeClass}`;
      badge.textContent = `Score: ${report.score}/100 (Grade ${report.grade})`;
    }

    if (summary) {
      summary.textContent = report.summary || 'Code analysis complete.';
    }

    if (list) {
      if (!report.findings || report.findings.length === 0) {
        list.innerHTML = `
          <div class="result-item success" style="padding: 14px;">
            <strong>Zero issues detected!</strong> Your code snippet adheres to all security, resource management, and clean code rules.
          </div>
        `;
        return;
      }

      const sevClassMap = {
        'Critical': 'danger',
        'High': 'danger',
        'Medium': 'warning',
        'Low': 'highlight'
      };

      list.innerHTML = report.findings.map(f => `
        <div class="result-item ${sevClassMap[f.severity] || 'warning'}" style="margin-bottom: 12px; padding: 12px 16px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <div style="font-weight: 700; font-size: 13px; font-family: var(--font-mono);">
              <span>${f.ruleId}</span> — <span style="color: var(--text-primary);">${this._escapeHtml(f.message)}</span>
            </div>
            <span class="badge ${f.severity === 'Critical' || f.severity === 'High' ? 'badge-critical' : 'badge-medium'}">${f.severity}</span>
          </div>

          <div style="font-size: 11px; color: var(--text-secondary); margin-bottom: 6px; font-family: var(--font-mono);">
            Category: ${f.category} | Line ${f.line}: <code>${this._escapeHtml(f.lineContent)}</code>
          </div>

          <div style="font-size: 12px; color: var(--severity-resolved); background: rgba(16, 185, 129, 0.08); padding: 6px 10px; border-radius: var(--radius-xs);">
            <strong>Recommendation:</strong> ${this._escapeHtml(f.suggestion)}
          </div>
        </div>
      `).join('');
    }

    container.scrollIntoView({ behavior: 'smooth' });
  }
}

// Initialize on DOM load
let app;
document.addEventListener('DOMContentLoaded', () => {
  app = new SmartBugAnalyzerApp();
});
