import { defineConfig } from "vitest/config";

function preserveLitWhitespace() {
  return {
    name: "preserve-lit-whitespace",
    generateBundle(_options: unknown, bundle: Record<string, { type: string; code?: string }>) {
      for (const file of Object.values(bundle)) {
        if (file.type === "chunk" && file.code) {
          // Replace minified `[ \t\n\f\r]` with "[ \\t\\n\\f\\r]" to eliminate literal trailing whitespace
          file.code = file.code.replace(/`\[ \t\n\\f\\r\]`/g, '"[ \\t\\n\\f\\r]"');
        }
      }
    },
  };
}

export default defineConfig({
  plugins: [preserveLitWhitespace()],
  build: {
    modulePreload: false,
    outDir: "../custom_components/unraid/frontend",
    emptyOutDir: true,
    target: "es2022",
    minify: true,
    sourcemap: false,
    reportCompressedSize: false,
    rollupOptions: {
      input: {
        "unraid-cards": "src/index.ts",
      },
      output: {
        format: "es",
        entryFileNames: "[name].js",
        chunkFileNames: "[name]-[hash].js",
        codeSplitting: false,
      },
    },
  },
  test: {
    environment: "jsdom",
    setupFiles: ["test/setup.ts"],
    include: ["test/**/*.test.ts"],
    coverage: {
      provider: "v8",
      include: ["src/**/*.ts"],
      exclude: ["src/index.ts"],
      thresholds: { lines: 80 },
      reporter: ["text-summary"],
    },
  },
});
