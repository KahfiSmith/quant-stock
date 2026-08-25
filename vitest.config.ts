import { fileURLToPath } from "node:url";

import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

// `act` is a development-only React API. Tests must load React's dev build,
// otherwise @testing-library/react fails with "React.act is not a function".
// The ambient shell may export NODE_ENV=production, so coerce it here.
(process.env as { NODE_ENV?: string }).NODE_ENV = "development";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    include: ["src/**/*.test.{ts,tsx}"],
    env: {
      NODE_ENV: "development",
    },
  },
});