import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";
import { Inicio } from "./screens/Inicio";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <Inicio />
  </StrictMode>,
);
