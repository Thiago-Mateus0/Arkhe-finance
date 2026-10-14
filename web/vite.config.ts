import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// O FastAPI serve web/dist em "/" (ADR 0021); no desenvolvimento o Vite encaminha a API para ele.
const API = ["/reports", "/months", "/budgets", "/transactions", "/categories"];

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: { proxy: Object.fromEntries(API.map((p) => [p, "http://127.0.0.1:8000"])) },
  test: { environment: "node" },
});
