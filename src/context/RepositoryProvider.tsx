import {
  useState,
  type ReactNode,
} from "react";

import {
  RepositoryContext,
  type Repository,
} from "./RepositoryContext";

const STORAGE_KEY = "devpilot_repository";

export function RepositoryProvider({
  children,
}: {
  children: ReactNode;
}) {
  const [repository, setRepositoryState] =
    useState<Repository | null>(() => {
      try {
        const storedRepository =
          localStorage.getItem(STORAGE_KEY);

        if (!storedRepository) {
          return null;
        }

        return JSON.parse(storedRepository);
      } catch (error) {
        console.error(
          "Failed to restore repository:",
          error
        );

        localStorage.removeItem(STORAGE_KEY);

        return null;
      }
    });

  function setRepository(
    newRepository: Repository | null
  ) {
    setRepositoryState(newRepository);

    if (newRepository) {
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify(newRepository)
      );
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
  }

  return (
    <RepositoryContext.Provider
      value={{
        repository,
        setRepository,
      }}
    >
      {children}
    </RepositoryContext.Provider>
  );
}