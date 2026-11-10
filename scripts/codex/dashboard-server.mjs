import { createReadStream } from "node:fs";
import { appendFile, lstat, readFile, readdir, realpath } from "node:fs/promises";
import { createServer } from "node:http";
import { dirname, isAbsolute, join, relative, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";
import { CodexAppServerClient } from "./app-server-client.mjs";
import { readProjectTaskState } from "./task-state.mjs";

const scriptDirectory = dirname(fileURLToPath(import.meta.url));
const defaultRoot = resolve(scriptDirectory, "../..");
const CACHE_MS = 2_000;
const REVIEW_KEYS = ["rules", "code", "tests"];
let answerWriteChain = Promise.resolve();

function isWithin(parent, candidate) {
  const child = relative(parent, candidate);
  return child === "" || (!child.startsWith(`..${sep}`) && child !== ".." && !isAbsolute(child));
}

function normalizePath(value) {
  return typeof value === "string" ? value.replaceAll("\\", "/").replace(/\/$/, "").toLowerCase() : "";
}

function getRoots(project) {
  return (Array.isArray(project?.roots) ? project.roots : [])
    .map((item) => typeof item === "string" ? item : item?.path)
    .filter((item) => typeof item === "string");
}

function inPackLabPath(value) {
  return normalizePath(value).split("/").includes("packlab");
}

function statusOf(thread) {
  if (typeof thread?.status === "string") return thread.status;
  if (typeof thread?.status?.type === "string") return thread.status.type;
  return thread?.archived ? "archived" : "idle";
}

function sanitizeThread(thread) {
  const title = typeof thread?.title === "string" && thread.title.trim()
    ? thread.title
    : typeof thread?.preview === "string" && thread.preview.trim() ? thread.preview : "Untitled Codex task";
  const updated = thread?.updatedAt ?? thread?.updated_at ?? thread?.recencyAt ?? thread?.recency_at ?? null;
  const updatedAt = typeof updated === "number"
    ? new Date(updated < 10_000_000_000 ? updated * 1_000 : updated).toISOString()
    : typeof updated === "string" ? updated : null;
  return {
    id: typeof thread?.id === "string" ? thread.id : "",
    title: title.slice(0, 180),
    cwd: typeof thread?.cwd === "string" ? thread.cwd : "",
    status: statusOf(thread),
    updatedAt,
    source: typeof thread?.sourceKind === "string" ? thread.sourceKind : "Codex",
    projectId: typeof thread?.projectId === "string" ? thread.projectId : null,
  };
}

export async function readWorkflowJobs(root) {
  const jobsPath = resolve(root, "project-control/codex/jobs");
  let entries;
  try { entries = await readdir(jobsPath, { withFileTypes: true }); }
  catch (error) { if (error?.code === "ENOENT") return []; throw error; }
  const canonicalRoot = await realpath(root);
  const canonicalJobs = await realpath(jobsPath);
  if (!isWithin(canonicalRoot, canonicalJobs)) return [];
  const jobs = [];
  for (const entry of entries) {
    if (!entry.isDirectory()) continue;
    try {
      const directory = join(canonicalJobs, entry.name);
      const canonicalDirectory = await realpath(directory);
      if (!isWithin(canonicalJobs, canonicalDirectory)) continue;
      const path = join(directory, "job.json");
      const canonicalFile = await realpath(path);
      if (!isWithin(canonicalDirectory, canonicalFile)) continue;
      const info = await lstat(path);
      if (info.isSymbolicLink() || !info.isFile()) continue;
      const value = JSON.parse(await readFile(canonicalFile, "utf8"));
      if (!value || typeof value !== "object" || Array.isArray(value)) continue;
      const taskId = value.taskId ?? value.task_id ?? value.id;
      const stage = value.stage ?? value.status;
      const title = value.title ?? value.task;
      if (!/^PL-\d{4}$/.test(taskId ?? "") || typeof title !== "string" || !title.trim() || typeof stage !== "string") continue;
      const reviews = Object.fromEntries(REVIEW_KEYS.map((key) => [key, ["pending", "pass", "changes"].includes(value.reviews?.[key]) ? value.reviews[key] : "not_used"]));
      jobs.push({
        taskId,
        title: title.slice(0, 240),
        stage: stage.slice(0, 40),
        updatedAt: typeof value.updatedAt === "string" ? value.updatedAt : null,
        blockedReason: typeof value.blockedReason === "string" ? value.blockedReason.slice(0, 500) : null,
        publication: typeof value.publication === "string" ? value.publication : "not_recorded",
        reviews,
      });
    } catch (error) {
      if (error?.code !== "ENOENT" && error?.code !== "ELOOP" && !(error instanceof SyntaxError)) throw error;
    }
  }
  return jobs.sort((a, b) => (b.updatedAt ?? "").localeCompare(a.updatedAt ?? ""));
}

async function readOwnerAnswers(root) {
  const path = resolve(root, "project-control/codex/owner-answers.jsonl");
  try {
    const info = await lstat(path);
    if (info.isSymbolicLink() || !info.isFile()) return [];
    return (await readFile(path, "utf8")).split(/\r?\n/).flatMap((line) => {
      if (!line || line.length > 8_500) return [];
      try {
        const value = JSON.parse(line);
        return typeof value?.questionId === "string" && typeof value?.taskId === "string" && typeof value?.answer === "string" && typeof value?.submittedAt === "string"
          ? [{ questionId: value.questionId, taskId: value.taskId, answer: value.answer.slice(0, 4_000), submittedAt: value.submittedAt }]
          : [];
      } catch { return []; }
    });
  } catch (error) { if (error?.code === "ENOENT") return []; throw error; }
}

function saveOwnerAnswer(root, payload, source) {
  const result = answerWriteChain.then(() => saveOwnerAnswerExclusive(root, payload, source));
  answerWriteChain = result.catch(() => {});
  return result;
}

async function saveOwnerAnswerExclusive(root, payload, source) {
  const question = source.state.questions.find((item) => item.id === payload.questionId && item.taskId === payload.taskId);
  if (!question) return { status: 404, error: "That PackLab question is no longer open." };
  const answers = await readOwnerAnswers(root);
  if (answers.some((item) => item.questionId === question.id && item.taskId === question.taskId)) {
    return { status: 409, error: "An answer is already recorded for that PackLab question." };
  }
  const entry = { questionId: question.id, taskId: question.taskId, answer: payload.answer, submittedAt: new Date().toISOString() };
  const path = resolve(root, "project-control/codex/owner-answers.jsonl");
  try {
    const info = await lstat(path);
    if (info.isSymbolicLink() || !info.isFile()) return { status: 400, error: "The PackLab answer inbox is not a regular file." };
  } catch (error) { if (error?.code !== "ENOENT") throw error; }
  await appendFile(path, `${JSON.stringify(entry)}\n`, { encoding: "utf8", flag: "a" });
  return { status: 201, entry };
}

async function readJsonBody(request, limit = 8_192) {
  let bytes = 0;
  const chunks = [];
  for await (const chunk of request) {
    bytes += chunk.length;
    if (bytes > limit) throw Object.assign(new Error("Request body is too large."), { status: 413 });
    chunks.push(chunk);
  }
  try { return JSON.parse(Buffer.concat(chunks).toString("utf8")); }
  catch { throw Object.assign(new Error("Request body must be valid JSON."), { status: 400 }); }
}

function safeError(error) {
  if (error?.code === -32601 || /method not found|unknown method/i.test(error?.message ?? "")) return { status: 501, message: "Read-only Codex project listing is unsupported by this App Server." };
  if (/timed out/i.test(error?.message ?? "")) return { status: 503, message: "Codex App Server did not respond in time." };
  return { status: 503, message: "PackLab dashboard data is temporarily unavailable." };
}

export function createDashboardServer({ root = defaultRoot, host = "127.0.0.1", port = 9000, clientFactory = () => new CodexAppServerClient() } = {}) {
  let client;
  let initialized = false;
  let cache;
  let loading;

  async function snapshot() {
    if (cache && Date.now() - cache.loadedAt < CACHE_MS) return cache.value;
    if (loading) return loading;
    loading = (async () => {
      try {
        const taskState = await readProjectTaskState(root);
        const jobs = await readWorkflowJobs(root);
        const answers = await readOwnerAnswers(root);
        client ??= clientFactory();
        if (!initialized) { await client.initialize(); initialized = true; }
        let projectListing = { rows: [], truncated: false };
        let projectListState = "available";
        try { projectListing = await client.listProjects(); }
        catch (error) { if (error?.code === -32601) projectListState = "unsupported"; else throw error; }
        const threadListing = await client.listThreads();
        const projects = projectListing.rows ?? [];
        const project = projects.find((item) => String(item?.name ?? "").toLowerCase() === "packlab" || getRoots(item).some(inPackLabPath));
        const projectId = typeof project?.id === "string" ? project.id : null;
        const canonicalRoot = normalizePath(await realpath(root));
        const threads = (threadListing.rows ?? []).map(sanitizeThread).filter((thread) =>
          (projectId && thread.projectId === projectId) || normalizePath(thread.cwd) === canonicalRoot || inPackLabPath(thread.cwd),
        );
        const questions = taskState.state.questions.map((question) => ({
          ...question,
          answer: answers.find((answer) => answer.questionId === question.id && answer.taskId === question.taskId) ?? null,
        }));
        const value = {
          generatedAt: new Date().toISOString(),
          repository: "Sekiph82/PackLab",
          root,
          source: "PackLab TASKS.md and read-only Codex App Server listings",
          projectListState,
          project: { id: "packlab", name: "PackLab", repository: "Sekiph82/PackLab", roots: [root] },
          task: taskState.state,
          questions,
          jobs,
          threads,
          activeThreadCount: threads.length,
          truncated: Boolean(projectListing.truncated || threadListing.truncated),
        };
        cache = { loadedAt: Date.now(), value };
        return value;
      } finally { loading = undefined; }
    })();
    return loading;
  }

  const server = createServer(async (request, response) => {
    response.setHeader("X-Content-Type-Options", "nosniff");
    response.setHeader("Referrer-Policy", "no-referrer");
    response.setHeader("X-Frame-Options", "DENY");
    response.setHeader("Cache-Control", "no-store");
    response.setHeader("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; base-uri 'none'; frame-ancestors 'none'");
    const boundPort = server.address()?.port ?? port;
    const hostHeader = request.headers.host;
    if (hostHeader && hostHeader !== `${host}:${boundPort}` && hostHeader !== `localhost:${boundPort}`) { response.writeHead(403).end("Forbidden"); return; }
    const pathname = new URL(request.url ?? "/", `http://${host}:${boundPort}`).pathname;
    if (request.method === "POST" && pathname === "/api/owner-answers") {
      if (request.headers.origin && request.headers.origin !== `http://${hostHeader}`) { response.writeHead(403).end("Forbidden"); return; }
      if (!String(request.headers["content-type"] ?? "").toLowerCase().startsWith("application/json")) { response.writeHead(415).end("Content-Type must be application/json."); return; }
      try {
        const payload = await readJsonBody(request);
        if (payload?.projectId !== "packlab" || !/^Q-[A-Z0-9.-]+$/.test(payload?.questionId ?? "") || !/^PL-\d{4}$/.test(payload?.taskId ?? "") || typeof payload?.answer !== "string" || !payload.answer.trim() || payload.answer.length > 4_000) {
          response.writeHead(400, { "Content-Type": "application/json; charset=utf-8" }).end(JSON.stringify({ error: "Provide a matching PackLab question/task and an answer of 1 to 4000 characters." }));
          return;
        }
        const taskState = await readProjectTaskState(root);
        const result = await saveOwnerAnswer(root, { ...payload, answer: payload.answer.trim() }, taskState);
        if (result.status !== 201) { response.writeHead(result.status, { "Content-Type": "application/json; charset=utf-8" }).end(JSON.stringify({ error: result.error })); return; }
        cache = undefined;
        response.writeHead(201, { "Content-Type": "application/json; charset=utf-8" }).end(JSON.stringify({ submittedAt: result.entry.submittedAt }));
      } catch (error) {
        response.writeHead(error?.status ?? 500, { "Content-Type": "application/json; charset=utf-8" }).end(JSON.stringify({ error: error?.status ? error.message : "The PackLab answer could not be saved." }));
      }
      return;
    }
    if (request.method !== "GET") { response.writeHead(405, { Allow: "GET, POST" }).end("Method not allowed"); return; }
    if (pathname === "/health") { response.writeHead(200, { "Content-Type": "application/json; charset=utf-8" }).end(JSON.stringify({ ok: true })); return; }
    if (pathname === "/api/overview") {
      try { response.writeHead(200, { "Content-Type": "application/json; charset=utf-8" }).end(JSON.stringify(await snapshot())); }
      catch (error) {
        const safe = safeError(error);
        response.writeHead(safe.status, { "Content-Type": "application/json; charset=utf-8" }).end(JSON.stringify({ error: safe.message, generatedAt: new Date().toISOString() }));
        const failed = client;
        client = undefined;
        initialized = false;
        try { await failed?.close(); } catch { /* Reconnect on a later refresh. */ }
      }
      return;
    }
    const assets = { "/": ["index.html", "text/html; charset=utf-8"], "/dashboard.js": ["dashboard.js", "text/javascript; charset=utf-8"], "/dashboard.css": ["dashboard.css", "text/css; charset=utf-8"] };
    const asset = assets[pathname];
    if (!asset) { response.writeHead(404).end("Not found"); return; }
    response.writeHead(200, { "Content-Type": asset[1] });
    createReadStream(resolve(scriptDirectory, "dashboard", asset[0])).pipe(response);
  });

  return {
    server,
    async listen() { await new Promise((resolveListen, reject) => { server.once("error", reject); server.listen(port, host, resolveListen); }); },
    async close() { await new Promise((resolveClose) => server.close(() => resolveClose())); await client?.close(); },
  };
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const app = createDashboardServer();
  app.server.on("error", (error) => { console.error(`PackLab dashboard could not start: ${error.message}`); process.exitCode = 1; });
  await app.listen();
  console.log("PackLab local dashboard: http://127.0.0.1:9000");
  const shutdown = async () => { await app.close(); process.exit(0); };
  process.once("SIGINT", shutdown);
  process.once("SIGTERM", shutdown);
}
