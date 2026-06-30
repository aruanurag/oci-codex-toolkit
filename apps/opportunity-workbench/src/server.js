import http from 'node:http';
import { execFile } from 'node:child_process';
import { promises as fs } from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { promisify } from 'node:util';
import {
  bootstrapTasks,
  getAccount,
  listReps,
  resolveFile,
  saveNotes,
  saveCommunications,
  saveRep,
  saveTeam,
  saveTasks,
  scanWorkspace
} from './workbench.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const APP_ROOT = path.resolve(__dirname, '..');
const PUBLIC_ROOT = path.join(APP_ROOT, 'public');
const PORT = Number(process.env.PORT || 4177);
const execFileAsync = promisify(execFile);

export function createServer() {
  return http.createServer(async (req, res) => {
    try {
      await route(req, res);
    } catch (error) {
      sendJson(res, error.statusCode || 500, {
        error: error.message || 'Internal server error'
      });
    }
  });
}

async function route(req, res) {
  const url = new URL(req.url, `http://${req.headers.host || 'localhost'}`);
  const method = req.method || 'GET';

  if (url.pathname === '/api/reps') {
    if (method === 'GET') {
      return sendJson(res, 200, await listReps());
    }
    if (method === 'POST') {
      const body = await readBody(req);
      return sendJson(res, 200, await saveRep(body.rep));
    }
  }

  if (method === 'POST' && url.pathname === '/api/select-folder') {
    return sendJson(res, 200, await selectFolder());
  }

  if (method === 'GET' && url.pathname === '/api/workspaces') {
    return sendJson(res, 200, await scanWorkspace(url.searchParams.get('root')));
  }

  const accountMatch = url.pathname.match(/^\/api\/accounts\/([^/]+)(?:\/(notes|tasks|tasks\/bootstrap|communications|team))?$/);
  if (accountMatch) {
    const slug = decodeURIComponent(accountMatch[1]);
    const action = accountMatch[2] || '';
    const root = url.searchParams.get('root');
    if (method === 'GET' && !action) {
      return sendJson(res, 200, await getAccount(root, slug));
    }
    if (method === 'PUT' && action === 'notes') {
      const body = await readBody(req);
      return sendJson(res, 200, await saveNotes(root, slug, body.notes));
    }
    if (method === 'PUT' && action === 'tasks') {
      const body = await readBody(req);
      return sendJson(res, 200, await saveTasks(root, slug, body.tasks));
    }
    if (method === 'PUT' && action === 'communications') {
      const body = await readBody(req);
      return sendJson(res, 200, await saveCommunications(root, slug, body.communications));
    }
    if (method === 'PUT' && action === 'team') {
      const body = await readBody(req);
      return sendJson(res, 200, await saveTeam(root, slug, body.team));
    }
    if (method === 'POST' && action === 'tasks/bootstrap') {
      const body = await readBody(req);
      return sendJson(res, 200, await bootstrapTasks(root, slug, Boolean(body.force)));
    }
  }

  if (method === 'GET' && url.pathname.startsWith('/files/')) {
    const root = url.searchParams.get('root');
    const relativePath = decodeURIComponent(url.pathname.slice('/files/'.length));
    const filePath = await resolveFile(root, relativePath);
    return sendFile(res, filePath);
  }

  if (method === 'GET') {
    return sendStatic(res, url.pathname);
  }

  sendJson(res, 404, { error: 'Not found' });
}

async function selectFolder() {
  if (process.platform === 'darwin') {
    const script = [
      'set selectedFolder to choose folder with prompt "Select Opportunity Coach research folder"',
      'POSIX path of selectedFolder'
    ].join('\n');
    const { stdout } = await execFileAsync('osascript', ['-e', script], { timeout: 120000 });
    return { path: stdout.trim() };
  }

  if (process.platform === 'win32') {
    const script = [
      'Add-Type -AssemblyName System.Windows.Forms',
      '$dialog = New-Object System.Windows.Forms.FolderBrowserDialog',
      '$dialog.Description = "Select Opportunity Coach research folder"',
      '$dialog.ShowNewFolderButton = $false',
      'if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { $dialog.SelectedPath }'
    ].join('; ');
    const { stdout } = await execFileAsync('powershell.exe', ['-NoProfile', '-STA', '-Command', script], { timeout: 120000 });
    return { path: stdout.trim() };
  }

  for (const command of ['zenity', 'kdialog']) {
    try {
      if (command === 'zenity') {
        const { stdout } = await execFileAsync(command, ['--file-selection', '--directory', '--title=Select Opportunity Coach research folder'], { timeout: 120000 });
        return { path: stdout.trim() };
      }
      const { stdout } = await execFileAsync(command, ['--getexistingdirectory', os.homedir(), 'Select Opportunity Coach research folder'], { timeout: 120000 });
      return { path: stdout.trim() };
    } catch {
      // Try the next installed folder picker.
    }
  }

  const error = new Error('No native folder picker is available on this system. Enter the folder path manually.');
  error.statusCode = 501;
  throw error;
}

async function readBody(req) {
  let raw = '';
  for await (const chunk of req) raw += chunk;
  if (!raw) return {};
  try {
    return JSON.parse(raw);
  } catch {
    const error = new Error('request body must be JSON');
    error.statusCode = 400;
    throw error;
  }
}

async function sendStatic(res, requestPath) {
  const cleanPath = requestPath === '/' ? '/index.html' : requestPath;
  const filePath = safeJoin(PUBLIC_ROOT, cleanPath);
  try {
    await sendFile(res, filePath);
  } catch (error) {
    if (error.code === 'ENOENT') {
      await sendFile(res, path.join(PUBLIC_ROOT, 'index.html'));
      return;
    }
    throw error;
  }
}

async function sendFile(res, filePath) {
  const stat = await fs.stat(filePath);
  if (!stat.isFile()) {
    const error = new Error('Not found');
    error.statusCode = 404;
    throw error;
  }
  res.writeHead(200, {
    'Content-Type': contentType(filePath),
    'Content-Length': stat.size,
    'Cache-Control': 'no-store'
  });
  const handle = await fs.open(filePath, 'r');
  try {
    for await (const chunk of handle.readableWebStream()) {
      res.write(Buffer.from(chunk));
    }
    res.end();
  } finally {
    await handle.close().catch(() => {});
  }
}

function safeJoin(root, requestPath) {
  const target = path.resolve(root, `.${decodeURIComponent(requestPath)}`);
  const relative = path.relative(root, target);
  if (relative.startsWith('..') || path.isAbsolute(relative)) {
    const error = new Error('path escapes static root');
    error.statusCode = 400;
    throw error;
  }
  return target;
}

function sendJson(res, statusCode, body) {
  const payload = JSON.stringify(body);
  res.writeHead(statusCode, {
    'Content-Type': 'application/json; charset=utf-8',
    'Content-Length': Buffer.byteLength(payload),
    'Cache-Control': 'no-store'
  });
  res.end(payload);
}

function contentType(filePath) {
  const ext = path.extname(filePath).toLowerCase();
  if (ext === '.html') return 'text/html; charset=utf-8';
  if (ext === '.css') return 'text/css; charset=utf-8';
  if (ext === '.js') return 'text/javascript; charset=utf-8';
  if (ext === '.json') return 'application/json; charset=utf-8';
  if (ext === '.pdf') return 'application/pdf';
  if (ext === '.docx') return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';
  return 'application/octet-stream';
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  createServer().listen(PORT, () => {
    console.log(`Opportunity Workbench running at http://localhost:${PORT}`);
  });
}
