import { useContext } from "react";

import {
  RepositoryContext,
} from "./RepositoryContext";

export function useRepository() {
  const context =
    useContext(
      RepositoryContext
    );

  if (!context) {
    throw new Error(
      "useRepository must be used inside RepositoryProvider"
    );
  }

  return context;
}