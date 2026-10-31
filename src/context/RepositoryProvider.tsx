
import { useEffect, useState, type ReactNode } from "react";

import {
  RepositoryContext,
  type Repository,
} from "./RepositoryContext";

const STORAGE_PREFIX = "devpilot_repository:";

export function RepositoryProvider({
  children,
}: {
  children: ReactNode;
}) {
  const [repository, setRepositoryState] =
    useState<Repository | null>(null);
  const [userLogin, setUserLogin] = useState<string | null>(null);
  const [identityLoaded, setIdentityLoaded] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function loadUserRepository() {
      try {
        const response = await fetch(
          "http://localhost:8000/auth/me",
          { credentials: "include" }
        );

        if (!response.ok) {
          if (!cancelled) {
            setUserLogin(null);
            setRepositoryState(null);
          }
          return;
        }

        const data = await response.json();
        const login = data?.user?.login;

        if (typeof login !== "string" || !login.trim()) {
          if (!cancelled) {
            setUserLogin(null);
            setRepositoryState(null);
          }
          return;
        }

        if (cancelled) return;

        setUserLogin(login.toLowerCase());

        try {
          const stored = localStorage.getItem(
            `${STORAGE_PREFIX}${login.toLowerCase()}`
          );

          if (stored) {
            const parsed: unknown = JSON.parse(stored);

            if (
              parsed &&
              typeof parsed === "object" &&
              "owner" in parsed &&
              "repo" in parsed
            ) {
              setRepositoryState(parsed as Repository);
            } else {
              setRepositoryState(null);
            }
          } else {
            setRepositoryState(null);
          }
        } catch {
          setRepositoryState(null);
        }
      } catch (error) {
        console.error("Failed to load repository identity:", error);
        if (!cancelled) {
          setUserLogin(null);
          setRepositoryState(null);
        }
      } finally {
        if (!cancelled) setIdentityLoaded(true);
      }
    }

    void loadUserRepository();

    return () => {
      cancelled = true;
    };
  }, []);

  function setRepository(newRepository: Repository | null) {
    setRepositoryState(newRepository);

    if (!userLogin) return;

    const storageKey = `${STORAGE_PREFIX}${userLogin}`;

    if (newRepository) {
      localStorage.setItem(
        storageKey,
        JSON.stringify(newRepository)
      );
    } else {
      localStorage.removeItem(storageKey);
    }
  }

  // Avoid exposing repository state before account identity is resolved.
  if (!identityLoaded) {
    return null;
  }

  return (
    <RepositoryContext.Provider
      value={{ repository, setRepository }}
    >
      {children}
    </RepositoryContext.Provider>
  );
}
