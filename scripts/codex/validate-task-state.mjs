import { resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { readProjectTaskState } from "./task-state.mjs";

const root = resolve(fileURLToPath(new URL("../..", import.meta.url)));
try {
  const { state } = await readProjectTaskState(root);
  console.log(`PackLab TASKS.md valid: ${state.currentTask.id} (${state.currentTaskStatus}); ${state.completedTasks}/${state.totalTasks} tasks complete.`);
  if (state.nextTaskSelectionRequired) console.log("The tracker does not name an exact successor; the queue will not infer one from checkbox order.");
} catch (error) {
  console.error(`PackLab task authority validation failed: ${error.message}`);
  process.exitCode = 1;
}
