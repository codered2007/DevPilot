import { StrictMode } from "react";
import ReactDOM from "react-dom/client";
import { RouterProvider } from "react-router-dom";
import "./index.css";
import { router } from "./router";
import { RepositoryProvider } from "./context/RepositoryProvider";
import { WorkspaceProvider } from "./context/WorkspaceProvider";
import { WorkspaceSync } from "./context/WorkspaceSync";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <RepositoryProvider>
      <WorkspaceProvider>
        <WorkspaceSync />
        <RouterProvider router={router} />
      </WorkspaceProvider>
    </RepositoryProvider>
  </StrictMode>
);