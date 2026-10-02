import { createReadStream, statSync } from "node:fs";
import { createServer } from "node:http";
import { dirname, extname, resolve, sep } from "node:path";

const root = resolve(process.cwd());
const port = Number(process.env.BROWSER_TEST_PORT ?? 4173);
const host = process.env.BROWSER_TEST_HOST ?? "127.0.0.1";
const bundlePath = process.env.UNRAID_BUNDLE_PATH
  ? resolve(process.env.UNRAID_BUNDLE_PATH)
  : resolve(
      root,
      "../custom_components/unraid/frontend/unraid-cards.js"
    );

const contentTypes = new Map([
  [".html", "text/html; charset=utf-8"],
  [".js", "text/javascript; charset=utf-8"],
  [".json", "application/json; charset=utf-8"],
]);

const server = createServer((request, response) => {
  const pathname = new URL(request.url ?? "/", "http://127.0.0.1").pathname;
  const file =
    pathname === "/unraid-cards.js"
      ? bundlePath
      : resolve(root, `.${pathname}`);

  const allowedRoots = [root, dirname(bundlePath)];
  if (!allowedRoots.some((allowed) => file.startsWith(`${allowed}${sep}`))) {
    response.writeHead(403).end();
    return;
  }
  try {
    if (!statSync(file).isFile()) throw new Error("not a file");
    response.writeHead(200, {
      "content-type":
        contentTypes.get(extname(file)) ?? "application/octet-stream",
      "cache-control": "no-store",
    });
    createReadStream(file).pipe(response);
  } catch {
    response.writeHead(404).end();
  }
});

server.listen(port, host, () => {
  console.log(`Browser fixture server listening at http://${host}:${port}`);
});
