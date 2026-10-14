import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// Durante a migração (ADR 0021) o app novo é servido em /novo; o antigo segue em /.
const API = ["/reports", "/months", "/budgets", "/transactions", "/categories"];

export default defineConfig({
  base: "/novo/",
  plugins: [react(), tailwindcss()],
  server: { proxy: Object.fromEntries(API.map((p) => [p, "http://127.0.0.1:8000"])) },
  test: { environment: "node" },
});
