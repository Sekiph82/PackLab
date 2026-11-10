import { existsSync } from "node:fs";
import { lstat, mkdir, readFile, rename, rmdir, unlink, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { parseQuestions, parseTaskRows, parseTaskState, readProjectTaskState } from "./task-state.mjs";

export function claimCurrentTask(source) {
  const state = parseTaskState(source);
  if (state.currentTaskStatus === "IN_PROGRESS") return { source, changed: false, ...state.currentTask };
  if (state.currentTaskStatus !== "READY") throw new Error(`The explicit current task is ${state.currentTaskStatus}; it cannot be claimed.`);
  const task = state.tasks.find((row) => row.id === state.currentTask.id);
  const lines = source.split(/\r?\n/);
  lines[task.lineIndex] = lines[task.lineIndex].replace("[ ]", "[~]");
  const updated = lines.join("\n").replace(/^- Current Task Status: READY(?=\s*(?:\/|$))/m, (line) => line.replace("READY", "IN_PROGRESS"));
  parseTaskState(updated);
  return { source: updated, changed: true, id: task.id, title: task.title };
}

export function applyOwnerAnswers(source, answers) {
  let updated = source;
  const applied = [];
  for (const answer of answers) {
    if (!answer || typeof answer.questionId !== "string" || typeof answer.taskId !== "string" || typeof answer.answer !== "string") continue;
    if (!answer.answer.trim()) throw new Error(`Owner answer ${answer.questionId} is blank.`);
    const question = parseQuestions(updated).find((item) => item.id === answer.questionId && item.taskId === answer.taskId);
    if (!question) continue;
    if (new RegExp(`^\\s*[-*]\\s+${escapeRegExp(question.id)}\\s*\\|`, "m").test(ownerDecisionSection(updated))) continue;
    updated = appendOwnerDecision(updated, question, answer.answer);
    updated = removeOpenQuestion(updated, question.id);
    const task = parseTaskRows(updated).find((row) => row.id === question.taskId);
    if (task?.marker === "!") {
      const current = parseTaskState(updated);
      const lines = updated.split(/\r?\n/);
      lines[task.lineIndex] = lines[task.lineIndex].replace("[!]", "[ ]");
      updated = lines.join("\n");
      if (current.currentTask.id === task.id && current.currentTaskStatus === "BLOCKED") {
        updated = updated.replace(/^- Current Task Status: BLOCKED(?=\s*(?:\/|$))/m, (line) => line.replace("BLOCKED", "READY"));
      }
    }
    applied.push({ questionId: question.id, taskId: question.taskId });
  }
  parseTaskState(updated);
  return { source: updated, applied };
}

function escapeRegExp(value) { return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); }
function ownerDecisionSection(source) {
  const match = /^## Owner Decisions\s*$/m.exec(source);
  if (!match) return "";
  const rest = source.slice(match.index + match[0].length);
  const end = rest.search(/^## /m);
  return end < 0 ? rest : rest.slice(0, end);
}
function appendOwnerDecision(source, question, rawAnswer) {
  const answer = rawAnswer.replace(/[\r\n]+/g, " ").trim().slice(0, 4_000);
  if (!answer) throw new Error("Owner answer is blank.");
  const line = `- ${question.id} | TASK: ${question.taskId} | ANSWER: ${answer}`;
  const heading = /^## Owner Decisions\s*$/m.exec(source);
  return heading
    ? `${source.slice(0, heading.index + heading[0].length)}\n${line}${source.slice(heading.index + heading[0].length)}`
    : `${source.trimEnd()}\n\n## Owner Decisions\n\n${line}\n`;
}
function removeOpenQuestion(source, questionId) {
  const heading = /^## Questions for (?:Owner|Şekip)\s*$/m.exec(source);
  if (!heading) return source;
  const afterHeading = heading.index + heading[0].length;
  const rest = source.slice(afterHeading);
  const nextHeading = rest.search(/^## /m);
  const sectionEnd = nextHeading < 0 ? source.length : afterHeading + nextHeading;
  const section = source.slice(afterHeading, sectionEnd);
  const escaped = escapeRegExp(questionId);
  const nextSection = section.replace(new RegExp(`^\\s*[-*]\\s+${escaped}\\s*\\|[^\\n]*(?:\\n|$)`, "m"), "");
  return `${source.slice(0, afterHeading)}${nextSection}${source.slice(sectionEnd)}`;
}
async function readAnswerInbox(root) {
  const path = resolve(root, "project-control/codex/owner-answers.jsonl");
  try {
    const info = await lstat(path);
    if (info.isSymbolicLink() || !info.isFile()) throw new Error("Owner answer inbox must be a regular file.");
    return (await readFile(path, "utf8")).split(/\r?\n/).flatMap((line, index) => {
      if (!line) return [];
      if (line.length > 8_500) throw new Error(`Owner answer inbox line ${index + 1} exceeds the size limit.`);
      let answer;
      try { answer = JSON.parse(line); } catch { throw new Error(`Owner answer inbox line ${index + 1} is invalid JSON.`); }
      if (!answer || typeof answer.questionId !== "string" || typeof answer.taskId !== "string" || typeof answer.answer !== "string" || !answer.answer.trim()) {
        throw new Error(`Owner answer inbox line ${index + 1} is incomplete.`);
      }
      return [answer];
    });
  } catch (error) { if (error?.code === "ENOENT") return []; throw error; }
}

export async function writeTracker(root, expectedSource, source) {
  const path = resolve(root, "TASKS.md");
  const temporaryPath = resolve(root, "TASKS.md.codex-queue.tmp");
  const lockPath = resolve(root, "TASKS.md.codex-queue.lock");
  let locked = false;
  try { await mkdir(lockPath); locked = true; }
  catch (error) { if (error?.code === "EEXIST") throw new Error("Another task queue update holds the TASKS.md lock."); throw error; }
  try {
    if (existsSync(temporaryPath)) throw new Error("TASKS.md.codex-queue.tmp exists; refusing to overwrite it.");
    const info = await lstat(path);
    if (info.isSymbolicLink() || !info.isFile()) throw new Error("TASKS.md must be a regular file.");
    if (await readFile(path, "utf8") !== expectedSource) throw new Error("TASKS.md changed during queue processing.");
    await writeFile(temporaryPath, source, { encoding: "utf8", flag: "wx" });
    try {
      if (await readFile(path, "utf8") !== expectedSource) throw new Error("TASKS.md changed before queue commit.");
      await rename(temporaryPath, path);
    } catch (error) { await unlink(temporaryPath).catch(() => {}); throw error; }
  } finally { if (locked) await rmdir(lockPath).catch(() => {}); }
}

async function run() {
  const root = resolve(fileURLToPath(new URL("../..", import.meta.url)));
  const args = new Set(process.argv.slice(2));
  if (!["--check", "--claim", "--apply-answers"].some((arg) => args.has(arg))) throw new Error("Use --check, --claim, or --apply-answers.");
  const { source, state } = await readProjectTaskState(root);
  if (args.has("--apply-answers")) {
    const result = applyOwnerAnswers(source, await readAnswerInbox(root));
    if (result.applied.length) {
      await writeTracker(root, source, result.source);
      for (const item of result.applied) console.log(`Applied owner answer ${item.questionId} to ${item.taskId}.`);
    } else console.log("No unanswered matching PackLab owner decisions in the inbox.");
    return;
  }
  if (args.has("--claim")) {
    const result = claimCurrentTask(source);
    if (result.changed) await writeTracker(root, source, result.source);
    console.log(result.changed ? `Claimed ${result.id}: ${result.title}` : `Current PackLab task: ${result.id}`);
    return;
  }
  console.log(JSON.stringify({ ...state, tasks: state.tasks.map(({ marker, id, title }) => ({ marker, id, title })) }, null, 2));
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try { await run(); } catch (error) { console.error(`PackLab autonomous queue stopped safely: ${error.message}`); process.exitCode = 1; }
}
