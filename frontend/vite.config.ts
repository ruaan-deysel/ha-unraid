import { defineConfig } from "vitest/config";

export default defineConfig({
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
        "unraid-server-card": "src/server-card.ts",
        "unraid-storage-card": "src/storage-card.ts",
        "unraid-docker-card": "src/docker-card.ts",
        "unraid-ups-card": "src/ups-card.ts",
        "unraid-vm-card": "src/vm-card.ts",
        "unraid-dashboard-card": "src/dashboard-card.ts",
      },
      output: {
        format: "es",
        entryFileNames: "[name].js",
        chunkFileNames: "chunks/[name]-[hash].js",
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
