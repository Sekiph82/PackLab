import test from "node:test";
import assert from "node:assert/strict";
import { EventEmitter } from "node:events";
import { PassThrough, Writable } from "node:stream";
import { CodexAppServerClient } from "./app-server-client.mjs";

function fakeSpawner(requests, responses = new Map()) {
  return () => {
    const child = new EventEmitter();
    child.stdout = new PassThrough();
    child.exitCode = null;
    child.stdin = new Writable({
      write(chunk, _encoding, callback) {
        const message = JSON.parse(chunk.toString("utf8"));
        if (message.id !== undefined) {
          requests.push(message);
          const result = responses.get(message.method) ?? (message.method === "initialize" ? {} : { data: [] });
          child.stdout.write(`${JSON.stringify({ jsonrpc: "2.0", id: message.id, result })}\n`);
        }
        callback();
      },
    });
    child.kill = () => { child.exitCode = 0; child.emit("close", 0); };
    return child;
  };
}

test("only read-only App Server listings are sent and state DB scope is explicit", async () => {
  const requests = [];
  const client = new CodexAppServerClient({ spawnProcess: fakeSpawner(requests) });
  await client.initialize();
  await client.listProjects();
  await client.listThreads();
  await client.close();
  assert.deepEqual(requests.map((item) => item.method), ["initialize", "project/list", "thread/list"]);
  assert.equal(requests[1].params.useStateDbOnly, true);
  assert.equal(requests[2].params.useStateDbOnly, true);
});

test("project listing pages are bounded and report truncation", async () => {
  const requests = [];
  const client = new CodexAppServerClient({
    spawnProcess: fakeSpawner(requests, new Map([
      ["project/list", { data: [], nextCursor: "more" }],
      ["thread/list", { data: [] }],
    ])),
  });
  await client.initialize();
  const projects = await client.listProjects();
  assert.equal(projects.truncated, true);
  assert.equal(requests.filter((item) => item.method === "project/list").length, 10);
  await client.close();
});
