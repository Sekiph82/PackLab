import { createHash } from "node:crypto";
import { lstat, readFile, rename, unlink, writeFile } from "node:fs/promises";
import { isAbsolute, relative, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

const stages = ["SPEC", "BUILD", "VERIFY", "LOCAL_COMPLETE", "BLOCKED"];
const taskPattern = /^PL-\d{4}$/;
const digestPattern = /^[0-9a-f]{64}$/i;

function validateEvidence(reference, name) {
  if (!reference || typeof reference.path !== "string" || !reference.path.trim() || !digestPattern.test(reference.sha256 ?? "")) {
    throw new Error(`${name} requires a repository-relative evidence path and SHA-256.`);
  }
  if (isAbsolute(reference.path) || reference.path.split(/[\\/]/).some((part) => part === ".." || part === ".")) {
    throw new Error(`${name} evidence path must stay inside PackLab.`);
  }
}

export function validateJobState(job) {
  if (!job || typeof job !== "object" || Array.isArray(job)) throw new Error("Job metadata must be an object.");
  if (!taskPattern.test(job.taskId ?? "")) throw new Error("Job taskId must be a canonical PL-#### ID.");
  if (typeof job.title !== "string" || !job.title.trim()) throw new Error("Job title is required.");
  if (!stages.includes(job.stage)) throw new Error("Job stage is invalid.");
  if (typeof job.updatedAt !== "string" || Number.isNaN(Date.parse(job.updatedAt))) throw new Error("updatedAt must be a valid timestamp.");
  if (job.validationEvidence != null) validateEvidence(job.validationEvidence, "Validation");
  if (job.stage === "VERIFY" && !job.validationEvidence) throw new Error("VERIFY requires recorded local validation evidence.");
  if (job.stage === "LOCAL_COMPLETE") {
    if (job.validationEvidence?.result !== "passed") throw new Error("LOCAL_COMPLETE requires passing local validation evidence.");
    validateEvidence(job.logEvidence, "Codex log");
  }
  if (job.stage === "BLOCKED" && (typeof job.blockedReason !== "string" || !job.blockedReason.trim())) {
    throw new Error("BLOCKED requires a specific reason.");
  }
  if (job.hostedVerification === true || job.independentReview === "pass" || job.releaseReady === true) {
    throw new Error("Local job metadata cannot claim hosted verification, independent review, or release readiness.");
  }
  return job;
}

export function transitionJob(job, stage, evidence = {}, now = new Date()) {
  validateJobState(job);
  if (!stages.includes(stage)) throw new Error(`Unknown job stage ${stage}.`);
  if (stage === "BLOCKED") {
    if (!evidence.blockedReason?.trim()) throw new Error("BLOCKED requires --reason.");
  } else if (job.stage === "BLOCKED") {
    if (stage !== "BUILD" || !evidence.resumeReason?.trim()) throw new Error("A blocked job resumes only to BUILD with an explicit environment/state change.");
  } else {
    const order = { SPEC: 0, BUILD: 1, VERIFY: 2, LOCAL_COMPLETE: 3 };
    if (order[stage] !== order[job.stage] + 1) throw new Error(`Job stage must advance one step from ${job.stage}.`);
  }
  const next = { ...job, ...evidence, stage, updatedAt: now.toISOString() };
  delete next.resumeReason;
  if (job.stage === "BLOCKED" && stage === "BUILD") delete next.blockedReason;
  return validateJobState(next);
}

export async function evidenceReference(root, relativePath, result = undefined) {
  if (typeof relativePath !== "string" || isAbsolute(relativePath)) throw new Error("Evidence path must be relative to PackLab.");
  const absolute = resolve(root, relativePath);
  const fromRoot = relative(root, absolute);
  if (!fromRoot || fromRoot === ".." || fromRoot.startsWith(`..${sep}`)) throw new Error("Evidence path escapes PackLab.");
  const info = await lstat(absolute);
  if (info.isSymbolicLink() || !info.isFile()) throw new Error("Evidence must be a regular PackLab file.");
  const reference = { path: fromRoot.split(sep).join("/"), sha256: createHash("sha256").update(await readFile(absolute)).digest("hex") };
  if (result) reference.result = result;
  return reference;
}

async function run() {
  const args = process.argv.slice(2);
  const value = (name) => { const index = args.indexOf(name); return index < 0 ? null : args[index + 1] ?? null; };
  const taskId = value("--task");
  if (!taskPattern.test(taskId ?? "")) throw new Error("Provide --task PL-####.");
  const root = resolve(fileURLToPath(new URL("../..", import.meta.url)));
  const path = resolve(root, "project-control/codex/jobs", taskId, "job.json");
  const allowed = resolve(root, "project-control/codex/jobs") + sep;
  if (!path.startsWith(allowed)) throw new Error("Job path escapes PackLab jobs directory.");
  const info = await lstat(path);
  if (info.isSymbolicLink() || !info.isFile()) throw new Error("Job metadata must be a regular file.");
  const job = validateJobState(JSON.parse(await readFile(path, "utf8")));
  const stage = value("--stage");
  if (!stage) throw new Error("Use --stage STAGE.");
  const evidence = {};
  if (value("--reason")) evidence.blockedReason = value("--reason");
  if (value("--resume-reason")) evidence.resumeReason = value("--resume-reason");
  if (value("--validation-evidence")) evidence.validationEvidence = await evidenceReference(root, value("--validation-evidence"), "passed");
  if (value("--log-evidence")) evidence.logEvidence = await evidenceReference(root, value("--log-evidence"));
  const updated = transitionJob(job, stage, evidence);
  const temporary = `${path}.tmp`;
  await writeFile(temporary, `${JSON.stringify(updated, null, 2)}\n`, { encoding: "utf8", flag: "wx" });
  try { await rename(temporary, path); } catch (error) { await unlink(temporary).catch(() => {}); throw error; }
  console.log(`Updated ${taskId}: ${updated.stage} (${updated.updatedAt}).`);
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try { await run(); } catch (error) { console.error(`PackLab job update refused: ${error.message}`); process.exitCode = 1; }
}
