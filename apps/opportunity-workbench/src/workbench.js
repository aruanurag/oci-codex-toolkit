import { promises as fs } from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';

const RESEARCH_FILE = 'account-research.json';
const WORKBENCH_DIR = 'workbench';
const NOTES_FILE = 'notes.md';
const NOTES_JSON_FILE = 'notes.json';
const TASKS_FILE = 'tasks.json';
const COMMUNICATIONS_FILE = 'communications.json';
const TEAM_FILE = 'team.json';
const ACTIVITY_FILE = 'activity.json';
const DATA_DIR = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', 'data');
const REPS_FILE = path.join(DATA_DIR, 'reps.json');

export async function listReps() {
  await fs.mkdir(DATA_DIR, { recursive: true });
  let reps = await readOptionalJson(REPS_FILE, null);
  if (!Array.isArray(reps)) {
    reps = await defaultReps();
    await writeJson(REPS_FILE, reps);
  }
  return { reps };
}

export async function saveRep(rep) {
  if (!rep || typeof rep !== 'object') throw badRequest('rep is required');
  const name = String(rep.name || '').trim();
  const rootInput = String(rep.root || '').trim();
  if (!name) throw badRequest('rep name is required');
  if (!rootInput) throw badRequest('research folder is required');
  const root = await resolveExistingDirectory(rootInput);
  const now = new Date().toISOString();
  const current = (await listReps()).reps;
  const id = String(rep.id || slugify(name) || `rep-${Date.now().toString(36)}`);
  const nextRep = {
    id,
    name,
    root,
    createdAt: current.find((item) => item.id === id)?.createdAt || now,
    updatedAt: now
  };
  const next = current.filter((item) => item.id !== id);
  next.push(nextRep);
  next.sort((a, b) => a.name.localeCompare(b.name));
  await writeJson(REPS_FILE, next);
  return { rep: nextRep, reps: next };
}

export async function scanWorkspace(rootInput) {
  const root = await resolveExistingDirectory(rootInput);
  const entries = await fs.readdir(root, { withFileTypes: true });
  const accounts = [];

  for (const entry of entries) {
    if (!entry.isDirectory()) continue;
    const accountDir = path.join(root, entry.name);
    const researchPath = path.join(accountDir, RESEARCH_FILE);
    try {
      const research = await readJson(researchPath);
      const summary = summarizeAccount(research, entry.name);
      accounts.push({
        slug: entry.name,
        path: accountDir,
        summary,
        hasWorkbench: await exists(path.join(accountDir, WORKBENCH_DIR))
      });
    } catch (error) {
      if (error.code !== 'ENOENT' && error.name !== 'SyntaxError') {
        throw error;
      }
    }
  }

  accounts.sort((a, b) => {
    const bs = Number(b.summary.scoreSort ?? -1);
    const as = Number(a.summary.scoreSort ?? -1);
    if (bs !== as) return bs - as;
    return a.summary.accountName.localeCompare(b.summary.accountName);
  });

  return {
    root,
    accountCount: accounts.length,
    accounts
  };
}

async function defaultReps() {
  const candidates = relativeDirectoryCandidates('Kellin');
  for (const candidate of candidates) {
    try {
      const root = await fs.realpath(candidate);
      const stat = await fs.stat(root);
      if (stat.isDirectory()) {
        return [{
          id: 'kellin',
          name: 'Kellin',
          root,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString()
        }];
      }
    } catch (error) {
      if (error.code !== 'ENOENT') throw error;
    }
  }
  return [];
}

export async function getAccount(rootInput, slug) {
  const root = await resolveExistingDirectory(rootInput);
  const accountDir = resolveAccountDir(root, slug);
  const research = await readJson(path.join(accountDir, RESEARCH_FILE));
  const workbench = await ensureWorkbench(accountDir, research);
  return {
    root,
    slug,
    accountDir,
    research,
    workbench
  };
}

export async function saveNotes(rootInput, slug, notes) {
  if (!Array.isArray(notes)) {
    throw badRequest('notes must be an array');
  }
  const root = await resolveExistingDirectory(rootInput);
  const accountDir = resolveAccountDir(root, slug);
  await assertAccountExists(accountDir);
  const dir = await ensureWorkbenchDir(accountDir);
  const normalized = notes.map(normalizeIncomingNote);
  await writeJson(path.join(dir, NOTES_JSON_FILE), normalized);
  await appendActivity(accountDir, { type: 'notes.saved', count: normalized.length });
  return { notes: normalized };
}

export async function saveTasks(rootInput, slug, tasks) {
  if (!Array.isArray(tasks)) {
    throw badRequest('tasks must be an array');
  }
  const root = await resolveExistingDirectory(rootInput);
  const accountDir = resolveAccountDir(root, slug);
  await assertAccountExists(accountDir);
  const normalized = tasks.map(normalizeIncomingTask);
  const dir = await ensureWorkbenchDir(accountDir);
  await writeJson(path.join(dir, TASKS_FILE), normalized);
  await appendActivity(accountDir, { type: 'tasks.saved', count: normalized.length });
  return { tasks: normalized };
}

export async function saveCommunications(rootInput, slug, threads) {
  if (!Array.isArray(threads)) {
    throw badRequest('communications must be an array');
  }
  const root = await resolveExistingDirectory(rootInput);
  const accountDir = resolveAccountDir(root, slug);
  await assertAccountExists(accountDir);
  const normalized = threads.map(normalizeIncomingCommunicationThread);
  const dir = await ensureWorkbenchDir(accountDir);
  await writeJson(path.join(dir, COMMUNICATIONS_FILE), normalized);
  await appendActivity(accountDir, { type: 'communications.saved', count: normalized.length });
  return { communications: normalized };
}

export async function saveTeam(rootInput, slug, team) {
  if (!Array.isArray(team)) {
    throw badRequest('team must be an array');
  }
  const root = await resolveExistingDirectory(rootInput);
  const accountDir = resolveAccountDir(root, slug);
  await assertAccountExists(accountDir);
  const normalized = team.map(normalizeIncomingTeamMember);
  const dir = await ensureWorkbenchDir(accountDir);
  await writeJson(path.join(dir, TEAM_FILE), normalized);
  await appendActivity(accountDir, { type: 'team.saved', count: normalized.length });
  return { team: normalized };
}

export async function bootstrapTasks(rootInput, slug, force = false) {
  const root = await resolveExistingDirectory(rootInput);
  const accountDir = resolveAccountDir(root, slug);
  const research = await readJson(path.join(accountDir, RESEARCH_FILE));
  const dir = await ensureWorkbenchDir(accountDir);
  const tasksPath = path.join(dir, TASKS_FILE);
  const current = await readOptionalJson(tasksPath, null);

  if (Array.isArray(current) && current.length && !force) {
    return { tasks: current, bootstrapped: false };
  }

  const tasks = buildInitialTasks(research);
  await writeJson(tasksPath, tasks);
  await appendActivity(accountDir, { type: 'tasks.bootstrapped', count: tasks.length });
  return { tasks, bootstrapped: true };
}

export async function resolveFile(rootInput, relativePath) {
  const root = await resolveExistingDirectory(rootInput);
  const decoded = String(relativePath || '');
  const filePath = path.resolve(root, decoded);
  const relative = path.relative(root, filePath);
  if (relative.startsWith('..') || path.isAbsolute(relative)) {
    throw badRequest('file path escapes workspace root');
  }
  const stat = await fs.stat(filePath);
  if (!stat.isFile()) {
    throw notFound('file not found');
  }
  return filePath;
}

export function buildInitialTasks(research) {
  const now = new Date().toISOString();
  const candidates = [
    ...itemsFrom(research.todo, 'todo', 'opportunity-coach'),
    ...itemsFrom(research.recommended_next_move ? [research.recommended_next_move] : [], 'follow-up', 'opportunity-coach'),
    ...itemsFrom(research.oci_buying_objection_prep?.next_actions, 'todo', 'opportunity-coach'),
    ...itemsFrom(research.outreach_todo, 'email', 'email-task'),
    ...itemsFrom(stakeholderEmailAngles(research), 'email', 'email-task'),
    ...itemsFrom(research.discovery_todo, 'discovery', 'opportunity-coach'),
    ...itemsFrom(research.internal_todo, 'internal', 'opportunity-coach')
  ];

  const seen = new Set();
  const tasks = [];
  for (const candidate of candidates) {
    const title = String(candidate.title || '').trim();
    const key = title.toLowerCase();
    if (!title || seen.has(key)) continue;
    seen.add(key);
    tasks.push({
      id: stableTaskId(candidate.category, title),
      source: candidate.source,
      category: candidate.category,
      title,
      recipient: candidate.recipient || '',
      subject: candidate.subject || '',
      message: candidate.message || '',
      status: 'open',
      dueAt: '',
      remindAt: '',
      completedAt: '',
      notes: '',
      createdAt: now,
      updatedAt: now
    });
  }
  return tasks;
}

function itemsFrom(value, category, source) {
  if (!Array.isArray(value)) return [];
  return value.map((item) => {
    if (item && typeof item === 'object' && item.title) {
      return {
        source: item.source || source,
        category: item.category || category,
        title: item.title,
        recipient: item.recipient || '',
        subject: item.subject || '',
        message: item.message || ''
      };
    }
    return {
      source,
      category,
      title: typeof item === 'object' ? JSON.stringify(item) : String(item || '')
    };
  });
}

function stakeholderEmailAngles(research) {
  if (!Array.isArray(research.stakeholders)) return [];
  return research.stakeholders
    .filter((stakeholder) => stakeholder?.person && stakeholder?.email_angle)
    .map((stakeholder) => ({
      source: 'email-task',
      category: 'email',
      title: `Email ${stakeholder.person}`,
      recipient: stakeholder.person,
      subject: accountEmailSubject(research),
      message: draftStakeholderMessage(research, stakeholder)
    }));
}

function accountEmailSubject(research) {
  const wedge = research.scorecard?.top_wedge || research._summary?.top_wedge || research.oci_pursuit_hypotheses?.[0]?.motion || 'OCI discovery';
  return `${research.account_name || 'Account'}: ${wedge}`;
}

function draftStakeholderMessage(research, stakeholder) {
  const wedge = research.scorecard?.top_wedge || research._summary?.top_wedge || research.oci_pursuit_hypotheses?.[0]?.motion || 'OCI';
  const nextMove = research.recommended_next_move || 'Would it make sense to compare notes on a focused workload discovery?';
  return [
    `Hi ${stakeholder.person || 'there'},`,
    '',
    `I wanted to reach out based on the ${wedge} opportunity area we are evaluating for ${research.account_name || 'your team'}.`,
    '',
    stakeholder.email_angle || nextMove,
    '',
    'Would you be open to a short conversation to validate the workload, success criteria, and any technical or commercial blockers?',
    '',
    'Best,'
  ].join('\n');
}

function normalizeIncomingTask(task) {
  if (!task || typeof task !== 'object') {
    throw badRequest('each task must be an object');
  }
  const now = new Date().toISOString();
  const title = String(task.title || '').trim();
  if (!title) throw badRequest('task title is required');
  const status = ['open', 'done', 'snoozed'].includes(task.status) ? task.status : 'open';
  return {
    id: String(task.id || stableTaskId(task.category || 'todo', title)),
    source: allowed(task.source, ['opportunity-coach', 'user', 'email-task', 'sync'], 'user'),
    category: allowed(task.category, ['todo', 'outreach', 'discovery', 'internal', 'email', 'follow-up'], 'todo'),
    title,
    recipient: String(task.recipient || ''),
    subject: String(task.subject || ''),
    message: String(task.message || ''),
    status,
    dueAt: String(task.dueAt || ''),
    remindAt: String(task.remindAt || ''),
    completedAt: status === 'done' ? String(task.completedAt || now) : '',
    notes: String(task.notes || ''),
    createdAt: String(task.createdAt || now),
    updatedAt: now
  };
}

function normalizeIncomingCommunicationThread(thread) {
  if (!thread || typeof thread !== 'object') {
    throw badRequest('each communication thread must be an object');
  }
  const now = new Date().toISOString();
  const subject = String(thread.subject || thread.title || '').trim();
  if (!subject) throw badRequest('communication subject is required');
  const messages = Array.isArray(thread.messages) ? thread.messages.map(normalizeIncomingCommunicationMessage) : [];
  const sortedMessages = messages.sort((a, b) => new Date(a.at) - new Date(b.at));
  return {
    id: String(thread.id || stableThreadId(subject, sortedMessages)),
    type: allowed(thread.type || thread.threadType, ['email', 'meeting', 'mixed', 'email-thread', 'meeting-conversation'], 'email').replace('-thread', '').replace('-conversation', ''),
    subject,
    participants: Array.isArray(thread.participants) ? thread.participants.map(personToString).filter(Boolean) : [],
    customerLastRepliedAt: String(thread.customerLastRepliedAt || inferCustomerLastRepliedAt(sortedMessages) || ''),
    ownerLastRepliedAt: String(thread.ownerLastRepliedAt || inferOwnerLastRepliedAt(sortedMessages) || ''),
    replyByAt: String(thread.replyByAt || ''),
    status: allowed(thread.status, ['open', 'waiting-on-customer', 'needs-reply', 'closed'], inferThreadStatus(sortedMessages)),
    source: allowed(thread.source, ['outlook', 'manual', 'sync'], 'sync'),
    externalId: String(thread.externalId || ''),
    messages: sortedMessages,
    createdAt: String(thread.createdAt || now),
    updatedAt: String(thread.updatedAt || now)
  };
}

function normalizeIncomingCommunicationMessage(message) {
  if (!message || typeof message !== 'object') {
    throw badRequest('each communication message must be an object');
  }
  const at = String(message.at || message.timestamp || '');
  if (!at) throw badRequest('communication message timestamp is required');
  return {
    id: String(message.id || stableMessageId(message)),
    type: allowed(message.type, ['email', 'meeting'], 'email'),
    direction: allowed(message.direction, ['inbound', 'outbound', 'internal'], 'internal'),
    from: personToString(message.from),
    to: Array.isArray(message.to) ? message.to.map(personToString).filter(Boolean) : [],
    at,
    subject: String(message.subject || ''),
    preview: String(message.preview || message.summary || ''),
    body: String(message.body || ''),
    externalId: String(message.externalId || ''),
    webLink: String(message.webLink || ''),
    hasAttachments: Boolean(message.hasAttachments)
  };
}

function normalizeIncomingTeamMember(member) {
  if (!member || typeof member !== 'object') {
    throw badRequest('each team member must be an object');
  }
  const now = new Date().toISOString();
  const name = String(member.name || '').trim();
  const email = String(member.email || '').trim();
  if (!name && !email) throw badRequest('team member name or email is required');
  const notes = Array.isArray(member.notes)
    ? member.notes.map(normalizeIncomingTeamNote)
    : [];
  return {
    id: String(member.id || stableTeamMemberId(email || name)),
    name,
    email,
    role: String(member.role || ''),
    organization: allowed(member.organization, ['oracle', 'customer', 'partner', 'internal', 'other'], 'oracle'),
    contribution: String(member.contribution || member.howHelping || ''),
    relationship: String(member.relationship || ''),
    source: allowed(member.source, ['manual', 'outlook', 'slack', 'notes', 'sync'], 'manual'),
    notes,
    createdAt: String(member.createdAt || now),
    updatedAt: now
  };
}

function normalizeIncomingTeamNote(note) {
  const now = new Date().toISOString();
  if (typeof note === 'string') {
    return {
      id: `team-note-${crypto.randomUUID()}`,
      at: now,
      body: note.trim(),
      source: 'manual'
    };
  }
  if (!note || typeof note !== 'object') {
    throw badRequest('each team note must be an object or string');
  }
  const body = String(note.body || '').trim();
  if (!body) throw badRequest('team note body is required');
  return {
    id: String(note.id || `team-note-${crypto.randomUUID()}`),
    at: String(note.at || note.takenAt || now),
    body,
    source: allowed(note.source, ['manual', 'outlook', 'slack', 'notes', 'sync'], 'manual')
  };
}

function personToString(value) {
  if (!value) return '';
  if (typeof value === 'string') return value.trim();
  if (typeof value !== 'object') return String(value).trim();
  const email = value.email || value.address || value.emailAddress?.address || '';
  const name = value.name || value.displayName || value.emailAddress?.name || '';
  const type = value.type ? ` (${value.type})` : '';
  if (name && email && name !== email) return `${name} <${email}>${type}`;
  return String(name || email || '').trim();
}

function normalizeIncomingNote(note) {
  if (!note || typeof note !== 'object') {
    throw badRequest('each note must be an object');
  }
  const now = new Date().toISOString();
  const body = String(note.body || '').trim();
  if (!body) throw badRequest('note body is required');
  return {
    id: String(note.id || `note-${crypto.randomUUID()}`),
    category: allowed(note.category, ['meeting-minutes', 'phone-conversation', 'field-insight', 'customer-insight', 'internal-note', 'next-step', 'other'], 'other'),
    body,
    takenAt: String(note.takenAt || now),
    createdAt: String(note.createdAt || now),
    updatedAt: now
  };
}

async function ensureWorkbench(accountDir, research) {
  const dir = await ensureWorkbenchDir(accountDir);
  const notesPath = path.join(dir, NOTES_FILE);
  const notesJsonPath = path.join(dir, NOTES_JSON_FILE);
  const tasksPath = path.join(dir, TASKS_FILE);
  const communicationsPath = path.join(dir, COMMUNICATIONS_FILE);
  const teamPath = path.join(dir, TEAM_FILE);
  const activityPath = path.join(dir, ACTIVITY_FILE);

  if (!(await exists(notesPath))) {
    await fs.writeFile(notesPath, '', 'utf8');
  }
  if (!(await exists(notesJsonPath))) {
    const legacyNotes = await fs.readFile(notesPath, 'utf8');
    const notes = legacyNotes.trim()
      ? [normalizeIncomingNote({ category: 'other', body: legacyNotes, takenAt: new Date().toISOString() })]
      : [];
    await writeJson(notesJsonPath, notes);
  }
  if (!(await exists(tasksPath))) {
    await writeJson(tasksPath, []);
  } else {
    const currentTasks = await readOptionalJson(tasksPath, []);
    const manualTasks = removeGeneratedTasks(currentTasks);
    if (manualTasks.length !== currentTasks.length) {
      await writeJson(tasksPath, manualTasks);
      await appendActivity(accountDir, { type: 'tasks.generated_cleared', removed: currentTasks.length - manualTasks.length });
    }
  }
  if (!(await exists(communicationsPath))) {
    await writeJson(communicationsPath, []);
  }
  if (!(await exists(teamPath))) {
    await writeJson(teamPath, []);
  }
  if (!(await exists(activityPath))) {
    await writeJson(activityPath, [{ type: 'workbench.initialized', at: new Date().toISOString() }]);
  }

  const tasks = await readOptionalJson(tasksPath, []);
  const communications = await readOptionalJson(communicationsPath, []);
  const team = await readOptionalJson(teamPath, []);
  const normalizedCommunications = Array.isArray(communications)
    ? communications.map(normalizeIncomingCommunicationThread)
    : [];
  if (JSON.stringify(normalizedCommunications) !== JSON.stringify(communications)) {
    await writeJson(communicationsPath, normalizedCommunications);
    await appendActivity(accountDir, { type: 'communications.normalized', count: normalizedCommunications.length });
  }

  return {
    legacyNotes: await fs.readFile(notesPath, 'utf8'),
    notes: await readOptionalJson(notesJsonPath, []),
    tasks,
    communications: normalizedCommunications,
    team: Array.isArray(team) ? team.map(normalizeIncomingTeamMember) : [],
    activity: await readOptionalJson(activityPath, [])
  };
}

function removeGeneratedTasks(tasks) {
  if (!Array.isArray(tasks)) return [];
  return tasks.filter((task) => task?.source === 'user');
}

function enrichEmailTasks(tasks, research) {
  if (!Array.isArray(tasks) || !tasks.length) return { tasks: [], changed: false };
  const generated = buildInitialTasks(research).filter((task) => task.category === 'email' || task.source === 'email-task');
  let changed = false;
  const enriched = tasks.map((task) => {
    if (task.category !== 'email' && task.source !== 'email-task') return task;
    const match = generated.find((candidate) => {
      const currentTitle = String(task.title || '').toLowerCase();
      const candidateTitle = String(candidate.title || '').toLowerCase();
      return currentTitle === candidateTitle || currentTitle.startsWith(`${candidateTitle}:`);
    });
    const next = {
      ...task,
      recipient: task.recipient || match?.recipient || recipientFromTitle(task.title) || '',
      subject: task.subject || match?.subject || accountEmailSubject(research),
      message: task.message || match?.message || genericEmailMessage(research, task.title),
    };
    if (next.recipient !== task.recipient || next.subject !== task.subject || next.message !== task.message) {
      changed = true;
    }
    return next;
  });
  return { tasks: enriched, changed };
}

function recipientFromTitle(title) {
  const text = String(title || '');
  const direct = text.match(/^Email\s+([^:]+)(?::|$)/i);
  if (direct) return direct[1].trim();
  const draft = text.match(/\bemail\s+to\s+(.+?)(?:\s+using|\s+around|\s+asking|\s+for\s+a|\.$|$)/i);
  if (draft) return draft[1].trim();
  return '';
}

function genericEmailMessage(research, title) {
  const wedge = research.scorecard?.top_wedge || research._summary?.top_wedge || research.oci_pursuit_hypotheses?.[0]?.motion || 'OCI';
  return [
    'Hi,',
    '',
    `I wanted to reach out regarding ${wedge} for ${research.account_name || 'your team'}.`,
    '',
    String(title || research.recommended_next_move || 'Would you be open to a short discovery conversation?'),
    '',
    'Best,'
  ].join('\n');
}

function inferCustomerLastRepliedAt(messages) {
  return [...messages].reverse().find((message) => message.direction === 'inbound')?.at || '';
}

function inferOwnerLastRepliedAt(messages) {
  return [...messages].reverse().find((message) => message.direction === 'outbound')?.at || '';
}

function inferThreadStatus(messages) {
  const last = [...messages].sort((a, b) => new Date(a.at) - new Date(b.at)).at(-1);
  if (!last) return 'open';
  if (last.direction === 'inbound') return 'needs-reply';
  if (last.direction === 'outbound') return 'waiting-on-customer';
  return 'open';
}

async function ensureWorkbenchDir(accountDir) {
  const dir = path.join(accountDir, WORKBENCH_DIR);
  await fs.mkdir(dir, { recursive: true });
  return dir;
}

async function appendActivity(accountDir, event) {
  const dir = await ensureWorkbenchDir(accountDir);
  const activityPath = path.join(dir, ACTIVITY_FILE);
  const activity = await readOptionalJson(activityPath, []);
  activity.push({ ...event, at: new Date().toISOString() });
  await writeJson(activityPath, activity.slice(-500));
}

function summarizeAccount(research, folderName) {
  const summary = research._summary || {};
  const score = summary.score || research.scorecard?.score || research.scorecard?.total_score || '';
  const topWedge = summary.top_wedge || research.scorecard?.top_wedge || extractTopWedge(research) || research.oci_pursuit_hypotheses?.[0]?.motion || '';
  return {
    accountName: summary.account_name || research.account_name || folderName,
    accountSlug: summary.account_slug || research.account_slug || folderName,
    sourceFolder: summary.source_folder || research.source_folder || folderName,
    score,
    scoreSort: Number(summary.score_sort ?? score ?? -1),
    disposition: summary.disposition || research.scorecard?.disposition || '',
    topWedge,
    buyerIntent: summary.buyer_intent || research.business_overview?.sales_navigator_context?.buyer_intent_visible || '',
    researchDate: research.research_date || ''
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

async function resolveExistingDirectory(rootInput) {
  if (!rootInput) throw badRequest('root is required');
  const input = String(rootInput);
  const candidates = path.isAbsolute(input) ? [input] : relativeDirectoryCandidates(input);
  for (const candidate of candidates) {
    try {
      const root = path.resolve(candidate);
      const stat = await fs.stat(root);
      if (stat.isDirectory()) return root;
    } catch (error) {
      if (error.code !== 'ENOENT') throw error;
    }
  }
  throw badRequest(`root directory not found: ${input}`);
}

function relativeDirectoryCandidates(input) {
  const candidates = [];
  let current = process.cwd();
  for (let index = 0; index < 6; index += 1) {
    candidates.push(path.join(current, input));
    const parent = path.dirname(current);
    if (parent === current) break;
    current = parent;
  }
  return candidates;
}

function resolveAccountDir(root, slug) {
  const cleanSlug = String(slug || '');
  if (!cleanSlug || cleanSlug.includes('/') || cleanSlug.includes('\\')) {
    throw badRequest('invalid account slug');
  }
  const accountDir = path.resolve(root, cleanSlug);
  const relative = path.relative(root, accountDir);
  if (relative.startsWith('..') || path.isAbsolute(relative)) {
    throw badRequest('account slug escapes workspace root');
  }
  return accountDir;
}

async function assertAccountExists(accountDir) {
  await fs.stat(path.join(accountDir, RESEARCH_FILE));
}

async function readJson(filePath) {
  return JSON.parse(await fs.readFile(filePath, 'utf8'));
}

async function readOptionalJson(filePath, fallback) {
  try {
    return await readJson(filePath);
  } catch (error) {
    if (error.code === 'ENOENT' || error.name === 'SyntaxError') return fallback;
    throw error;
  }
}

async function writeJson(filePath, value) {
  await fs.writeFile(filePath, `${JSON.stringify(value, null, 2)}\n`, 'utf8');
}

async function exists(filePath) {
  try {
    await fs.stat(filePath);
    return true;
  } catch (error) {
    if (error.code === 'ENOENT') return false;
    throw error;
  }
}

function stableTaskId(category, title) {
  return `${category}-${crypto.createHash('sha1').update(`${category}:${title}`).digest('hex').slice(0, 12)}`;
}

function stableThreadId(subject, messages) {
  const external = messages.map((message) => message.externalId).filter(Boolean).join(':');
  const basis = external || `${subject}:${messages.map((message) => `${message.at}:${message.from}`).join(':')}`;
  return `thread-${crypto.createHash('sha1').update(basis).digest('hex').slice(0, 12)}`;
}

function stableMessageId(message) {
  const basis = message.externalId || `${message.type}:${message.direction}:${message.at}:${message.from}:${message.subject || ''}`;
  return `msg-${crypto.createHash('sha1').update(basis).digest('hex').slice(0, 12)}`;
}

function stableTeamMemberId(value) {
  return `team-${crypto.createHash('sha1').update(String(value || '').toLowerCase()).digest('hex').slice(0, 12)}`;
}

function allowed(value, values, fallback) {
  return values.includes(value) ? value : fallback;
}

function slugify(value) {
  return String(value || '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 80);
}

function badRequest(message) {
  const error = new Error(message);
  error.statusCode = 400;
  return error;
}

function notFound(message) {
  const error = new Error(message);
  error.statusCode = 404;
  return error;
}
