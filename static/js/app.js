/**
 * AI-Powered Software Requirements & Test Case Generator
 * Interactive Testing Tool Controller (Full CRUD, Live Execution & Defect Tracking)
 */

document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initEventHandlers();
    initPresets();
    loadAllData();
});

// State tracking
let currentEditingReqCode = null;
let activeModalTcId = null;
let allTestCasesCache = [];

// ============================================================================
// 1. NAVIGATION & TAB SWITCHING
// ============================================================================

function initNavigation() {
    const tabs = document.querySelectorAll('.nav-tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const targetId = tab.getAttribute('data-tab');
            switchTab(targetId);
        });
    });
}

function switchTab(tabId) {
    document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));

    const activeBtn = document.querySelector(`.nav-tab[data-tab="${tabId}"]`);
    const activePane = document.getElementById(tabId);

    if (activeBtn) activeBtn.classList.add('active');
    if (activePane) activePane.classList.add('active');

    // Trigger tab-specific refreshes
    if (tabId === 'tab-dashboard') loadDashboard();
    if (tabId === 'tab-requirements') loadRequirements();
    if (tabId === 'tab-testcases') {
        loadTestCases();
        loadDefects();
    }
    if (tabId === 'tab-reports') loadReportTab();
}

// ============================================================================
// 2. EVENT HANDLERS INITIALIZATION
// ============================================================================

function initEventHandlers() {
    // Reset Data
    document.getElementById('btnResetData').addEventListener('click', handleResetData);

    // Dashboard quick execute
    document.getElementById('btnDashExecuteAll').addEventListener('click', handleExecuteAllLive);

    // About modal
    document.getElementById('btnOpenAbout').addEventListener('click', () => {
        document.getElementById('modalAbout').classList.remove('hidden');
    });
    document.getElementById('btnCloseAboutModal').addEventListener('click', () => {
        document.getElementById('modalAbout').classList.add('hidden');
    });
    document.getElementById('btnOkAbout').addEventListener('click', () => {
        document.getElementById('modalAbout').classList.add('hidden');
    });

    // Requirements form (Create or Update)
    document.getElementById('formRequirement').addEventListener('submit', handleSaveRequirement);
    document.getElementById('btnCancelReqEdit').addEventListener('click', cancelReqEdit);
    document.getElementById('btnClearReqForm').addEventListener('click', cancelReqEdit);

    // Test Case Generation
    document.getElementById('btnTriggerGenerate').addEventListener('click', handleTriggerGenerate);

    // Test Cases Filters & Search
    document.getElementById('filterReq').addEventListener('change', renderFilteredCachedTestCases);
    document.getElementById('filterStatus').addEventListener('change', renderFilteredCachedTestCases);
    document.getElementById('inputSearchTc').addEventListener('input', renderFilteredCachedTestCases);

    // Execute All Live in Test Cases Tab
    document.getElementById('btnExecuteAllLive').addEventListener('click', handleExecuteAllLive);

    // Add Test Case Modal
    document.getElementById('btnOpenAddTestModal').addEventListener('click', openAddTestModal);
    document.getElementById('btnCloseAddTcModal').addEventListener('click', () => {
        document.getElementById('modalAddTestCase').classList.add('hidden');
    });
    document.getElementById('formAddTestCase').addEventListener('submit', handleCreateCustomTestCase);

    // Portal Sandbox Toggle
    document.getElementById('btnToggleSandbox').addEventListener('click', togglePortalSandbox);
    document.getElementById('sandboxRegistrationForm').addEventListener('submit', handleSandboxSubmit);

    // Manual Execution Modal
    document.getElementById('btnCloseModal').addEventListener('click', closeManualModal);
    document.getElementById('btnCancelModal').addEventListener('click', closeManualModal);
    document.getElementById('btnSaveManualExecution').addEventListener('click', handleSaveManualExecution);
    document.getElementById('btnRunLiveInsideModal').addEventListener('click', handleRunLiveFromModal);

    // Modal Status dropdown toggles Defect Description field
    document.getElementById('manualStatusSelect').addEventListener('change', (e) => {
        const group = document.getElementById('groupDefectDesc');
        if (e.target.value === 'FAIL') {
            group.classList.remove('hidden');
        }
    });
}

// Sandbox presets for quick testing
function initPresets() {
    document.getElementById('presetValid').addEventListener('click', () => {
        const rand = Math.floor(1000 + Math.random() * 9000);
        document.getElementById('sbFullName').value = "Priya Sharma";
        document.getElementById('sbEmail').value = `priya.sharma${rand}@example.com`;
        document.getElementById('sbPassword').value = "SecurePass123";
        document.getElementById('sbPhone').value = "9812345678";
        document.getElementById('sbCourse').value = "MCA";
    });

    document.getElementById('presetShortPass').addEventListener('click', () => {
        document.getElementById('sbFullName').value = "Amit Patel";
        document.getElementById('sbEmail').value = "amit.patel@example.com";
        document.getElementById('sbPassword').value = "Pass1"; // < 8 characters
        document.getElementById('sbPhone').value = "9823456789";
        document.getElementById('sbCourse').value = "MCA";
    });

    document.getElementById('presetInvalidEmail').addEventListener('click', () => {
        document.getElementById('sbFullName').value = "Rohan Verma";
        document.getElementById('sbEmail').value = "rohan_invalid_email.com"; // Missing @
        document.getElementById('sbPassword').value = "ValidPassword1";
        document.getElementById('sbPhone').value = "9123456780";
        document.getElementById('sbCourse').value = "MCA";
    });

    document.getElementById('presetDuplicate').addEventListener('click', () => {
        document.getElementById('sbFullName').value = "Duplicate Applicant";
        document.getElementById('sbEmail').value = "arun.kumar@example.com"; // Pre-seeded duplicate
        document.getElementById('sbPassword').value = "Password123";
        document.getElementById('sbPhone').value = "9876543211";
        document.getElementById('sbCourse').value = "M.Tech";
    });

    document.getElementById('presetBoundaryName').addEventListener('click', () => {
        document.getElementById('sbFullName').value = "Christopher Bartholomew Montgomery Alexander The Great Explorer"; // > 50 chars
        document.getElementById('sbEmail').value = "chris.boundary@example.com";
        document.getElementById('sbPassword').value = "Password123";
        document.getElementById('sbPhone').value = "9998887776";
        document.getElementById('sbCourse').value = "B.Tech";
    });
}

function togglePortalSandbox() {
    const card = document.getElementById('cardPortalSandbox');
    card.classList.toggle('hidden');
    if (!card.classList.contains('hidden')) {
        card.scrollIntoView({ behavior: 'smooth' });
    }
}

// ============================================================================
// 3. MASTER DATA LOADERS
// ============================================================================

async function loadAllData() {
    await loadDashboard();
    await loadRequirements();
    await loadTestCases();
    await loadDefects();
}

async function loadDashboard() {
    try {
        const res = await fetch('/api/report/summary');
        const data = await res.json();
        if (data.status === 'success') {
            const s = data.summary;
            document.getElementById('statTotalReqs').textContent = s.total_requirements;
            document.getElementById('statTotalTests').textContent = s.total_test_cases;
            document.getElementById('statTestsExecuted').textContent = s.tests_executed;
            document.getElementById('statPassedTests').textContent = s.passed;
            document.getElementById('statFailedTests').textContent = s.failed;
            document.getElementById('statPendingTests').textContent = s.pending;
            document.getElementById('statOpenDefects').textContent = s.open_defects;
            document.getElementById('statPassRate').textContent = `Pass Rate: ${s.pass_rate}%`;

            // Progress bar
            const total = s.total_test_cases || 1;
            const passPct = (s.passed / total) * 100;
            const failPct = (s.failed / total) * 100;
            const pendPct = (s.pending / total) * 100;

            document.getElementById('barPassed').style.width = `${passPct}%`;
            document.getElementById('barFailed').style.width = `${failPct}%`;
            document.getElementById('barPending').style.width = `${pendPct}%`;

            document.getElementById('progressSummaryText').textContent = 
                `${s.tests_executed} / ${s.total_test_cases} Executed (${s.pass_rate}% Pass Rate)`;

            // Recent summary table on dashboard
            loadDashboardSummaryTable();
        }
    } catch (err) {
        console.error('Failed to load dashboard summary:', err);
    }
}

async function loadDashboardSummaryTable() {
    try {
        const res = await fetch('/api/test-cases');
        const data = await res.json();
        if (data.status === 'success') {
            const tbody = document.querySelector('#tableDashSummary tbody');
            tbody.innerHTML = '';
            const cases = data.test_cases.slice(0, 8); // Top 8 cases

            if (cases.length === 0) {
                tbody.innerHTML = `<tr><td colspan="6" class="text-center text-muted">No test cases generated yet.</td></tr>`;
                return;
            }

            cases.forEach(tc => {
                const tr = document.createElement('tr');
                let badge = '<span class="badge badge-warning">Not Executed</span>';
                if (tc.status === 'PASS') badge = '<span class="badge badge-success">PASS</span>';
                if (tc.status === 'FAIL') badge = '<span class="badge badge-danger">FAIL</span>';

                tr.innerHTML = `
                    <td><strong>${escapeHtml(tc.tc_id)}</strong></td>
                    <td><span class="badge badge-info">${escapeHtml(tc.req_code)}</span></td>
                    <td>${escapeHtml(tc.scenario)}</td>
                    <td><small>${escapeHtml(tc.expected_result)}</small></td>
                    <td><small>${escapeHtml(tc.actual_result || 'Pending execution')}</small></td>
                    <td>${badge}</td>
                `;
                tbody.appendChild(tr);
            });
        }
    } catch (err) {
        console.error('Error loading dashboard summary table:', err);
    }
}

// ============================================================================
// 4. REQUIREMENTS MANAGEMENT (FULL CRUD)
// ============================================================================

async function loadRequirements() {
    try {
        const res = await fetch('/api/requirements');
        const data = await res.json();
        if (data.status === 'success') {
            const reqs = data.requirements;
            document.getElementById('reqCountBadge').textContent = reqs.length;

            const tbody = document.querySelector('#tableRequirements tbody');
            const selectGen = document.getElementById('selectGenReq');
            const selectFilter = document.getElementById('filterReq');
            const selectModalTc = document.getElementById('newTcReqCode');

            tbody.innerHTML = '';
            selectGen.innerHTML = '';
            selectFilter.innerHTML = '<option value="ALL">All Requirements</option>';
            if (selectModalTc) selectModalTc.innerHTML = '';

            reqs.forEach(r => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td><strong>${escapeHtml(r.req_code)}</strong></td>
                    <td><strong>${escapeHtml(r.title)}</strong></td>
                    <td><span class="badge badge-info">${escapeHtml(r.category)}</span></td>
                    <td>${escapeHtml(r.description)}</td>
                    <td style="text-align: center;"><span class="badge badge-primary">${r.test_case_count || 0}</span></td>
                    <td>
                        <div style="display: flex; gap: 4px; flex-wrap: wrap;">
                            <button class="btn btn-xs btn-primary" onclick="quickGenerateForReq('${r.req_code}')" title="Generate 8+ test cases for this requirement">
                                ✨ Gen 8+
                            </button>
                            <button class="btn btn-xs btn-outline-secondary" onclick="editRequirement('${r.req_code}')" title="Edit this requirement">
                                ✏️ Edit
                            </button>
                            <button class="btn btn-xs btn-outline-danger" onclick="deleteRequirement('${r.req_code}')" title="Delete requirement">
                                🗑️
                            </button>
                        </div>
                    </td>
                `;
                tbody.appendChild(tr);

                // Populate Generator & Filter dropdowns
                const optGen = document.createElement('option');
                optGen.value = r.req_code;
                optGen.textContent = `${r.req_code}: ${r.title}`;
                selectGen.appendChild(optGen);

                const optFilter = document.createElement('option');
                optFilter.value = r.req_code;
                optFilter.textContent = `${r.req_code} - ${r.title}`;
                selectFilter.appendChild(optFilter);

                if (selectModalTc) {
                    const optModal = document.createElement('option');
                    optModal.value = r.req_code;
                    optModal.textContent = `${r.req_code} - ${r.title}`;
                    selectModalTc.appendChild(optModal);
                }
            });
        }
    } catch (err) {
        console.error('Failed to load requirements:', err);
    }
}

async function handleSaveRequirement(e) {
    e.preventDefault();
    const reqCode = document.getElementById('reqInputCode').value.trim().toUpperCase();
    const title = document.getElementById('reqInputTitle').value.trim();
    const category = document.getElementById('reqInputCategory').value.trim();
    const description = document.getElementById('reqInputDesc').value.trim();

    if (!reqCode || !title || !description) {
        alert('Please fill all required fields.');
        return;
    }

    const payload = { req_code: reqCode, title, category, description };

    try {
        let url = '/api/requirements';
        let method = 'POST';

        if (currentEditingReqCode) {
            url = `/api/requirements/${encodeURIComponent(currentEditingReqCode)}`;
            method = 'PUT';
        }

        const res = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (data.status === 'success') {
            alert(data.message);
            cancelReqEdit();
            await loadRequirements();
            await loadDashboard();
        } else {
            alert(`Error: ${data.message}`);
        }
    } catch (err) {
        alert(`Failed to save requirement: ${err.message}`);
    }
}

window.editRequirement = async function(reqCode) {
    try {
        const res = await fetch(`/api/requirements/${encodeURIComponent(reqCode)}`);
        const data = await res.json();
        if (data.status === 'success') {
            const r = data.requirement;
            currentEditingReqCode = r.req_code;

            document.getElementById('reqInputCode').value = r.req_code;
            document.getElementById('reqInputCode').disabled = true; // Code cannot change during edit
            document.getElementById('reqInputTitle').value = r.title;
            document.getElementById('reqInputCategory').value = r.category;
            document.getElementById('reqInputDesc').value = r.description;

            document.getElementById('reqFormTitle').textContent = `✏️ Edit Requirement: ${r.req_code}`;
            document.getElementById('reqFormBadge').textContent = 'Mode: Edit';
            document.getElementById('reqFormBadge').className = 'badge badge-warning';
            document.getElementById('btnSaveRequirement').textContent = '💾 Update Requirement';
            document.getElementById('btnCancelReqEdit').style.display = 'inline-flex';

            document.getElementById('formRequirement').scrollIntoView({ behavior: 'smooth' });
        }
    } catch (err) {
        alert(`Failed to load requirement details: ${err.message}`);
    }
};

function cancelReqEdit() {
    currentEditingReqCode = null;
    document.getElementById('formRequirement').reset();
    document.getElementById('reqInputCode').disabled = false;
    document.getElementById('reqFormTitle').textContent = '➕ Enter Software Functional Requirement';
    document.getElementById('reqFormBadge').textContent = 'Mode: Create';
    document.getElementById('reqFormBadge').className = 'badge badge-info';
    document.getElementById('btnSaveRequirement').textContent = '💾 Save Requirement';
    document.getElementById('btnCancelReqEdit').style.display = 'none';
}

window.deleteRequirement = async function(reqCode) {
    const confirmed = confirm(`Are you sure you want to delete requirement '${reqCode}'? Linked test cases and defects will also be deleted.`);
    if (!confirmed) return;

    try {
        const res = await fetch(`/api/requirements/${encodeURIComponent(reqCode)}`, { method: 'DELETE' });
        const data = await res.json();
        if (data.status === 'success') {
            alert(data.message);
            if (currentEditingReqCode === reqCode) cancelReqEdit();
            await loadRequirements();
            await loadTestCases();
            await loadDashboard();
            await loadDefects();
        } else {
            alert(`Error: ${data.message}`);
        }
    } catch (err) {
        alert(`Failed to delete requirement: ${err.message}`);
    }
};

window.quickGenerateForReq = function(reqCode) {
    document.getElementById('selectGenReq').value = reqCode;
    switchTab('tab-testcases');
    handleTriggerGenerate();
};

// ============================================================================
// 5. TEST CASE GENERATION
// ============================================================================

async function handleTriggerGenerate() {
    const reqCode = document.getElementById('selectGenReq').value;
    const engineMode = document.getElementById('selectGenEngine').value;
    const forceFallback = engineMode === 'fallback';

    if (!reqCode) {
        alert('Please select or create a requirement first.');
        return;
    }

    const btn = document.getElementById('btnTriggerGenerate');
    const alertBox = document.getElementById('aiGenStatusAlert');

    btn.disabled = true;
    btn.innerHTML = '⏳ Generating 8+ Tests...';
    alertBox.classList.add('hidden');

    try {
        const res = await fetch('/api/generate-test-cases', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ req_code: reqCode, force_fallback: forceFallback })
        });
        const data = await res.json();

        if (data.status === 'success') {
            alertBox.classList.remove('hidden');
            alertBox.innerHTML = `
                <strong>✅ Success!</strong> Generated <strong>${data.count} structured test cases</strong> for requirement <strong>${escapeHtml(reqCode)}</strong>.<br>
                <small>Engine: ${escapeHtml(data.engine)}</small>
            `;

            // Update badge in header
            document.getElementById('engineBadgeText').textContent = data.engine.includes('Gemini') 
                ? 'Engine: Google Gemini Live API' 
                : 'Engine: Rule & Keyword Fallback (Offline)';

            await loadTestCases();
            await loadDashboard();
            await loadRequirements();
        } else {
            alertBox.classList.remove('hidden');
            alertBox.innerHTML = `<strong>Error:</strong> ${data.message}`;
        }
    } catch (err) {
        alertBox.classList.remove('hidden');
        alertBox.innerHTML = `<strong>Network Error:</strong> ${err.message}`;
    } finally {
        btn.disabled = false;
        btn.innerHTML = '✨ Generate 8+ Test Cases';
    }
}

// ============================================================================
// 6. TEST CASES & EXECUTION ENGINE
// ============================================================================

async function loadTestCases() {
    try {
        const res = await fetch('/api/test-cases');
        const data = await res.json();
        if (data.status === 'success') {
            allTestCasesCache = data.test_cases;
            renderFilteredCachedTestCases();
        }
    } catch (err) {
        console.error('Failed to load test cases:', err);
    }
}

function renderFilteredCachedTestCases() {
    const reqFilter = document.getElementById('filterReq').value;
    const statusFilter = document.getElementById('filterStatus').value;
    const search = document.getElementById('inputSearchTc').value.trim().toLowerCase();

    let filtered = allTestCasesCache.filter(tc => {
        if (reqFilter !== 'ALL' && tc.req_code !== reqFilter) return false;
        if (statusFilter !== 'ALL' && tc.status !== statusFilter) return false;
        if (search) {
            const matched = tc.tc_id.toLowerCase().includes(search) || 
                            tc.scenario.toLowerCase().includes(search) ||
                            tc.expected_result.toLowerCase().includes(search);
            if (!matched) return false;
        }
        return true;
    });

    document.getElementById('tcFilteredCount').textContent = `Showing ${filtered.length} of ${allTestCasesCache.length} test cases`;

    const tbody = document.querySelector('#tableTestCases tbody');
    tbody.innerHTML = '';

    if (filtered.length === 0) {
        tbody.innerHTML = `<tr><td colspan="9" class="text-center text-muted">No test cases match filter.</td></tr>`;
        return;
    }

    filtered.forEach(tc => {
        const tr = document.createElement('tr');

        let statusBadge = '<span class="badge badge-warning">Not Executed</span>';
        if (tc.status === 'PASS') statusBadge = '<span class="badge badge-success">PASS</span>';
        if (tc.status === 'FAIL') statusBadge = '<span class="badge badge-danger">FAIL</span>';

        let typeBadge = `<span class="badge badge-primary">${escapeHtml(tc.test_type)}</span>`;
        if (tc.test_type === 'Negative') typeBadge = `<span class="badge badge-danger">Negative</span>`;
        if (tc.test_type === 'Boundary') typeBadge = `<span class="badge badge-warning">Boundary</span>`;
        if (tc.test_type === 'Security') typeBadge = `<span class="badge badge-info">Security</span>`;

        tr.innerHTML = `
            <td><strong>${escapeHtml(tc.tc_id)}</strong></td>
            <td><span class="badge badge-info">${escapeHtml(tc.req_code)}</span></td>
            <td><strong>${escapeHtml(tc.scenario)}</strong></td>
            <td>${typeBadge}</td>
            <td><pre class="code-preview">${escapeHtml(tc.input_data)}</pre></td>
            <td><small>${escapeHtml(tc.expected_result)}</small></td>
            <td><small>${escapeHtml(tc.actual_result || '—')}</small></td>
            <td>${statusBadge}</td>
            <td>
                <div style="display: flex; gap: 4px;">
                    <button class="btn btn-xs btn-success" onclick="executeSingleTestLive('${tc.tc_id}')" title="Run live test against backend validator">
                        ▶️ Run
                    </button>
                    <button class="btn btn-xs btn-outline-secondary" onclick="openManualModal('${tc.tc_id}')" title="Manual run or edit actual result">
                        ✏️
                    </button>
                    <button class="btn btn-xs btn-outline-danger" onclick="deleteTestCase('${tc.tc_id}')" title="Delete test case">
                        🗑️
                    </button>
                </div>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

window.executeSingleTestLive = async function(tcId) {
    try {
        const res = await fetch(`/api/test-cases/execute-live/${encodeURIComponent(tcId)}`, { method: 'POST' });
        const data = await res.json();

        if (data.status === 'success') {
            await loadTestCases();
            await loadDashboard();
            await loadDefects();
        } else if (data.manual_required) {
            // Test case is manual-only; open manual modal
            alert(data.message);
            openManualModal(tcId);
        } else {
            alert(`Execution Error: ${data.message}`);
        }
    } catch (err) {
        alert(`Execution failed: ${err.message}`);
    }
};

async function handleExecuteAllLive() {
    const btn1 = document.getElementById('btnExecuteAllLive');
    const btn2 = document.getElementById('btnDashExecuteAll');

    if (btn1) { btn1.disabled = true; btn1.innerHTML = '⏳ Executing...'; }
    if (btn2) { btn2.disabled = true; btn2.innerHTML = '⏳ Executing...'; }

    try {
        const res = await fetch('/api/test-cases/execute-all-live', { method: 'POST' });
        const data = await res.json();

        if (data.status === 'success') {
            await loadTestCases();
            await loadDashboard();
            await loadDefects();
            alert(`Batch Execution Complete:\n${data.message}`);
        } else {
            alert(`Error: ${data.message}`);
        }
    } catch (err) {
        alert(`Batch execution failed: ${err.message}`);
    } finally {
        if (btn1) { btn1.disabled = false; btn1.innerHTML = '▶️ Execute All Tests'; }
        if (btn2) { btn2.disabled = false; btn2.innerHTML = '▶️ Execute All Automated Tests'; }
    }
}

window.deleteTestCase = async function(tcId) {
    if (!confirm(`Delete test case '${tcId}'?`)) return;
    try {
        const res = await fetch(`/api/test-cases/${encodeURIComponent(tcId)}`, { method: 'DELETE' });
        const data = await res.json();
        if (data.status === 'success') {
            await loadTestCases();
            await loadDashboard();
            await loadRequirements();
            await loadDefects();
        } else {
            alert(`Error: ${data.message}`);
        }
    } catch (err) {
        alert(`Failed to delete test case: ${err.message}`);
    }
};

// ============================================================================
// 7. MANUAL EXECUTION & EDIT MODAL
// ============================================================================

window.openManualModal = function(tcId) {
    activeModalTcId = tcId;
    const tc = allTestCasesCache.find(t => t.tc_id === tcId);
    if (!tc) return;

    document.getElementById('modalTcTitle').textContent = `Execute / Edit ${tc.tc_id} (${tc.req_code})`;
    document.getElementById('modalTcScenario').textContent = tc.scenario;
    document.getElementById('modalTcInput').value = tc.input_data;
    document.getElementById('modalTcExpected').value = tc.expected_result;
    document.getElementById('manualActualResult').value = tc.actual_result || '';
    document.getElementById('manualStatusSelect').value = tc.status === 'Not Executed' ? 'PASS' : tc.status;
    document.getElementById('manualDefectDesc').value = tc.defect_desc || '';

    const group = document.getElementById('groupDefectDesc');
    if (document.getElementById('manualStatusSelect').value === 'FAIL') {
        group.classList.remove('hidden');
    } else {
        group.classList.add('hidden');
    }

    document.getElementById('modalManualExecute').classList.remove('hidden');
};

function closeManualModal() {
    document.getElementById('modalManualExecute').classList.add('hidden');
    activeModalTcId = null;
}

async function handleRunLiveFromModal() {
    if (!activeModalTcId) return;

    // First update the test case with any modified input data / expected result
    const updatedInput = document.getElementById('modalTcInput').value;
    const updatedExpected = document.getElementById('modalTcExpected').value;

    try {
        await fetch(`/api/test-cases/${encodeURIComponent(activeModalTcId)}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ input_data: updatedInput, expected_result: updatedExpected })
        });

        // Run live against backend
        const res = await fetch(`/api/test-cases/execute-live/${encodeURIComponent(activeModalTcId)}`, { method: 'POST' });
        const data = await res.json();

        if (data.status === 'success') {
            document.getElementById('manualActualResult').value = data.actual_result;
            document.getElementById('manualStatusSelect').value = data.test_status;
            document.getElementById('manualDefectDesc').value = data.defect_desc || '';

            const group = document.getElementById('groupDefectDesc');
            if (data.test_status === 'FAIL') {
                group.classList.remove('hidden');
            } else {
                group.classList.add('hidden');
            }
            alert(`Executed: Result is ${data.test_status}`);
        } else {
            alert(`Notice: ${data.message}`);
        }
    } catch (err) {
        alert(`Failed to execute live: ${err.message}`);
    }
}

async function handleSaveManualExecution() {
    if (!activeModalTcId) return;

    const payload = {
        tc_id: activeModalTcId,
        actual_result: document.getElementById('manualActualResult').value,
        status: document.getElementById('manualStatusSelect').value,
        defect_desc: document.getElementById('manualDefectDesc').value
    };

    try {
        const res = await fetch('/api/test-cases/execute-manual', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.status === 'success') {
            closeManualModal();
            await loadTestCases();
            await loadDashboard();
            await loadDefects();
        } else {
            alert(`Error: ${data.message}`);
        }
    } catch (err) {
        alert(`Failed to save execution: ${err.message}`);
    }
}

// Add Custom Test Case
function openAddTestModal() {
    document.getElementById('formAddTestCase').reset();
    document.getElementById('modalAddTestCase').classList.remove('hidden');
}

async function handleCreateCustomTestCase(e) {
    e.preventDefault();
    const payload = {
        tc_id: document.getElementById('newTcId').value.trim().toUpperCase(),
        req_code: document.getElementById('newTcReqCode').value,
        test_type: document.getElementById('newTcType').value,
        scenario: document.getElementById('newTcScenario').value.trim(),
        input_data: document.getElementById('newTcInputData').value.trim(),
        expected_result: document.getElementById('newTcExpected').value.trim()
    };

    try {
        const res = await fetch('/api/test-cases', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.status === 'success') {
            document.getElementById('modalAddTestCase').classList.add('hidden');
            await loadTestCases();
            await loadDashboard();
            await loadRequirements();
        } else {
            alert(`Error: ${data.message}`);
        }
    } catch (err) {
        alert(`Failed to add test case: ${err.message}`);
    }
}

// ============================================================================
// 8. DEFECT TRACKING & MANAGEMENT (FR9)
// ============================================================================

async function loadDefects() {
    try {
        const res = await fetch('/api/defects');
        const data = await res.json();
        if (data.status === 'success') {
            const defects = data.defects;
            const openCount = defects.filter(d => d.status === 'Open').length;

            document.getElementById('defectCountBadge').textContent = defects.length;
            document.getElementById('defectStatusBadge').textContent = `${openCount} Open`;

            const tbody = document.querySelector('#tableDefects tbody');
            tbody.innerHTML = '';

            if (defects.length === 0) {
                tbody.innerHTML = `<tr><td colspan="8" class="text-center text-success">✅ Zero active defects logged. All executed tests conform to requirements!</td></tr>`;
                return;
            }

            defects.forEach(d => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td><strong>#${d.id}</strong></td>
                    <td><code>${escapeHtml(d.tc_id)}</code></td>
                    <td>${escapeHtml(d.description)}</td>
                    <td><small>${escapeHtml(d.expected_result || '—')}</small></td>
                    <td><small class="text-danger">${escapeHtml(d.actual_result || '—')}</small></td>
                    <td><span class="badge badge-danger">${escapeHtml(d.severity)}</span></td>
                    <td>
                        <select class="form-control form-control-sm" onchange="changeDefectStatus(${d.id}, this.value)">
                            <option value="Open" ${d.status === 'Open' ? 'selected' : ''}>Open</option>
                            <option value="In Progress" ${d.status === 'In Progress' ? 'selected' : ''}>In Progress</option>
                            <option value="Resolved" ${d.status === 'Resolved' ? 'selected' : ''}>Resolved</option>
                            <option value="Closed" ${d.status === 'Closed' ? 'selected' : ''}>Closed</option>
                        </select>
                    </td>
                    <td>
                        <button class="btn btn-xs btn-outline-danger" onclick="deleteDefect(${d.id})" title="Delete defect">
                            🗑️
                        </button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }
    } catch (err) {
        console.error('Failed to load defects:', err);
    }
}

window.changeDefectStatus = async function(defectId, newStatus) {
    try {
        const res = await fetch(`/api/defects/${defectId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: newStatus })
        });
        const data = await res.json();
        if (data.status === 'success') {
            await loadDefects();
            await loadDashboard();
        }
    } catch (err) {
        alert(`Failed to update defect status: ${err.message}`);
    }
};

window.deleteDefect = async function(defectId) {
    if (!confirm(`Delete defect #${defectId}?`)) return;
    try {
        const res = await fetch(`/api/defects/${defectId}`, { method: 'DELETE' });
        const data = await res.json();
        if (data.status === 'success') {
            await loadDefects();
            await loadDashboard();
        }
    } catch (err) {
        alert(`Failed to delete defect: ${err.message}`);
    }
};

// ============================================================================
// 9. STUDENT REGISTRATION PORTAL SANDBOX
// ============================================================================

async function handleSandboxSubmit(e) {
    e.preventDefault();
    const payload = {
        full_name: document.getElementById('sbFullName').value,
        email: document.getElementById('sbEmail').value,
        password: document.getElementById('sbPassword').value,
        phone: document.getElementById('sbPhone').value,
        course: document.getElementById('sbCourse').value
    };

    const box = document.getElementById('sbResponseBox');
    const badge = document.getElementById('sbStatusBadge');
    const time = document.getElementById('sbTimestamp');
    const msg = document.getElementById('sbMessage');
    const code = document.getElementById('sbPayload');

    box.classList.remove('hidden', 'success', 'error');

    try {
        const res = await fetch('/api/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        time.textContent = `Timestamp: ${new Date().toLocaleTimeString()}`;
        badge.textContent = `HTTP ${res.status} ${res.status === 201 ? 'Created' : 'Client Error'}`;
        code.textContent = JSON.stringify(data, null, 2);

        if (res.status === 201) {
            box.classList.add('success');
            msg.textContent = `✅ ${data.message}`;
            document.getElementById('sandboxRegistrationForm').reset();
        } else {
            box.classList.add('error');
            msg.textContent = `❌ ${data.message}`;
        }
    } catch (err) {
        box.classList.add('error');
        badge.textContent = 'Network Error';
        msg.textContent = err.message;
    }
}

// ============================================================================
// 10. TEST REPORTS TAB
// ============================================================================

async function loadReportTab() {
    try {
        // Summary
        const resSum = await fetch('/api/report/summary');
        const dataSum = await resSum.json();
        if (dataSum.status === 'success') {
            const s = dataSum.summary;
            document.getElementById('repTotalReqs').textContent = s.total_requirements;
            document.getElementById('repTotalTests').textContent = s.total_test_cases;
            document.getElementById('repExecuted').textContent = s.tests_executed;
            document.getElementById('repPassed').textContent = s.passed;
            document.getElementById('repFailed').textContent = s.failed;
            document.getElementById('repPending').textContent = s.pending;
            document.getElementById('repDefects').textContent = s.open_defects;
            document.getElementById('repPassRate').textContent = `${s.pass_rate}%`;
        }

        // Comparison Table
        const resTc = await fetch('/api/test-cases');
        const dataTc = await resTc.json();
        if (dataTc.status === 'success') {
            const tbody = document.querySelector('#tableReportComparison tbody');
            tbody.innerHTML = '';

            dataTc.test_cases.forEach(tc => {
                const tr = document.createElement('tr');
                let badge = '<span class="badge badge-warning">Not Executed</span>';
                if (tc.status === 'PASS') badge = '<span class="badge badge-success">PASS</span>';
                if (tc.status === 'FAIL') badge = '<span class="badge badge-danger">FAIL</span>';

                tr.innerHTML = `
                    <td><strong>${escapeHtml(tc.tc_id)}</strong></td>
                    <td>${escapeHtml(tc.scenario)}</td>
                    <td><small>${escapeHtml(tc.expected_result)}</small></td>
                    <td><small>${escapeHtml(tc.actual_result || 'Pending execution')}</small></td>
                    <td>${badge}</td>
                    <td>${escapeHtml(tc.defect_desc || 'None')}</td>
                `;
                tbody.appendChild(tr);
            });
        }
    } catch (err) {
        console.error('Failed to load report tab:', err);
    }
}

// ============================================================================
// 11. RESET DEMO DATA
// ============================================================================

async function handleResetData() {
    const ok = confirm('Reset database back to clean demo state with baseline requirements and test cases? This will clear all execution results and defects.');
    if (!ok) return;

    try {
        const res = await fetch('/api/reset-data', { method: 'POST' });
        const data = await res.json();
        if (data.status === 'success') {
            alert(data.message);
            await loadAllData();
            switchTab('tab-dashboard');
        } else {
            alert(`Error: ${data.message}`);
        }
    } catch (err) {
        alert(`Reset failed: ${err.message}`);
    }
}

// Helper: escape HTML
function escapeHtml(str) {
    if (!str) return '';
    return str
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
