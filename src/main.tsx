import { StrictMode } from "react";
import ReactDOM from "react-dom/client";
import { RouterProvider } from "react-router-dom";

import "./index.css";

import { router } from "./router";
import { RepositoryProvider } from "./context/RepositoryProvider";
ReactDOM.createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <RepositoryProvider>
      <RouterProvider router={router} />
    </RepositoryProvider>
  </StrictMode>
);