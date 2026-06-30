import test from 'node:test';
import assert from 'node:assert/strict';
import { promises as fs } from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {
  bootstrapTasks,
  getAccount,
  resolveFile,
  saveCommunications,
  saveNotes,
  saveTeam,
  saveTasks,
  scanWorkspace
} from '../src/workbench.js';

test('scans account folders and ignores non-account folders', async () => {
  const root = await fixture();
  const workspace = await scanWorkspace(root);

  assert.equal(workspace.accountCount, 2);
  assert.deepEqual(workspace.accounts.map((account) => account.slug).sort(), ['001-alpha', '002-beta']);
  assert.equal(workspace.accounts.find((account) => account.slug === '001-alpha').summary.accountName, 'Alpha Inc');
});

test('opening account initializes workbench files without editing research', async () => {
  const root = await fixture();
  const researchPath = path.join(root, '001-alpha', 'account-research.json');
  const before = await fs.readFile(researchPath, 'utf8');

  const account = await getAccount(root, '001-alpha');

  assert.deepEqual(account.workbench.notes, []);
  assert.deepEqual(account.workbench.tasks, []);
  assert.deepEqual(account.workbench.communications, []);
  assert.deepEqual(account.workbench.team, []);
  assert.ok(await exists(path.join(root, '001-alpha', 'workbench', 'notes.md')));
  assert.ok(await exists(path.join(root, '001-alpha', 'workbench', 'notes.json')));
  assert.ok(await exists(path.join(root, '001-alpha', 'workbench', 'tasks.json')));
  assert.ok(await exists(path.join(root, '001-alpha', 'workbench', 'communications.json')));
  assert.ok(await exists(path.join(root, '001-alpha', 'workbench', 'team.json')));
  assert.ok(await exists(path.join(root, '001-alpha', 'workbench', 'activity.json')));
  assert.equal(await fs.readFile(researchPath, 'utf8'), before);
});

test('manual task file starts empty but legacy bootstrap still deduplicates when called directly', async () => {
  const root = await fixture();
  const first = await bootstrapTasks(root, '001-alpha');
  const second = await bootstrapTasks(root, '001-alpha');
  const forced = await bootstrapTasks(root, '001-alpha', true);

  assert.equal(first.bootstrapped, true);
  assert.equal(second.bootstrapped, false);
  assert.equal(first.tasks.length, second.tasks.length);
  assert.equal(forced.bootstrapped, true);
  assert.equal(new Set(forced.tasks.map((task) => task.title.toLowerCase())).size, forced.tasks.length);
});

test('opening account clears generated Opportunity Coach tasks but keeps user tasks', async () => {
  const root = await fixture();
  const workbench = path.join(root, '001-alpha', 'workbench');
  await fs.mkdir(workbench);
  await fs.writeFile(path.join(workbench, 'tasks.json'), JSON.stringify([{
    id: 'generated-1',
    source: 'opportunity-coach',
    category: 'todo',
    title: 'Generated task',
    status: 'open'
  }, {
    id: 'manual-1',
    source: 'user',
    category: 'todo',
    title: 'Manual task',
    status: 'open'
  }], null, 2));

  const account = await getAccount(root, '001-alpha');

  assert.equal(account.workbench.tasks.length, 1);
  assert.equal(account.workbench.tasks[0].title, 'Manual task');
});

test('saves notes and task state', async () => {
  const root = await fixture();
  await getAccount(root, '001-alpha');
  await saveNotes(root, '001-alpha', [{
    id: 'note-1',
    category: 'phone-conversation',
    body: 'Call notes\n- follow up',
    takenAt: '2026-06-17T16:00:00.000Z'
  }]);

  const tasks = [{
    id: 'task-1',
    source: 'user',
    category: 'email',
    title: 'Send recap',
    recipient: 'buyer@example.com',
    subject: 'Recap and next steps',
    message: 'Thanks for the conversation.',
    status: 'done',
    dueAt: '2026-06-17T18:00:00.000Z',
    remindAt: '2026-06-17T17:00:00.000Z',
    notes: 'Use executive angle'
  }];
  await saveTasks(root, '001-alpha', tasks);
  const account = await getAccount(root, '001-alpha');

  assert.equal(account.workbench.notes.length, 1);
  assert.equal(account.workbench.notes[0].category, 'phone-conversation');
  assert.equal(account.workbench.notes[0].body, 'Call notes\n- follow up');
  assert.equal(account.workbench.tasks.length, 1);
  assert.equal(account.workbench.tasks[0].status, 'done');
  assert.equal(account.workbench.tasks[0].recipient, 'buyer@example.com');
  assert.equal(account.workbench.tasks[0].message, 'Thanks for the conversation.');
  assert.ok(account.workbench.tasks[0].completedAt);
});

test('saves timestamped communication threads', async () => {
  const root = await fixture();
  await getAccount(root, '001-alpha');

  await saveCommunications(root, '001-alpha', [{
    type: 'email',
    subject: 'DR follow-up',
    participants: ['buyer@example.com', 'anurag@example.com'],
    messages: [{
      type: 'email',
      direction: 'inbound',
      from: 'buyer@example.com',
      to: ['anurag@example.com'],
      at: '2026-06-26T12:00:00.000Z',
      preview: 'Can we meet tomorrow?'
    }, {
      type: 'email',
      direction: 'outbound',
      from: 'anurag@example.com',
      to: ['buyer@example.com'],
      at: '2026-06-26T13:00:00.000Z',
      preview: 'Yes, I will send time options.'
    }]
  }]);

  const account = await getAccount(root, '001-alpha');

  assert.equal(account.workbench.communications.length, 1);
  assert.equal(account.workbench.communications[0].subject, 'DR follow-up');
  assert.equal(account.workbench.communications[0].customerLastRepliedAt, '2026-06-26T12:00:00.000Z');
  assert.equal(account.workbench.communications[0].ownerLastRepliedAt, '2026-06-26T13:00:00.000Z');
});

test('saves editable account team members with notes', async () => {
  const root = await fixture();
  await getAccount(root, '001-alpha');

  await saveTeam(root, '001-alpha', [{
    name: 'Oracle Engineer',
    email: 'engineer@oracle.com',
    role: 'Cloud Architect',
    organization: 'oracle',
    contribution: 'Helps validate OKE architecture and DR readiness.',
    relationship: 'Technical owner for workshops',
    source: 'manual',
    notes: [{
      at: '2026-06-30T15:00:00.000Z',
      body: 'Can help review customer Kubernetes upgrade runbook.',
      source: 'manual'
    }]
  }]);

  const account = await getAccount(root, '001-alpha');

  assert.equal(account.workbench.team.length, 1);
  assert.equal(account.workbench.team[0].email, 'engineer@oracle.com');
  assert.equal(account.workbench.team[0].role, 'Cloud Architect');
  assert.equal(account.workbench.team[0].organization, 'oracle');
  assert.equal(account.workbench.team[0].notes[0].body, 'Can help review customer Kubernetes upgrade runbook.');
});

test('normalizes Outlook person objects in saved communication threads', async () => {
  const root = await fixture();
  const workbench = path.join(root, '001-alpha', 'workbench');
  await fs.mkdir(workbench);
  await fs.writeFile(path.join(workbench, 'communications.json'), JSON.stringify([{
    id: 'thread-1',
    source: 'outlook',
    threadType: 'email-thread',
    status: 'needs-reply',
    subject: 'Support case',
    participants: [
      { name: 'A Buyer', email: 'buyer@example.com', type: 'customer' },
      { name: 'Anurag Mohan', email: 'anurag@example.com', type: 'owner' }
    ],
    messages: [{
      id: 'message-1',
      direction: 'inbound',
      timestamp: '2026-06-26T12:00:00.000Z',
      from: { name: 'A Buyer', email: 'buyer@example.com' },
      subject: 'Support case',
      preview: 'Can you help?'
    }]
  }], null, 2));

  const account = await getAccount(root, '001-alpha');
  const thread = account.workbench.communications[0];

  assert.equal(thread.type, 'email');
  assert.deepEqual(thread.participants, [
    'A Buyer <buyer@example.com> (customer)',
    'Anurag Mohan <anurag@example.com> (owner)'
  ]);
  assert.equal(thread.messages[0].at, '2026-06-26T12:00:00.000Z');
  assert.equal(thread.messages[0].from, 'A Buyer <buyer@example.com>');
});

test('migrates legacy markdown notes into structured notes', async () => {
  const root = await fixture();
  const workbench = path.join(root, '001-alpha', 'workbench');
  await fs.mkdir(workbench);
  await fs.writeFile(path.join(workbench, 'notes.md'), 'Legacy note text');

  const account = await getAccount(root, '001-alpha');

  assert.equal(account.workbench.legacyNotes, 'Legacy note text');
  assert.equal(account.workbench.notes.length, 1);
  assert.equal(account.workbench.notes[0].body, 'Legacy note text');
  assert.equal(account.workbench.notes[0].category, 'other');
});

test('opening account clears legacy generated email tasks', async () => {
  const root = await fixture();
  const workbench = path.join(root, '001-alpha', 'workbench');
  await fs.mkdir(workbench);
  await fs.writeFile(path.join(workbench, 'tasks.json'), JSON.stringify([{
    id: 'email-old',
    source: 'email-task',
    category: 'email',
    title: 'Email A Buyer: Ask for discovery.',
    status: 'open',
    dueAt: '',
    remindAt: '',
    completedAt: '',
    notes: '',
    createdAt: '2026-06-17T16:00:00.000Z',
    updatedAt: '2026-06-17T16:00:00.000Z'
  }], null, 2));

  const account = await getAccount(root, '001-alpha');

  assert.deepEqual(account.workbench.tasks, []);
});

test('file resolution cannot escape workspace root', async () => {
  const root = await fixture();
  await assert.rejects(() => resolveFile(root, '../secret.txt'), /escapes workspace root/);
});

test('relative root names resolve from parent directories', async () => {
  const parent = await fs.mkdtemp(path.join(os.tmpdir(), 'opp-workbench-parent-'));
  const root = path.join(parent, 'Kellin');
  await fs.mkdir(root);
  await writeAccount(root, '001-alpha', {
    account_name: 'Alpha Inc',
    account_slug: '001-alpha',
    source_folder: '001-alpha'
  });
  const nested = path.join(parent, 'apps', 'opportunity-workbench');
  await fs.mkdir(nested, { recursive: true });
  const previous = process.cwd();
  try {
    process.chdir(nested);
    const workspace = await scanWorkspace('Kellin');
    assert.equal(workspace.accountCount, 1);
    assert.equal(workspace.root, await fs.realpath(root));
  } finally {
    process.chdir(previous);
  }
});

test('extracts top wedge from legacy scorecard raw text', async () => {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), 'opp-workbench-legacy-'));
  await writeAccount(root, '001-legacy', {
    account_name: 'Legacy Account',
    account_slug: '001-legacy',
    source_folder: '001-legacy',
    scorecard: {
      raw: 'Overall score: 82 / 100\nDisposition: Go\nTop wedge: AI/data platform benchmark\nConfidence: Medium-low',
      score: '82',
      disposition: 'Go'
    },
    artifacts: {},
    research_date: '2026-05-27',
    executive_snapshot: 'Legacy account'
  });

  const workspace = await scanWorkspace(root);

  assert.equal(workspace.accounts[0].summary.topWedge, 'AI/data platform benchmark');
});

async function fixture() {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), 'opp-workbench-'));
  await writeAccount(root, '001-alpha', {
    account_name: 'Alpha Inc',
    account_slug: '001-alpha',
    source_folder: '001-alpha',
    research_date: '2026-06-17',
    executive_snapshot: 'Alpha snapshot',
    recommended_next_move: 'Send first email',
    todo: ['Send first email', 'Prepare agenda'],
    outreach_todo: ['Draft first email'],
    discovery_todo: ['Ask for workload'],
    internal_todo: ['Verify CRM'],
    stakeholders: [
      { person: 'A Buyer', email_angle: 'Ask for discovery.' },
      { person: 'A Buyer', email_angle: 'Ask for discovery.' }
    ],
    oci_buying_objection_prep: {
      next_actions: ['Prepare agenda']
    },
    artifacts: {
      research_pack_pdf: 'account-research-pack.pdf'
    },
    _summary: {
      account_name: 'Alpha Inc',
      account_slug: '001-alpha',
      source_folder: '001-alpha',
      score: '72',
      score_sort: 72,
      disposition: 'Go',
      top_wedge: 'Database modernization',
      buyer_intent: 'not found'
    }
  });
  await writeAccount(root, '002-beta', {
    account_name: 'Beta LLC',
    account_slug: '002-beta',
    source_folder: '002-beta',
    todo: []
  });
  await fs.mkdir(path.join(root, 'not-account'));
  await fs.writeFile(path.join(root, '001-alpha', 'account-research-pack.pdf'), 'pdf');
  return root;
}

async function writeAccount(root, slug, research) {
  const dir = path.join(root, slug);
  await fs.mkdir(dir, { recursive: true });
  await fs.writeFile(path.join(dir, 'account-research.json'), `${JSON.stringify(research, null, 2)}\n`);
}

async function exists(filePath) {
  try {
    await fs.stat(filePath);
    return true;
  } catch {
    return false;
  }
}
