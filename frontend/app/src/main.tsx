import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "@fontsource-variable/fraunces";
import "@fontsource-variable/hanken-grotesk";
import "./estilos.css";
import "./movil.css";
import "./tactil.css";
import App from "./App";

createRoot(document.getElementById("raiz")!).render(<StrictMode><App /></StrictMode>);
