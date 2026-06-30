const state = {
  root: localStorage.getItem('opportunityWorkbench.root') || defaultRoot(),
  reps: [],
  selectedRepId: localStorage.getItem('opportunityWorkbench.repId') || '',
  accounts: [],
  selectedSlug: '',
  account: null,
  tab: 'overview',
  fileKey: '',
  sidebarCollapsed: localStorage.getItem('opportunityWorkbench.sidebarCollapsed') === 'true'
};

const tabs = [
  ['overview', 'Overview'],
  ['research', 'Research'],
  ['artifacts', 'Artifacts'],
  ['timeline', 'Timeline'],
  ['team', 'Team'],
  ['tasks', 'Tasks'],
  ['reminders', 'Reminders']
];

const els = {
  appShell: document.getElementById('appShell'),
  repForm: document.getElementById('repForm'),
  repSelect: document.getElementById('repSelect'),
  newRepButton: document.getElementById('newRepButton'),
  ownerSettings: document.getElementById('ownerSettings'),
  hideSidebarButton: document.getElementById('hideSidebarButton'),
  showSidebarButton: document.getElementById('showSidebarButton'),
  browseFolderButton: document.getElementById('browseFolderButton'),
  repNameInput: document.getElementById('repNameInput'),
  rootInput: document.getElementById('rootInput'),
  rootLabel: document.getElementById('rootLabel'),
  accountList: document.getElementById('accountList'),
  searchInput: document.getElementById('searchInput'),
  dispositionFilter: document.getElementById('dispositionFilter'),
  taskFilter: document.getElementById('taskFilter'),
  statAccounts: document.getElementById('statAccounts'),
  statOpen: document.getElementById('statOpen'),
  statDue: document.getElementById('statDue'),
  emptyState: document.getElementById('emptyState'),
  detailView: document.getElementById('detailView'),
  accountTitle: document.getElementById('accountTitle'),
  accountMeta: document.getElementById('accountMeta'),
  accountBadge: document.getElementById('accountBadge'),
  bootstrapButton: document.getElementById('bootstrapButton'),
  summaryScore: document.getElementById('summaryScore'),
  summaryWedge: document.getElementById('summaryWedge'),
  summaryIntent: document.getElementById('summaryIntent'),
  summaryReminder: document.getElementById('summaryReminder'),
  tabs: document.getElementById('tabs'),
  panel: document.getElementById('panel')
};

init();

function init() {
  els.rootInput.value = state.root;
  setSidebarCollapsed(state.sidebarCollapsed);
  els.repForm.addEventListener('submit', (event) => {
    event.preventDefault();
    saveCurrentRep();
  });
  els.repSelect.addEventListener('change', () => selectRep(els.repSelect.value));
  els.newRepButton.addEventListener('click', startNewRep);
  els.hideSidebarButton.addEventListener('click', () => setSidebarCollapsed(true));
  els.showSidebarButton.addEventListener('click', () => setSidebarCollapsed(false));
  els.browseFolderButton.addEventListener('click', browseForFolder);
  els.searchInput.addEventListener('input', renderAccountList);
  els.dispositionFilter.addEventListener('change', renderAccountList);
  els.taskFilter.addEventListener('change', renderAccountList);
  els.bootstrapButton.addEventListener('click', clearTodoTasks);
  renderTabs();
  loadReps();
}

function setSidebarCollapsed(collapsed) {
  state.sidebarCollapsed = collapsed;
  localStorage.setItem('opportunityWorkbench.sidebarCollapsed', String(collapsed));
  els.appShell.classList.toggle('sidebar-collapsed', collapsed);
  els.showSidebarButton.classList.toggle('hidden', !collapsed);
  els.hideSidebarButton.textContent = collapsed ? 'Hidden' : 'Hide';
  els.hideSidebarButton.title = collapsed ? 'Left pane hidden' : 'Hide left pane';
}

async function browseForFolder() {
  els.browseFolderButton.disabled = true;
  els.browseFolderButton.textContent = 'Browsing...';
  try {
    const result = await api('/api/select-folder', { method: 'POST', body: {} });
    if (result.path) {
      els.rootInput.value = result.path;
      if (!els.repNameInput.value.trim()) {
        els.repNameInput.value = result.path.split(/[\\/]/).filter(Boolean).pop() || '';
      }
    }
  } catch (error) {
    showToast(error.message);
  } finally {
    els.browseFolderButton.disabled = false;
    els.browseFolderButton.textContent = 'Browse';
  }
}

function startNewRep() {
  state.selectedRepId = '';
  state.root = '';
  state.accounts = [];
  state.selectedSlug = '';
  state.account = null;
  els.repSelect.value = '';
  els.repNameInput.value = '';
  els.rootInput.value = '';
  els.rootLabel.textContent = 'New account owner';
  els.rootLabel.title = '';
  els.ownerSettings.open = true;
  renderAccountList();
  showEmpty('Enter the account owner and that owner’s Opportunity Coach research folder, then save.');
}

async function loadReps() {
  try {
    const data = await api('/api/reps');
    state.reps = data.reps || [];
    renderRepSelect();
    const selected = state.reps.find((rep) => rep.id === state.selectedRepId) || state.reps[0];
    if (selected) {
      await selectRep(selected.id);
    } else {
      els.ownerSettings.open = true;
      showEmpty('Add an account owner and choose that owner’s Opportunity Coach research folder.');
    }
  } catch (error) {
    showToast(error.message);
    showEmpty(error.message);
  }
}

function renderRepSelect() {
  els.repSelect.innerHTML = '<option value="">Add/select owner</option>' + state.reps.map((rep) => `<option value="${escAttr(rep.id)}">${esc(rep.name)}</option>`).join('');
}

async function selectRep(repId) {
  const rep = state.reps.find((item) => item.id === repId);
  if (!rep) {
    state.selectedRepId = '';
    state.root = '';
    state.accounts = [];
    renderAccountList();
    return;
  }
  state.selectedRepId = rep.id;
  state.root = rep.root;
  localStorage.setItem('opportunityWorkbench.repId', rep.id);
  localStorage.setItem('opportunityWorkbench.root', rep.root);
  els.repSelect.value = rep.id;
  els.repNameInput.value = rep.name;
  els.rootInput.value = rep.root;
  await loadWorkspace(rep.root, rep);
}

async function saveCurrentRep() {
  const rep = {
    id: state.selectedRepId || undefined,
    name: els.repNameInput.value.trim(),
    root: els.rootInput.value.trim()
  };
  try {
    const data = await api('/api/reps', {
      method: 'POST',
      body: { rep }
    });
    state.reps = data.reps || [];
    renderRepSelect();
    state.selectedRepId = data.rep.id;
    await selectRep(data.rep.id);
    els.ownerSettings.open = false;
    showToast('Account owner saved');
  } catch (error) {
    showToast(error.message);
  }
}

async function loadWorkspace(root, rep = null) {
  try {
    const data = await api(`/api/workspaces?root=${encodeURIComponent(root)}`);
    state.root = data.root;
    state.accounts = data.accounts;
    state.selectedSlug = data.accounts[0]?.slug || '';
    state.account = null;
    localStorage.setItem('opportunityWorkbench.root', data.root);
    els.rootInput.value = data.root;
    els.rootLabel.textContent = workspaceLabel(data.root, rep);
    els.rootLabel.title = data.root;
    renderAccountList();
    if (state.selectedSlug) {
      await loadAccount(state.selectedSlug);
    } else {
      showEmpty('No account folders with account-research.json were found.');
    }
  } catch (error) {
    showToast(error.message);
    showEmpty(error.message);
  }
}

function workspaceLabel(root, rep) {
  const folder = String(root || '').split(/[\\/]/).filter(Boolean).pop() || 'Research folder';
  if (rep?.name && rep.name.toLowerCase() !== folder.toLowerCase()) return `${rep.name} · ${folder}`;
  if (rep?.name) return `${rep.name} workspace`;
  return folder;
}

async function loadAccount(slug) {
  const data = await api(`/api/accounts/${encodeURIComponent(slug)}?root=${encodeURIComponent(state.root)}`);
  state.selectedSlug = slug;
  state.account = data;
  state.fileKey = '';
  els.emptyState.classList.add('hidden');
  els.detailView.classList.remove('hidden');
  renderAccountList();
  renderDetail();
}

function renderAccountList() {
  const query = els.searchInput.value.trim().toLowerCase();
  const disposition = els.dispositionFilter.value;
  const taskFilter = els.taskFilter.value;
  const summaries = accountTaskSummaries();

  const filtered = state.accounts.filter((account) => {
    const summary = account.summary || {};
    const text = JSON.stringify(summary).toLowerCase();
    if (query && !text.includes(query)) return false;
    if (disposition && !String(summary.disposition || '').toLowerCase().includes(disposition)) return false;
    const taskSummary = summaries.get(account.slug) || {};
    if (taskFilter === 'open' && !taskSummary.open) return false;
    if (taskFilter === 'overdue' && !taskSummary.overdue) return false;
    if (taskFilter === 'done' && taskSummary.open) return false;
    return true;
  });

  els.statAccounts.textContent = state.accounts.length;
  els.statOpen.textContent = [...summaries.values()].reduce((sum, item) => sum + (item.open || 0), 0);
  els.statDue.textContent = [...summaries.values()].reduce((sum, item) => sum + (item.overdue || 0), 0);

  els.accountList.innerHTML = filtered.map((account) => {
    const summary = account.summary || {};
    const taskSummary = summaries.get(account.slug) || {};
    const active = account.slug === state.selectedSlug ? ' active' : '';
    return `<div class="account-row${active}" data-slug="${escAttr(account.slug)}" role="button" tabindex="0">
      <span class="row-title"><span>${esc(summary.accountName)}</span><span>${esc(summary.score || '-')}</span></span>
      <span class="row-meta">${esc(summary.topWedge || 'No wedge')} · ${esc(summary.buyerIntent || 'No intent signal')}</span>
      <span class="row-taskline">
        <span class="badge ${badgeClass(summary.disposition)}">${esc(summary.disposition || 'Not scored')}</span>
        <span class="pill">${taskSummary.open || 0} open</span>
        ${taskSummary.overdue ? `<span class="pill overdue">${taskSummary.overdue} due</span>` : ''}
      </span>
    </div>`;
  }).join('') || '<div class="empty-state"><p>No accounts match the filters.</p></div>';

  els.accountList.querySelectorAll('.account-row').forEach((row) => {
    row.addEventListener('click', () => loadAccount(row.dataset.slug));
    row.addEventListener('keydown', (event) => {
      if (event.key !== 'Enter' && event.key !== ' ') return;
      event.preventDefault();
      loadAccount(row.dataset.slug);
    });
  });
}

function accountTaskSummaries() {
  const map = new Map();
  if (state.account?.slug) {
    map.set(state.account.slug, summarizeTasks(state.account.workbench?.tasks || []));
  }
  return map;
}

function renderDetail() {
  const research = state.account.research;
  const summary = summarizeResearch(research, state.selectedSlug);
  els.accountTitle.textContent = summary.accountName;
  els.accountMeta.textContent = `${summary.sourceFolder || state.selectedSlug} · ${research.research_date || 'No research date'}`;
  els.accountBadge.textContent = summary.disposition || 'Not scored';
  els.accountBadge.className = `badge ${badgeClass(summary.disposition)}`;
  els.summaryScore.textContent = summary.score || '-';
  els.summaryWedge.textContent = summary.topWedge || 'Not specified';
  els.summaryIntent.textContent = summary.buyerIntent || 'Not found';
  els.summaryReminder.textContent = nextReminderLabel(state.account.workbench?.tasks || []);
  renderTabs();
  renderPanel();
}

function renderTabs() {
  els.tabs.innerHTML = tabs.map(([key, label]) => `<button class="tab ${state.tab === key ? 'active' : ''}" data-tab="${key}">${label}</button>`).join('');
  els.tabs.querySelectorAll('.tab').forEach((button) => {
    button.addEventListener('click', () => {
      state.tab = button.dataset.tab;
      renderDetail();
    });
  });
}

function renderPanel() {
  const research = state.account.research;
  if (state.tab === 'overview') renderOverview(research);
  if (state.tab === 'research') renderResearch(research);
  if (state.tab === 'artifacts') renderArtifacts(research);
  if (state.tab === 'timeline') renderTimeline();
  if (state.tab === 'team') renderTeam();
  if (state.tab === 'tasks') renderTasks();
  if (state.tab === 'reminders') renderReminders();
}

function renderOverview(research) {
  els.panel.innerHTML = `<div class="grid">
    ${block('Executive Snapshot', value(research.executive_snapshot))}
    ${block('Recommended Next Move', value(research.recommended_next_move))}
    ${block('Validation Needed', list(research.validation_needed))}
    ${block('OCI Hypotheses', list(research.oci_pursuit_hypotheses))}
  </div>`;
}

function renderResearch(research) {
  els.panel.innerHTML = `<div class="grid">
    ${block('Business Overview', objectView(research.business_overview, ['sales_navigator_context']))}
    ${block('Stakeholders', list(research.stakeholders))}
    ${block('Technology Signals', list(research.technology_signals))}
    ${block('Cloud / Stack Posture', objectView(research.tech_stack_cloud_posture))}
    ${block('Objection Prep', objectView(research.oci_buying_objection_prep, ['objection_inventory']))}
    ${block('Source Log', list(research.source_log))}
  </div>`;
}

function renderArtifacts(research) {
  const groups = artifactGroups(research);
  if (!groups.length) {
    els.panel.innerHTML = '<p class="muted">No linked artifacts found.</p>';
    return;
  }
  if (!state.fileKey) state.fileKey = groups[0].key;
  const selected = groups.find((group) => group.key === state.fileKey) || groups[0];
  const folder = research.source_folder || research.account_slug || state.selectedSlug;
  const pdfUrl = selected.pdf ? fileUrl(`${folder}/${selected.pdf}`) : '';
  const docxUrl = selected.docx ? fileUrl(`${folder}/${selected.docx}`) : '';
  els.panel.innerHTML = `<div class="file-tabs">
      ${groups.map((group) => `<button class="file-tab ${group.key === selected.key ? 'active' : ''}" data-key="${escAttr(group.key)}">${esc(group.label)}</button>`).join('')}
    </div>
    <div class="file-actions">
      ${pdfUrl ? `<a href="${pdfUrl}" target="_blank" rel="noreferrer">Open PDF</a>` : ''}
      ${docxUrl ? `<a href="${docxUrl}" target="_blank" rel="noreferrer">Open DOCX</a>` : ''}
      <a href="${fileUrl(`${folder}/account-research.json`)}" target="_blank" rel="noreferrer">Open JSON</a>
    </div>
    ${pdfUrl ? `<iframe class="file-frame" src="${pdfUrl}" title="${escAttr(selected.label)}"></iframe>` : '<p class="muted">No PDF preview for this artifact.</p>'}`;
  els.panel.querySelectorAll('.file-tab').forEach((button) => {
    button.addEventListener('click', () => {
      state.fileKey = button.dataset.key;
      renderArtifacts(research);
    });
  });
}

function renderTeam() {
  const team = [...(state.account.workbench?.team || [])].sort((a, b) => {
    const org = String(a.organization || '').localeCompare(String(b.organization || ''));
    if (org) return org;
    return String(a.name || a.email).localeCompare(String(b.name || b.email));
  });
  els.panel.innerHTML = `<div class="team-board">
    <div class="team-head">
      <div>
        <h3>Account Team</h3>
        <p class="muted">Track Oracle, customer, partner, and internal people involved in this account, including role, email, and how they are helping.</p>
      </div>
      <div class="team-actions">
        <button id="addTeamMember" type="button">Add Person</button>
        <button id="saveTeam" class="primary" type="button">Save Team</button>
        <span class="pill">${team.length} people</span>
      </div>
    </div>
    <div id="teamList" class="team-list"></div>
  </div>`;

  document.getElementById('addTeamMember').addEventListener('click', addTeamMember);
  document.getElementById('saveTeam').addEventListener('click', saveCurrentTeam);
  const listEl = document.getElementById('teamList');
  listEl.innerHTML = team.length ? '' : '<p class="muted">No team members yet. Add Oracle team members, customer champions, partners, or internal stakeholders.</p>';
  for (const member of team) {
    listEl.append(renderTeamMember(member));
  }
}

function renderTeamMember(member) {
  const row = document.createElement('article');
  row.className = 'team-member';
  row.dataset.id = member.id;
  const notes = Array.isArray(member.notes) ? [...member.notes].sort((a, b) => new Date(b.at) - new Date(a.at)) : [];
  row.innerHTML = `
    <div class="team-member-head">
      <input class="team-name" type="text" value="${escAttr(member.name || '')}" placeholder="Name" aria-label="Person name">
      <input class="team-email" type="email" value="${escAttr(member.email || '')}" placeholder="email@example.com" aria-label="Person email">
      <input class="team-role" type="text" value="${escAttr(member.role || '')}" placeholder="Role" aria-label="Person role">
      <select class="team-organization" aria-label="Team organization">
        ${teamOption('oracle', 'Oracle', member.organization)}
        ${teamOption('customer', 'Customer', member.organization)}
        ${teamOption('partner', 'Partner', member.organization)}
        ${teamOption('internal', 'Internal', member.organization)}
        ${teamOption('other', 'Other', member.organization)}
      </select>
      <select class="team-source" aria-label="Team source">
        ${teamOption('manual', 'Manual', member.source)}
        ${teamOption('outlook', 'Outlook', member.source)}
        ${teamOption('slack', 'Slack', member.source)}
        ${teamOption('notes', 'Notes', member.source)}
        ${teamOption('sync', 'Sync', member.source)}
      </select>
      <button class="team-delete" type="button">Delete</button>
    </div>
    <textarea class="team-contribution" rows="3" placeholder="How this person is helping">${esc(member.contribution || '')}</textarea>
    <textarea class="team-relationship" rows="2" placeholder="Relationship, ownership, or account-team context">${esc(member.relationship || '')}</textarea>
    <div class="team-note-composer">
      <input class="team-new-note-at" type="datetime-local" value="${escAttr(toLocalInput(new Date().toISOString()))}" aria-label="Team note timestamp">
      <textarea class="team-new-note-body" rows="2" placeholder="Add a note about this person"></textarea>
      <button class="team-add-note" type="button">Add Note</button>
    </div>
    <div class="team-notes">${notes.length ? '' : '<p class="muted">No notes for this person yet.</p>'}</div>
  `;
  const notesEl = row.querySelector('.team-notes');
  for (const note of notes) {
    notesEl.append(renderTeamNote(note));
  }
  row.querySelector('.team-delete').addEventListener('click', () => row.remove());
  row.querySelector('.team-add-note').addEventListener('click', () => addTeamNote(row));
  return row;
}

function renderTeamNote(note) {
  const row = document.createElement('div');
  row.className = 'team-note';
  row.dataset.id = note.id;
  row.innerHTML = `
    <input class="team-note-at" type="datetime-local" value="${escAttr(toLocalInput(note.at))}" aria-label="Team note time">
    <select class="team-note-source" aria-label="Team note source">
      ${teamOption('manual', 'Manual', note.source)}
      ${teamOption('outlook', 'Outlook', note.source)}
      ${teamOption('slack', 'Slack', note.source)}
      ${teamOption('notes', 'Notes', note.source)}
      ${teamOption('sync', 'Sync', note.source)}
    </select>
    <textarea class="team-note-body" rows="2" placeholder="Note">${esc(note.body || '')}</textarea>
    <button class="team-note-delete" type="button">Delete</button>
  `;
  row.querySelector('.team-note-delete').addEventListener('click', () => row.remove());
  return row;
}

function teamOption(value, label, selected) {
  return `<option value="${value}" ${value === selected ? 'selected' : ''}>${label}</option>`;
}

function renderNotes() {
  const notes = state.account.workbench?.notes || [];
  els.panel.innerHTML = `<div class="notes-layout">
    <form id="addNoteForm" class="add-note">
      <select id="newNoteCategory">${noteCategoryOptions('meeting-minutes')}</select>
      <input id="newNoteTakenAt" type="datetime-local" value="${escAttr(toLocalInput(new Date().toISOString()))}">
      <textarea id="newNoteBody" rows="4" placeholder="New note"></textarea>
      <button type="submit">Add Note</button>
    </form>
    <div class="notes-actions">
      <button id="saveNotes" class="primary" type="button">Save Notes</button>
      <span id="notesStatus" class="notes-status"></span>
    </div>
    <div id="notesList" class="notes-list">${notes.length ? '' : '<p class="muted">No notes yet.</p>'}</div>
  </div>`;
  const listEl = document.getElementById('notesList');
  for (const note of [...notes].sort((a, b) => new Date(b.takenAt) - new Date(a.takenAt))) {
    listEl.append(renderNoteRow(note));
  }
  document.getElementById('addNoteForm').addEventListener('submit', addNote);
  document.getElementById('saveNotes').addEventListener('click', saveCurrentNotes);
}

function renderTimeline() {
  const items = timelineItems();
  els.panel.innerHTML = `<div class="timeline-board">
    <div class="timeline-head">
      <div>
        <h3>Timeline</h3>
      </div>
      <div class="timeline-actions">
        <select id="timelineAddType" aria-label="Add timeline item">
          <option value="note">Add Note</option>
          <option value="meeting-note">Add Meeting Note</option>
          <option value="communication">Add Email/Meeting Thread</option>
        </select>
        <button id="timelineAddButton" type="button">Add</button>
        <button id="timelineSaveButton" class="primary" type="button">Save Timeline</button>
      </div>
    </div>
    <div class="timeline-filters" aria-label="Timeline filters">
      <label title="Item type">Type
        <select id="timelineTypeFilter" aria-label="Timeline type filter">
          <option value="">All</option>
          <option value="note">Notes</option>
          <option value="meeting-minutes">Minutes</option>
          <option value="customer-insight">Insights</option>
          <option value="internal-note">Internal</option>
          <option value="email-thread">Email</option>
          <option value="meeting">Meetings</option>
        </select>
      </label>
      <label title="Source">Source
        <select id="timelineSourceFilter" aria-label="Timeline source filter">
          <option value="">All</option>
          <option value="manual">Manual</option>
          <option value="outlook">Outlook</option>
          <option value="sync">Sync</option>
          <option value="other">Other</option>
        </select>
      </label>
      <label title="Reply status">Reply
        <select id="timelineReplyFilter" aria-label="Reply status filter">
          <option value="">All</option>
          <option value="needs-reply">Needs reply</option>
          <option value="waiting-on-customer">Waiting</option>
          <option value="closed">Closed</option>
        </select>
      </label>
      <span class="pill">${items.length} items</span>
    </div>
    <div id="timelineList" class="timeline-list"></div>
  </div>`;

  document.getElementById('timelineAddButton').addEventListener('click', addTimelineItem);
  document.getElementById('timelineSaveButton').addEventListener('click', saveCurrentTimeline);
  for (const id of ['timelineTypeFilter', 'timelineSourceFilter', 'timelineReplyFilter']) {
    document.getElementById(id).addEventListener('change', renderTimelineList);
  }
  renderTimelineList();
}

function renderTimelineList() {
  const listEl = document.getElementById('timelineList');
  if (!listEl) return;
  const typeFilter = document.getElementById('timelineTypeFilter')?.value || '';
  const sourceFilter = document.getElementById('timelineSourceFilter')?.value || '';
  const replyFilter = document.getElementById('timelineReplyFilter')?.value || '';
  const items = timelineItems().filter((item) => {
    if (typeFilter && item.type !== typeFilter) return false;
    if (sourceFilter && item.sourceGroup !== sourceFilter) return false;
    if (replyFilter && item.replyStatus !== replyFilter) return false;
    return true;
  });
  listEl.innerHTML = items.length ? '' : '<p class="muted">No timeline items match the current filters.</p>';
  for (const item of items) {
    const card = document.createElement('article');
    card.className = `timeline-card ${item.kind}`;
    card.dataset.kind = item.kind;
    card.dataset.id = item.id;
    card.innerHTML = `<div class="timeline-card-head">
      <div>
        <span class="pill ${item.replyStatus === 'needs-reply' ? 'overdue' : ''}">${esc(item.label)}</span>
        <span class="muted">${esc(formatDate(item.at) || 'No timestamp')}</span>
      </div>
      <div class="timeline-card-tools">
        <span class="muted">${esc(item.sourceLabel)}</span>
        <button class="timeline-detail" type="button" title="Show full details">Details</button>
        <button class="timeline-task" type="button" title="Create a task from this item">Task</button>
        <button class="timeline-reminder" type="button" title="Create a reminder from this item">Reminder</button>
        <button class="timeline-edit" type="button" title="Edit">Edit</button>
      </div>
    </div>
    <div class="timeline-card-body"></div>`;
    const body = card.querySelector('.timeline-card-body');
    body.append(item.kind === 'note' ? renderTimelineNoteSummary(item.raw) : renderTimelineCommunicationSummary(item.raw));
    card.querySelector('.timeline-detail').addEventListener('click', () => toggleTimelineDetails(card, item));
    card.querySelector('.timeline-task').addEventListener('click', () => createTaskFromTimeline(item, false));
    card.querySelector('.timeline-reminder').addEventListener('click', () => createTaskFromTimeline(item, true));
    card.querySelector('.timeline-edit').addEventListener('click', () => editTimelineCard(card, item));
    listEl.append(card);
  }
}

function renderTimelineNoteSummary(note) {
  const node = document.createElement('div');
  node.className = 'timeline-summary note-summary';
  node.innerHTML = `
    <div class="timeline-summary-title">${esc(noteTimelineLabel(note.category))}</div>
    <div class="timeline-summary-text">${esc(truncateText(note.body || 'Empty note', 520))}</div>`;
  return node;
}

function renderTimelineCommunicationSummary(thread) {
  const node = document.createElement('div');
  node.className = 'timeline-summary communication-summary';
  const messages = [...(thread.messages || [])].sort((a, b) => new Date(b.at) - new Date(a.at));
  const latest = messages[0];
  const latestText = latest?.preview || latest?.subject || `${messages.length} messages`;
  node.innerHTML = `
    <div class="timeline-summary-title">${esc(thread.subject || 'Untitled thread')}</div>
    <div class="timeline-summary-meta">
      <span>${esc((thread.participants || []).map(formatPerson).filter(Boolean).slice(0, 4).join(', ') || 'No participants')}</span>
      <span>${esc(thread.status || 'open')}</span>
    </div>
    <div class="timeline-summary-text">${esc(truncateText(latestText, 520))}</div>
  `;
  return node;
}

function toggleTimelineDetails(card, item) {
  const existing = card.querySelector('.timeline-full');
  const button = card.querySelector('.timeline-detail');
  if (existing) {
    existing.remove();
    button.textContent = 'Details';
    button.title = 'Show full details';
    return;
  }
  const node = item.kind === 'note' ? renderFullTimelineNote(item.raw) : renderFullTimelineCommunication(item.raw);
  card.querySelector('.timeline-card-body').append(node);
  button.textContent = 'Hide';
  button.title = 'Hide full details';
}

function renderFullTimelineNote(note) {
  const node = document.createElement('div');
  node.className = 'timeline-full';
  node.innerHTML = `
    <div class="timeline-full-meta">
      <span class="pill">${esc(noteTimelineLabel(note.category))}</span>
      <span class="muted">${esc(formatDate(note.takenAt) || 'No timestamp')}</span>
    </div>
    <div class="prose">${esc(note.body || 'Empty note')}</div>
  `;
  return node;
}

function renderFullTimelineCommunication(thread) {
  const node = document.createElement('div');
  node.className = 'timeline-full';
  const participants = (thread.participants || []).map(formatPerson).filter(Boolean);
  const messages = [...(thread.messages || [])].sort((a, b) => new Date(a.at) - new Date(b.at));
  node.innerHTML = `
    <div class="timeline-full-meta">
      <span class="pill">${esc(thread.type || 'email')}</span>
      <span class="pill ${thread.status === 'needs-reply' ? 'overdue' : ''}">${esc(thread.status || 'open')}</span>
      <span class="muted">${esc(participants.join(', ') || 'No participants')}</span>
    </div>
    <div class="timeline-message-list">
      ${messages.map((message) => `<div class="timeline-message ${escAttr(message.direction || '')}">
        <div class="timeline-message-meta">
          <strong>${esc(message.direction || 'message')}</strong>
          <span>${esc(formatDate(message.at) || 'No timestamp')}</span>
          <span>${esc(message.from || '')}</span>
        </div>
        <div class="timeline-message-subject">${esc(message.subject || '')}</div>
        <div class="prose">${esc(message.preview || '')}</div>
        ${message.webLink ? `<a href="${escAttr(message.webLink)}" target="_blank" rel="noreferrer">Open source item</a>` : ''}
      </div>`).join('') || '<p class="muted">No messages in this thread.</p>'}
    </div>
  `;
  return node;
}

function editTimelineCard(card, item) {
  const body = card.querySelector('.timeline-card-body');
  body.innerHTML = '';
  body.append(item.kind === 'note' ? renderNoteRow(item.raw) : renderCommunicationThread(item.raw));
  card.classList.add('editing');
  const button = card.querySelector('.timeline-edit');
  const doneButton = button.cloneNode(true);
  doneButton.textContent = 'Done';
  doneButton.title = 'Done editing';
  doneButton.addEventListener('click', saveCurrentTimeline);
  button.replaceWith(doneButton);
  for (const deleteButton of card.querySelectorAll('.note-delete, .comm-delete')) {
    const replacement = deleteButton.cloneNode(true);
    replacement.addEventListener('click', () => card.remove());
    deleteButton.replaceWith(replacement);
  }
}

async function createTaskFromTimeline(item, reminderOnly) {
  const now = new Date();
  const dueAt = new Date(now.getTime() + 24 * 60 * 60 * 1000).toISOString();
  const remindAt = reminderOnly ? dueAt : '';
  const task = {
    id: `timeline-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`,
    source: 'user',
    category: reminderOnly ? 'follow-up' : timelineTaskCategory(item),
    title: timelineTaskTitle(item, reminderOnly),
    status: 'open',
    dueAt,
    remindAt,
    completedAt: '',
    notes: timelineTaskNotes(item),
    createdAt: now.toISOString(),
    updatedAt: now.toISOString()
  };
  if (item.kind === 'communication') {
    task.recipient = (item.raw.participants || []).map(formatPerson).filter(Boolean).join(', ');
    task.subject = item.raw.subject || '';
    task.message = '';
  }
  const result = await api(`/api/accounts/${encodeURIComponent(state.selectedSlug)}/tasks?root=${encodeURIComponent(state.root)}`, {
    method: 'PUT',
    body: { tasks: [...(state.account.workbench.tasks || []), task] }
  });
  state.account.workbench.tasks = result.tasks;
  renderAccountList();
  showToast(reminderOnly ? 'Reminder task created' : 'Task created');
}

function timelineTaskCategory(item) {
  if (item.kind === 'communication') return 'email';
  if (item.type === 'meeting-minutes') return 'follow-up';
  if (item.type === 'customer-insight') return 'discovery';
  return 'todo';
}

function timelineTaskTitle(item, reminderOnly) {
  const prefix = reminderOnly ? 'Follow up on' : 'Task from';
  if (item.kind === 'communication') return `${prefix} ${item.raw.subject || 'communication thread'}`;
  return `${prefix} ${noteTimelineLabel(item.raw.category)}`;
}

function timelineTaskNotes(item) {
  if (item.kind === 'communication') {
    const latest = [...(item.raw.messages || [])].sort((a, b) => new Date(b.at) - new Date(a.at))[0];
    return [
      `Created from timeline ${item.label}.`,
      item.raw.subject ? `Subject: ${item.raw.subject}` : '',
      latest?.preview ? `Latest: ${latest.preview}` : ''
    ].filter(Boolean).join('\n');
  }
  return `Created from timeline ${noteTimelineLabel(item.raw.category)}.\n\n${truncateText(item.raw.body || '', 1000)}`;
}

function timelineItems() {
  const notes = (state.account.workbench?.notes || []).map((note) => ({
    kind: 'note',
    id: note.id,
    type: note.category || 'note',
    label: noteTimelineLabel(note.category),
    at: note.takenAt || note.createdAt,
    sourceGroup: note.source ? sourceGroup(note.source) : 'manual',
    sourceLabel: note.source || 'Manual note',
    replyStatus: '',
    raw: note
  }));
  const communications = (state.account.workbench?.communications || []).map((thread) => ({
    kind: 'communication',
    id: thread.id,
    type: thread.type === 'meeting' ? 'meeting' : 'email-thread',
    label: thread.type === 'meeting' ? 'Meeting' : 'Email Thread',
    at: communicationLastIso(thread),
    sourceGroup: sourceGroup(thread.source),
    sourceLabel: thread.source || 'Manual',
    replyStatus: thread.status || '',
    raw: thread
  }));
  return [...notes, ...communications].sort((a, b) => new Date(b.at || 0) - new Date(a.at || 0));
}

function noteTimelineLabel(category) {
  const labels = {
    'meeting-minutes': 'Meeting Minutes',
    'customer-insight': 'Customer Insight',
    'internal-note': 'Internal',
    'phone-conversation': 'Phone Conversation',
    'field-insight': 'Field Insight',
    'next-step': 'Next Step',
    other: 'Note'
  };
  return labels[category] || 'Note';
}

function sourceGroup(source) {
  const value = String(source || '').toLowerCase();
  if (value.includes('outlook') || value.includes('zoom')) return 'outlook';
  if (value === 'manual') return 'manual';
  if (value === 'sync') return 'sync';
  return value ? 'other' : 'manual';
}

function communicationLastIso(thread) {
  const times = (thread.messages || []).map((message) => message.at).filter(Boolean);
  return times.sort((a, b) => new Date(b) - new Date(a))[0] || thread.updatedAt || thread.createdAt;
}

function renderNoteRow(note) {
  const row = document.createElement('article');
  row.className = 'note-row';
  row.dataset.id = note.id;
  row.innerHTML = `
    <div class="note-head">
      <select class="note-category">${noteCategoryOptions(note.category)}</select>
      <input class="note-taken" type="datetime-local" value="${escAttr(toLocalInput(note.takenAt))}">
      <button class="note-delete" type="button">Delete</button>
    </div>
    <textarea class="note-body" rows="5">${esc(note.body || '')}</textarea>
    <div class="muted">Created ${esc(formatDate(note.createdAt) || 'now')}</div>
  `;
  row.querySelector('.note-delete').addEventListener('click', () => row.remove());
  return row;
}

function noteCategoryOptions(selected) {
  const categories = [
    ['meeting-minutes', 'Minutes of meeting'],
    ['phone-conversation', 'Phone conversation'],
    ['field-insight', 'Field insight'],
    ['customer-insight', 'Customer insight'],
    ['internal-note', 'Internal note'],
    ['next-step', 'Next step'],
    ['other', 'Other']
  ];
  return categories.map(([value, label]) => `<option value="${value}" ${value === selected ? 'selected' : ''}>${label}</option>`).join('');
}

function renderTasks() {
  const allTasks = [...(state.account.workbench?.tasks || [])].sort((a, b) => taskSortTime(a) - taskSortTime(b));
  els.panel.innerHTML = `<div class="task-board">
    <form id="addTaskForm" class="add-task">
      <input id="newTaskTitle" type="text" placeholder="New task">
      <select id="newTaskCategory">
        <option value="todo">Todo</option>
        <option value="email">Email</option>
        <option value="follow-up">Follow-up</option>
        <option value="outreach">Outreach</option>
        <option value="discovery">Discovery</option>
        <option value="internal">Internal</option>
      </select>
      <button type="submit">Add</button>
    </form>
    <div class="task-filters">
      <select id="taskCategoryFilter" aria-label="Task category filter">
        <option value="">All categories</option>
        <option value="todo">Todo</option>
        <option value="email">Email</option>
        <option value="follow-up">Follow-up</option>
        <option value="outreach">Outreach</option>
        <option value="discovery">Discovery</option>
        <option value="internal">Internal</option>
      </select>
      <select id="taskStatusFilter" aria-label="Task status filter">
        <option value="">All statuses</option>
        <option value="open">Open</option>
        <option value="done">Done</option>
        <option value="snoozed">Snoozed</option>
        <option value="overdue">Overdue</option>
      </select>
      <select id="taskSourceFilter" aria-label="Task source filter">
        <option value="">All sources</option>
        <option value="user">User</option>
        <option value="email-task">Email task</option>
        <option value="sync">Sync</option>
        <option value="opportunity-coach">Opportunity Coach</option>
      </select>
      <span class="pill">${allTasks.length} tasks</span>
    </div>
    <div class="task-actions">
      <button id="saveTasks" class="primary" type="button">Save Tasks</button>
      <span id="taskStatus" class="task-status"></span>
    </div>
    <div id="taskList" class="task-list"></div>
  </div>`;
  document.getElementById('addTaskForm').addEventListener('submit', addTask);
  document.getElementById('saveTasks').addEventListener('click', saveCurrentTasks);
  for (const id of ['taskCategoryFilter', 'taskStatusFilter', 'taskSourceFilter']) {
    document.getElementById(id).addEventListener('change', renderTaskList);
  }
  renderTaskList();
}

function renderTaskList() {
  const allTasks = [...(state.account.workbench?.tasks || [])].sort((a, b) => taskSortTime(a) - taskSortTime(b));
  const filters = currentTaskFilters();
  const tasks = allTasks.filter((task) => taskMatchesFilters(task, filters));
  const listEl = document.getElementById('taskList');
  if (!listEl) return;
  listEl.innerHTML = tasks.length ? '' : '<p class="muted">No tasks in this view.</p>';
  for (const task of tasks) {
    listEl.append(renderTaskRow(task));
  }
}

function renderTaskRow(task) {
  const template = document.getElementById('taskTemplate');
  const row = template.content.firstElementChild.cloneNode(true);
  row.dataset.id = task.id;
  row.querySelector('.task-done').checked = task.status === 'done';
  row.querySelector('.task-title').value = task.title;
  row.querySelector('.task-title').classList.toggle('done', task.status === 'done');
  row.querySelector('.task-category').value = task.category || 'todo';
  row.querySelector('.task-due').value = toLocalInput(task.dueAt);
  row.querySelector('.task-remind').value = toLocalInput(task.remindAt);
  row.querySelector('.task-recipient').value = task.recipient || '';
  row.querySelector('.task-subject').value = task.subject || '';
  row.querySelector('.task-message').value = task.message || '';
  row.querySelector('.task-notes').value = task.notes || '';
  const meta = document.createElement('div');
  meta.className = 'task-meta';
  meta.innerHTML = `
    <span class="pill ${task.category === 'email' ? 'email' : ''}">${esc(task.category)}</span>
    <span class="pill">${esc(task.source)}</span>
    <span class="pill task-date-pill">Due: ${esc(formatDate(task.dueAt) || 'Not set')}</span>
    <span class="pill task-date-pill">Reminder: ${esc(formatDate(task.remindAt) || 'Not set')}</span>
    ${isOverdue(task) ? '<span class="pill overdue">Overdue</span>' : ''}`;
  row.append(meta);
  row.querySelector('.task-done').addEventListener('change', () => {
    row.querySelector('.task-title').classList.toggle('done', row.querySelector('.task-done').checked);
  });
  row.querySelector('.task-category').addEventListener('change', () => updateEmailFields(row));
  row.querySelector('.task-delete').addEventListener('click', () => row.remove());
  updateEmailFields(row);
  return row;
}

function renderReminders() {
  const tasks = state.account.workbench?.tasks || [];
  const reminders = tasks
    .filter((task) => task.remindAt || task.dueAt || task.status === 'done')
    .sort((a, b) => reminderTime(a) - reminderTime(b));
  els.panel.innerHTML = `<div class="reminder-list">
    ${reminders.map((task) => `<article class="reminder-card">
      <div><strong>${esc(task.title)}</strong></div>
      <div class="task-meta">
        <span class="pill ${task.status === 'done' ? 'done' : ''}">${esc(task.status)}</span>
        <span class="pill">${esc(task.category)}</span>
        ${isOverdue(task) ? '<span class="pill overdue">Overdue</span>' : ''}
      </div>
      <div class="muted">Reminder: ${esc(formatDate(task.remindAt) || 'None')} · Due: ${esc(formatDate(task.dueAt) || 'None')}</div>
    </article>`).join('') || '<p class="muted">No reminders or due dates set.</p>'}
  </div>`;
}

function renderCommunications() {
  const threads = [...(state.account.workbench?.communications || [])].sort((a, b) => {
    const aTime = communicationLastTime(a);
    const bTime = communicationLastTime(b);
    return bTime - aTime;
  });
  els.panel.innerHTML = `<div class="communication-board">
    <div class="communication-head">
      <div>
        <h3>Meetings & Email Timeline</h3>
        <p class="muted">Synced and manual items are grouped as one thread per email conversation or meeting. Edit fields here to override synced details locally.</p>
      </div>
      <div class="communication-actions">
        <button id="addCommunicationThread" type="button">Add Thread</button>
        <button id="saveCommunications" class="primary" type="button">Save Changes</button>
        <span class="pill">${threads.length} threads</span>
      </div>
    </div>
    <div id="communicationList" class="communication-list"></div>
  </div>`;

  document.getElementById('addCommunicationThread').addEventListener('click', addCommunicationThread);
  document.getElementById('saveCommunications').addEventListener('click', saveCurrentCommunications);
  const listEl = document.getElementById('communicationList');
  listEl.innerHTML = threads.length ? '' : '<p class="muted">No synced emails or meetings yet. Add one manually or wait for the daily 8 AM sync.</p>';
  for (const thread of threads) {
    listEl.append(renderCommunicationThread(thread));
  }
}

function renderCommunicationThread(thread) {
  const messages = [...(thread.messages || [])].sort((a, b) => new Date(a.at) - new Date(b.at));
  const participants = (thread.participants || []).map(formatPerson).filter(Boolean);
  const row = document.createElement('article');
  row.className = 'communication-thread';
  row.dataset.id = thread.id;
  row.innerHTML = `
    <div class="communication-edit-head">
      <input class="comm-subject" type="text" value="${escAttr(thread.subject || '')}" aria-label="Thread subject">
      <select class="comm-type" aria-label="Thread type">
        ${communicationOption('email', 'Email', thread.type)}
        ${communicationOption('meeting', 'Meeting', thread.type)}
        ${communicationOption('mixed', 'Mixed', thread.type)}
      </select>
      <select class="comm-status" aria-label="Thread status">
        ${communicationOption('open', 'Open', thread.status)}
        ${communicationOption('needs-reply', 'Needs reply', thread.status)}
        ${communicationOption('waiting-on-customer', 'Waiting on customer', thread.status)}
        ${communicationOption('closed', 'Closed', thread.status)}
      </select>
      <button class="comm-delete" type="button">Delete</button>
    </div>
    <textarea class="comm-participants" rows="2" placeholder="Participants, one per line or comma-separated">${esc(participants.join('\n'))}</textarea>
    <div class="communication-meta">
      <label>Customer replied <input class="comm-customer-replied" type="datetime-local" value="${escAttr(toLocalInput(thread.customerLastRepliedAt))}"></label>
      <label>My last reply <input class="comm-owner-replied" type="datetime-local" value="${escAttr(toLocalInput(thread.ownerLastRepliedAt))}"></label>
      <label>Reply by <input class="comm-reply-by" type="datetime-local" value="${escAttr(toLocalInput(thread.replyByAt))}"></label>
    </div>
    <div class="message-toolbar">
      <span class="muted">${messages.length} messages</span>
      <button class="comm-add-message" type="button">Add Message</button>
    </div>
    <div class="message-list"></div>
  `;
  const list = row.querySelector('.message-list');
  list.innerHTML = messages.length ? '' : '<p class="muted">No messages captured in this thread.</p>';
  for (const message of messages) {
    list.append(renderCommunicationMessage(message));
  }
  row.querySelector('.comm-delete').addEventListener('click', () => row.remove());
  row.querySelector('.comm-add-message').addEventListener('click', () => {
    const placeholder = list.querySelector('p.muted');
    if (placeholder) placeholder.remove();
    list.append(renderCommunicationMessage(newCommunicationMessage()));
  });
  return row;
}

function renderCommunicationMessage(message) {
  const row = document.createElement('div');
  row.className = `message-row editable ${message.direction || 'internal'}`;
  row.dataset.id = message.id;
  row.innerHTML = `
    <input class="message-at" type="datetime-local" value="${escAttr(toLocalInput(message.at))}" aria-label="Message time">
    <select class="message-direction" aria-label="Message direction">
      ${communicationOption('inbound', 'Inbound', message.direction)}
      ${communicationOption('outbound', 'Outbound', message.direction)}
      ${communicationOption('internal', 'Internal', message.direction)}
    </select>
    <input class="message-from" type="text" value="${escAttr(formatPerson(message.from) || '')}" placeholder="From">
    <input class="message-subject" type="text" value="${escAttr(message.subject || '')}" placeholder="Subject">
    <textarea class="message-preview" rows="2" placeholder="Preview or summary">${esc(message.preview || '')}</textarea>
    <input class="message-link" type="url" value="${escAttr(message.webLink || '')}" placeholder="Outlook link">
    <label class="message-attachment"><input class="message-attachments" type="checkbox" ${message.hasAttachments ? 'checked' : ''}> Attachments</label>
    <button class="message-delete" type="button">Delete</button>
  `;
  row.querySelector('.message-delete').addEventListener('click', () => row.remove());
  row.querySelector('.message-direction').addEventListener('change', (event) => {
    row.classList.remove('inbound', 'outbound', 'internal');
    row.classList.add(event.target.value);
  });
  return row;
}

function communicationOption(value, label, selected) {
  return `<option value="${value}" ${value === selected ? 'selected' : ''}>${label}</option>`;
}

async function saveCurrentNotes() {
  const notes = readNoteRows();
  const result = await api(`/api/accounts/${encodeURIComponent(state.selectedSlug)}/notes?root=${encodeURIComponent(state.root)}`, {
    method: 'PUT',
    body: { notes }
  });
  state.account.workbench.notes = result.notes;
  document.getElementById('notesStatus').textContent = `Saved ${new Date().toLocaleTimeString()}`;
  renderPanel();
}

async function saveCurrentTimeline() {
  const notes = readTimelineNotes();
  const communications = readTimelineCommunications();
  const [notesResult, communicationsResult] = await Promise.all([
    api(`/api/accounts/${encodeURIComponent(state.selectedSlug)}/notes?root=${encodeURIComponent(state.root)}`, {
      method: 'PUT',
      body: { notes }
    }),
    api(`/api/accounts/${encodeURIComponent(state.selectedSlug)}/communications?root=${encodeURIComponent(state.root)}`, {
      method: 'PUT',
      body: { communications }
    })
  ]);
  state.account.workbench.notes = notesResult.notes;
  state.account.workbench.communications = communicationsResult.communications;
  renderDetail();
  showToast('Timeline saved');
}

async function saveCurrentTasks() {
  const edited = readTaskRows();
  const editedIds = new Set(edited.map((task) => task.id));
  const filters = currentTaskFilters();
  const hidden = (state.account.workbench?.tasks || []).filter((task) => {
    return !taskMatchesFilters(task, filters) && !editedIds.has(task.id);
  });
  const result = await api(`/api/accounts/${encodeURIComponent(state.selectedSlug)}/tasks?root=${encodeURIComponent(state.root)}`, {
    method: 'PUT',
    body: { tasks: [...hidden, ...edited] }
  });
  state.account.workbench.tasks = result.tasks;
  renderDetail();
  renderAccountList();
  showToast('Tasks saved');
}

async function clearTodoTasks() {
  const hidden = (state.account.workbench?.tasks || []).filter((task) => task.category === 'email' || task.source === 'email-task');
  const result = await api(`/api/accounts/${encodeURIComponent(state.selectedSlug)}/tasks?root=${encodeURIComponent(state.root)}`, {
    method: 'PUT',
    body: { tasks: hidden }
  });
  state.account.workbench.tasks = result.tasks;
  renderDetail();
  renderAccountList();
  showToast('Todo tasks cleared');
}

async function saveCurrentCommunications() {
  const communications = readCommunicationRows();
  const result = await api(`/api/accounts/${encodeURIComponent(state.selectedSlug)}/communications?root=${encodeURIComponent(state.root)}`, {
    method: 'PUT',
    body: { communications }
  });
  state.account.workbench.communications = result.communications;
  renderDetail();
  showToast('Meetings & Email saved');
}

async function saveCurrentTeam() {
  const team = readTeamRows();
  const result = await api(`/api/accounts/${encodeURIComponent(state.selectedSlug)}/team?root=${encodeURIComponent(state.root)}`, {
    method: 'PUT',
    body: { team }
  });
  state.account.workbench.team = result.team;
  renderDetail();
  showToast('Team saved');
}

function addCommunicationThread() {
  state.account.workbench.communications.push(newCommunicationThread());
  renderPanel();
}

function addTimelineItem() {
  const type = document.getElementById('timelineAddType').value;
  const now = new Date().toISOString();
  if (type === 'communication') {
    state.account.workbench.communications.push(newCommunicationThread());
  } else {
    state.account.workbench.notes.push({
      id: `note-${Date.now().toString(36)}`,
      category: type === 'meeting-note' ? 'meeting-minutes' : 'other',
      body: '',
      takenAt: now,
      createdAt: now,
      updatedAt: now
    });
  }
  renderPanel();
}

function addTeamMember() {
  const now = new Date().toISOString();
  if (!Array.isArray(state.account.workbench.team)) state.account.workbench.team = [];
  state.account.workbench.team.push({
    id: `team-${Date.now().toString(36)}`,
    name: '',
    email: '',
    role: '',
    organization: 'oracle',
    contribution: '',
    relationship: '',
    source: 'manual',
    notes: [],
    createdAt: now,
    updatedAt: now
  });
  renderPanel();
}

function addTeamNote(memberRow) {
  const bodyInput = memberRow.querySelector('.team-new-note-body');
  const body = bodyInput.value.trim();
  if (!body) return;
  const notesEl = memberRow.querySelector('.team-notes');
  const placeholder = notesEl.querySelector('p.muted');
  if (placeholder) placeholder.remove();
  notesEl.prepend(renderTeamNote({
    id: `team-note-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`,
    at: fromLocalInput(memberRow.querySelector('.team-new-note-at').value) || new Date().toISOString(),
    body,
    source: 'manual'
  }));
  bodyInput.value = '';
  memberRow.querySelector('.team-new-note-at').value = toLocalInput(new Date().toISOString());
}

function readCommunicationRows() {
  return [...document.querySelectorAll('.communication-thread')].map(readCommunicationRow).filter((thread) => thread.subject);
}

function readTeamRows() {
  return [...document.querySelectorAll('.team-member')].map((row) => {
    const original = (state.account.workbench.team || []).find((member) => member.id === row.dataset.id) || {};
    return {
      ...original,
      id: row.dataset.id,
      name: row.querySelector('.team-name').value.trim(),
      email: row.querySelector('.team-email').value.trim(),
      role: row.querySelector('.team-role').value.trim(),
      organization: row.querySelector('.team-organization').value,
      source: row.querySelector('.team-source').value,
      contribution: row.querySelector('.team-contribution').value.trim(),
      relationship: row.querySelector('.team-relationship').value.trim(),
      notes: readTeamNotes(row)
    };
  }).filter((member) => member.name || member.email);
}

function readTeamNotes(memberRow) {
  return [...memberRow.querySelectorAll('.team-note')].map((row) => ({
    id: row.dataset.id,
    at: fromLocalInput(row.querySelector('.team-note-at').value) || new Date().toISOString(),
    source: row.querySelector('.team-note-source').value,
    body: row.querySelector('.team-note-body').value.trim()
  })).filter((note) => note.body);
}

function readTimelineNotes() {
  return [...document.querySelectorAll('.timeline-card[data-kind="note"]')].map((card) => {
    const noteRow = card.querySelector('.note-row');
    if (noteRow) return readNoteRow(noteRow);
    return (state.account.workbench.notes || []).find((note) => note.id === card.dataset.id);
  }).filter((note) => note && String(note.body || '').trim());
}

function readTimelineCommunications() {
  return [...document.querySelectorAll('.timeline-card[data-kind="communication"]')].map((card) => {
    const communicationRow = card.querySelector('.communication-thread');
    if (communicationRow) return readCommunicationRow(communicationRow);
    return (state.account.workbench.communications || []).find((thread) => thread.id === card.dataset.id);
  }).filter((thread) => thread && String(thread.subject || '').trim());
}

function readCommunicationRow(row) {
  const original = (state.account.workbench.communications || []).find((thread) => thread.id === row.dataset.id) || {};
  const messages = [...row.querySelectorAll('.message-row.editable')].map((messageRow) => {
    const originalMessage = (original.messages || []).find((message) => message.id === messageRow.dataset.id) || {};
    return {
      ...originalMessage,
      id: messageRow.dataset.id,
      type: 'email',
      direction: messageRow.querySelector('.message-direction').value,
      from: messageRow.querySelector('.message-from').value.trim(),
      at: fromLocalInput(messageRow.querySelector('.message-at').value) || new Date().toISOString(),
      subject: messageRow.querySelector('.message-subject').value.trim(),
      preview: messageRow.querySelector('.message-preview').value.trim(),
      webLink: messageRow.querySelector('.message-link').value.trim(),
      hasAttachments: messageRow.querySelector('.message-attachments').checked
    };
  });
  return {
    ...original,
    id: row.dataset.id,
    source: original.source === 'outlook' ? 'outlook' : 'manual',
    type: row.querySelector('.comm-type').value,
    subject: row.querySelector('.comm-subject').value.trim(),
    participants: splitParticipants(row.querySelector('.comm-participants').value),
    customerLastRepliedAt: fromLocalInput(row.querySelector('.comm-customer-replied').value),
    ownerLastRepliedAt: fromLocalInput(row.querySelector('.comm-owner-replied').value),
    replyByAt: fromLocalInput(row.querySelector('.comm-reply-by').value),
    status: row.querySelector('.comm-status').value,
    messages
  };
}

function splitParticipants(value) {
  return String(value || '')
    .split(/\n|,/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function newCommunicationThread() {
  const now = new Date().toISOString();
  return {
    id: `manual-thread-${Date.now().toString(36)}`,
    source: 'manual',
    type: 'email',
    subject: 'New communication thread',
    participants: [],
    customerLastRepliedAt: '',
    ownerLastRepliedAt: '',
    replyByAt: '',
    status: 'open',
    messages: [],
    createdAt: now,
    updatedAt: now
  };
}

function newCommunicationMessage() {
  return {
    id: `manual-message-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`,
    type: 'email',
    direction: 'internal',
    from: '',
    at: new Date().toISOString(),
    subject: '',
    preview: '',
    webLink: '',
    hasAttachments: false
  };
}

function addTask(event) {
  event.preventDefault();
  const input = document.getElementById('newTaskTitle');
  const title = input.value.trim();
  if (!title) return;
  const now = new Date().toISOString();
  const task = {
    id: `user-${Date.now().toString(36)}`,
    source: 'user',
    category: document.getElementById('newTaskCategory').value,
    recipient: '',
    subject: '',
    message: '',
    title,
    status: 'open',
    dueAt: '',
    remindAt: '',
    completedAt: '',
    notes: '',
    createdAt: now,
    updatedAt: now
  };
  state.account.workbench.tasks.push(task);
  input.value = '';
  renderPanel();
}

function readTaskRows() {
  return [...document.querySelectorAll('.task-row')].map((row) => {
    const original = (state.account.workbench.tasks || []).find((task) => task.id === row.dataset.id) || {};
    const done = row.querySelector('.task-done').checked;
    return {
      ...original,
      id: row.dataset.id,
      title: row.querySelector('.task-title').value,
      category: row.querySelector('.task-category').value,
      recipient: row.querySelector('.task-recipient').value,
      subject: row.querySelector('.task-subject').value,
      message: row.querySelector('.task-message').value,
      status: done ? 'done' : 'open',
      dueAt: fromLocalInput(row.querySelector('.task-due').value),
      remindAt: fromLocalInput(row.querySelector('.task-remind').value),
      completedAt: done ? (original.completedAt || new Date().toISOString()) : '',
      notes: row.querySelector('.task-notes').value
    };
  });
}

function addNote(event) {
  event.preventDefault();
  const body = document.getElementById('newNoteBody').value.trim();
  if (!body) return;
  const now = new Date().toISOString();
  state.account.workbench.notes.push({
    id: `note-${Date.now().toString(36)}`,
    category: document.getElementById('newNoteCategory').value,
    body,
    takenAt: fromLocalInput(document.getElementById('newNoteTakenAt').value) || now,
    createdAt: now,
    updatedAt: now
  });
  renderPanel();
}

function readNoteRows() {
  return [...document.querySelectorAll('.note-row')].map(readNoteRow).filter((note) => note.body.trim());
}

function readNoteRow(row) {
  const original = (state.account.workbench.notes || []).find((note) => note.id === row.dataset.id) || {};
  return {
    ...original,
    id: row.dataset.id,
    category: row.querySelector('.note-category').value,
    takenAt: fromLocalInput(row.querySelector('.note-taken').value) || new Date().toISOString(),
    body: row.querySelector('.note-body').value
  };
}

function updateEmailFields(row) {
  const isEmail = row.querySelector('.task-category').value === 'email';
  row.querySelector('.email-fields').classList.toggle('hidden', !isEmail);
}

async function api(url, options = {}) {
  const response = await fetch(url, {
    method: options.method || 'GET',
    headers: options.body ? { 'Content-Type': 'application/json' } : undefined,
    body: options.body ? JSON.stringify(options.body) : undefined
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'Request failed');
  return data;
}

function summarizeTasks(tasks) {
  return {
    open: tasks.filter((task) => task.status !== 'done').length,
    overdue: tasks.filter(isOverdue).length
  };
}

function isOverdue(task) {
  if (task.status === 'done') return false;
  const value = task.remindAt || task.dueAt;
  return value ? new Date(value).getTime() < Date.now() : false;
}

function nextReminderLabel(tasks) {
  const upcoming = tasks
    .filter((task) => task.status !== 'done' && (task.remindAt || task.dueAt))
    .sort((a, b) => reminderTime(a) - reminderTime(b))[0];
  return upcoming ? formatDate(upcoming.remindAt || upcoming.dueAt) : 'None scheduled';
}

function reminderTime(task) {
  return new Date(task.remindAt || task.dueAt || task.completedAt || '9999-12-31').getTime();
}

function taskSortTime(task) {
  return new Date(task.remindAt || task.dueAt || task.createdAt || '9999-12-31').getTime();
}

function currentTaskFilters() {
  return {
    category: document.getElementById('taskCategoryFilter')?.value || '',
    status: document.getElementById('taskStatusFilter')?.value || '',
    source: document.getElementById('taskSourceFilter')?.value || ''
  };
}

function taskMatchesFilters(task, filters) {
  if (filters.category && task.category !== filters.category) return false;
  if (filters.source && task.source !== filters.source) return false;
  if (filters.status === 'overdue') return isOverdue(task);
  if (filters.status && task.status !== filters.status) return false;
  return true;
}

function communicationLastTime(thread) {
  return Math.max(0, ...(thread.messages || []).map((message) => new Date(message.at).getTime() || 0));
}

function formatPerson(value) {
  if (!value) return '';
  if (typeof value === 'string') return value;
  if (typeof value !== 'object') return String(value);
  const email = value.email || value.address || value.emailAddress?.address || '';
  const name = value.name || value.displayName || value.emailAddress?.name || '';
  const type = value.type ? ` (${value.type})` : '';
  if (name && email && name !== email) return `${name} <${email}>${type}`;
  return name || email || '';
}

function truncateText(value, limit) {
  const text = String(value || '').replace(/\s+/g, ' ').trim();
  return text.length > limit ? `${text.slice(0, limit - 3)}...` : text;
}

function artifactGroups(research) {
  if (Array.isArray(research._artifact_groups)) return research._artifact_groups;
  const artifacts = research.artifacts || {};
  const labels = {
    source_log: 'Source Log',
    comprehensive_profile: 'Comprehensive Profile',
    executive_one_pager: 'Executive One-Pager',
    scorecard: 'Scorecard',
    outreach_kit: 'Outreach Kit',
    stakeholder_profiles: 'Stakeholder Profiles',
    champion_persona_targets: 'Champion/Persona Targets',
    oci_buying_objection_prep: 'OCI Buying Objection Prep',
    research_pack: 'Research Pack'
  };
  const groups = new Map();
  for (const [key, filename] of Object.entries(artifacts)) {
    const match = key.match(/(.+)_(docx|pdf)$/);
    if (!match) continue;
    const group = groups.get(match[1]) || { key: match[1], label: labels[match[1]] || titleize(match[1]) };
    group[match[2]] = filename;
    groups.set(match[1], group);
  }
  return [...groups.values()];
}

function summarizeResearch(research, fallbackSlug) {
  const summary = research._summary || {};
  const score = summary.score || research.scorecard?.score || research.scorecard?.total_score || '';
  return {
    accountName: summary.account_name || research.account_name || fallbackSlug,
    sourceFolder: summary.source_folder || research.source_folder || fallbackSlug,
    score,
    disposition: summary.disposition || research.scorecard?.disposition || '',
    topWedge: summary.top_wedge || research.scorecard?.top_wedge || extractTopWedge(research) || research.oci_pursuit_hypotheses?.[0]?.motion || '',
    buyerIntent: summary.buyer_intent || research.business_overview?.sales_navigator_context?.buyer_intent_visible || ''
  };
}

function extractTopWedge(research) {
  const raw = String(research.scorecard?.raw || '');
  const rawMatch = raw.match(/Top wedge:\s*([^\n]+)/i);
  if (rawMatch) return rawMatch[1].trim();
  const hypothesis = Array.isArray(research.oci_pursuit_hypotheses)
    ? research.oci_pursuit_hypotheses.find((item) => /^Top wedge from existing research:/i.test(String(item)))
    : '';
  const hypothesisMatch = String(hypothesis || '').match(/^Top wedge from existing research:\s*(.+)$/i);
  return hypothesisMatch ? hypothesisMatch[1].trim() : '';
}

function block(title, body) {
  return `<article class="block"><h3>${esc(title)}</h3>${body}</article>`;
}

function value(item) {
  if (Array.isArray(item)) return list(item);
  if (item && typeof item === 'object') return objectView(item);
  return item ? `<div class="prose">${esc(item)}</div>` : '<p class="muted">Not found.</p>';
}

function list(items) {
  if (!Array.isArray(items)) return value(items);
  if (!items.length) return '<p class="muted">Not found.</p>';
  return `<ul class="clean">${items.map((item) => `<li>${item && typeof item === 'object' ? objectView(item) : esc(item)}</li>`).join('')}</ul>`;
}

function objectView(obj, omit = []) {
  const entries = Object.entries(obj || {}).filter(([key]) => !key.startsWith('_') && !omit.includes(key));
  if (!entries.length) return '<p class="muted">Not found.</p>';
  return `<dl class="kv">${entries.map(([key, item]) => `<dt>${esc(titleize(key))}</dt><dd>${value(item)}</dd>`).join('')}</dl>`;
}

function fileUrl(relativePath) {
  return `/files/${relativePath.split('/').map(encodeURIComponent).join('/')}?root=${encodeURIComponent(state.root)}`;
}

function toLocalInput(value) {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  const pad = (number) => String(number).padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

function fromLocalInput(value) {
  return value ? new Date(value).toISOString() : '';
}

function formatDate(value) {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  return date.toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' });
}

function titleize(key) {
  return String(key).replaceAll('_', ' ').replace(/\b\w/g, (char) => char.toUpperCase());
}

function badgeClass(value) {
  const text = String(value || '').toLowerCase();
  if (text.includes('go')) return 'go';
  if (text.includes('watch')) return 'watch';
  if (text.includes('hold')) return 'hold';
  return '';
}

function showEmpty(message) {
  els.detailView.classList.add('hidden');
  els.emptyState.classList.remove('hidden');
  els.emptyState.innerHTML = `<h2>Opportunity Workbench</h2><p>${esc(message)}</p>`;
}

function showToast(message) {
  const existing = document.querySelector('.toast');
  if (existing) existing.remove();
  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.textContent = message;
  document.body.append(toast);
  setTimeout(() => toast.remove(), 2600);
}

function defaultRoot() {
  const path = window.location.pathname;
  return path ? 'Kellin' : '';
}

function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]));
}

function escAttr(value) {
  return esc(value).replace(/`/g, '&#96;');
}
