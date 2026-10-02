import { spawn } from "node:child_process";
import { constants } from "node:os";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname, "../..");
const port = process.env.BROWSER_TEST_PORT ?? "4173";
const host = process.env.BROWSER_TEST_HOST ?? "127.0.0.1";
const children = new Set();

function start(args, options) {
  const child = spawn(process.execPath, args, { cwd: root, ...options });
  children.add(child);
  child.once("exit", () => children.delete(child));
  return child;
}

for (const signal of ["SIGINT", "SIGTERM", "SIGHUP"]) {
  process.once(signal, () => {
    process.exitCode = 128 + constants.signals[signal];
    for (const child of children) child.kill(signal);
  });
}

const server = start(["test/browser/server.mjs"], {
  env: { ...process.env, BROWSER_TEST_HOST: host, BROWSER_TEST_PORT: port },
  stdio: ["ignore", "pipe", "inherit"],
});

function waitForServer() {
  return new Promise((resolveReady, reject) => {
    const timeout = setTimeout(
      () => reject(new Error("Browser fixture server did not start in 10s")),
      10_000
    );
    server.once("error", reject);
    server.once("exit", (code) => {
      reject(new Error(`Browser fixture server exited with code ${code}`));
    });
    server.stdout.setEncoding("utf8");
    server.stdout.on("data", (chunk) => {
      process.stdout.write(chunk);
      if (chunk.includes("Browser fixture server listening")) {
        clearTimeout(timeout);
        resolveReady();
      }
    });
  });
}

let exitCode = 1;
try {
  await waitForServer();
  const playwright = start(
    [
      "node_modules/@playwright/test/cli.js",
      "test",
      ...process.argv.slice(2),
    ],
    {
      env: {
        ...process.env,
        BROWSER_TEST_EXTERNAL_SERVER: "1",
        BROWSER_TEST_HOST: host,
        BROWSER_TEST_PORT: port,
      },
      stdio: "inherit",
    }
  );
  exitCode = await new Promise((resolveExit, reject) => {
    playwright.once("error", reject);
    playwright.once("exit", (code) => resolveExit(code ?? 1));
  });
} finally {
  server.kill();
}

process.exitCode ??= exitCode;
