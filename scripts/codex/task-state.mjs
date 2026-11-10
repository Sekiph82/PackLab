import { readFile } from "node:fs/promises";
import { resolve } from "node:path";

const taskPattern = /^- \[([ x~!])\] (?:\*\*)?(PL-\d{4})(?:\*\*)?(?: — )?(.+)$/;
const currentPattern = /^(PL-\d{4}) — (.+)$/;

export function readField(source, name) {
  const escaped = name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const matches = [...source.matchAll(new RegExp(`^- ${escaped}:\\s*(.+)$`, "gm"))];
  if (matches.length !== 1) throw new Error(`${name} must appear exactly once in TASKS.md.`);
  return matches[0][1].trim();
}

export function parseTaskRows(source) {
  const lines = source.split(/\r?\n/);
  const headings = lines.flatMap((line, index) => line === "## Tasks" ? [index] : []);
  if (headings.length !== 1) throw new Error("TASKS.md must contain exactly one canonical ## Tasks ledger.");
  const tasks = lines.flatMap((line, lineIndex) => {
    const match = line.match(taskPattern);
    if (match) {
      const title = match[3].split(/\s+\*\*Mandatory pre-read:\*\*/i, 1)[0].trim();
      return [{ marker: match[1], id: match[2], title, lineIndex }];
    }
    if (/^- \[[ x~!]\] (?:\*\*)?PL-\d{4}\b/.test(line)) throw new Error(`Malformed canonical task row: ${line}`);
    return [];
  });
  if (!tasks.length) throw new Error("The canonical task ledger is empty.");
  if (new Set(tasks.map((task) => task.id)).size !== tasks.length) throw new Error("Task IDs must be unique.");
  return tasks;
}

export function parseTaskState(source) {
  const tasks = parseTaskRows(source);
  const currentValue = readField(source, "Current Task");
  const current = currentValue.match(currentPattern);
  if (!current) throw new Error("Current Task must identify one PL task ID and exact title.");
  const statusValue = readField(source, "Current Task Status");
  const status = statusValue.split(" / ", 1)[0].trim();
  const requiredActor = readField(source, "Required Actor");
  const milestone = readField(source, "Current Milestone");
  const sprint = readField(source, "Current Sprint");
  const nextTask = readField(source, "Next Task/Action");
  if (!/^CODEX\b/.test(requiredActor)) throw new Error("Required Actor must authorize CODEX.");
  if (!milestone || !sprint || !nextTask) throw new Error("Milestone, sprint, and next action must be explicit.");
  const matches = tasks.filter((task) => task.id === current[1] && task.title === current[2]);
  if (matches.length !== 1) throw new Error(`Current Task ${current[1]} must match exactly one canonical task row.`);
  const marker = { READY: " ", IN_PROGRESS: "~", BLOCKED: "!", COMPLETE: "x" }[status];
  if (marker === undefined) throw new Error(`Unsupported Current Task Status: ${status}.`);
  if (matches[0].marker !== marker) throw new Error(`Current Task Status ${status} does not match [${matches[0].marker}] for ${current[1]}.`);
  const inProgress = tasks.filter((task) => task.marker === "~");
  if (inProgress.length > 1 || (status === "IN_PROGRESS" && (inProgress.length !== 1 || inProgress[0].id !== current[1]))) {
    throw new Error("Only the explicit Current Task may be marked in progress.");
  }
  const nextReference = nextTask.match(currentPattern);
  if (nextReference && !tasks.some((task) => task.id === nextReference[1] && task.title === nextReference[2])) {
    throw new Error(`Next Task/Action references unknown task ${nextReference[1]}.`);
  }
  const questions = parseQuestions(source, tasks);
  return {
    currentTask: { id: current[1], title: current[2] },
    currentTaskStatus: status,
    requiredActor,
    milestone,
    sprint,
    nextTask,
    nextTaskId: nextReference?.[1] === current[1] ? null : nextReference?.[1] ?? null,
    nextTaskTitle: nextReference?.[1] === current[1] ? null : nextReference?.[2] ?? null,
    nextTaskSelectionRequired: status !== "COMPLETE" && (!nextReference || nextReference[1] === current[1]),
    tasks,
    questions,
    completedTasks: tasks.filter((task) => task.marker === "x").length,
    totalTasks: tasks.length,
  };
}

export function parseQuestions(source, tasks = parseTaskRows(source)) {
  const headings = [...source.matchAll(/^## Questions for (?:Owner|Şekip)\s*$/gm)];
  if (headings.length > 1) throw new Error("TASKS.md may contain only one Questions for Owner section.");
  if (!headings.length) return [];
  const start = headings[0].index + headings[0][0].length;
  const after = source.slice(start);
  const end = after.search(/^## /m);
  const section = end < 0 ? after : after.slice(0, end);
  const canonical = new Set(tasks.map((task) => task.id));
  const questions = section.split(/\r?\n/).flatMap((line) => {
    const match = line.match(/^\s*[-*]\s+(Q-[A-Z0-9.-]+)\s*\|\s*(.+?)\s*\|\s*TASK:\s*(PL-\d{4})\s*$/);
    return match && canonical.has(match[3]) ? [{ id: match[1], question: match[2].slice(0, 1_000), taskId: match[3] }] : [];
  });
  if (new Set(questions.map((question) => question.id)).size !== questions.length) throw new Error("Owner question IDs must be unique.");
  return questions;
}

export async function readProjectTaskState(root) {
  const trackerPath = resolve(root, "TASKS.md");
  const source = await readFile(trackerPath, "utf8");
  return { source, state: parseTaskState(source), trackerPath };
}
