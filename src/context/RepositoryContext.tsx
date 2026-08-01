import {
  createContext,
  useContext,
  useState,
  type ReactNode,
} from "react";

interface Repository {
  owner: string;
  repo: string;
  name: string;
  description: string;
  stars: number;
  forks: number;
  language: string;
  branch: string;
}

interface RepositoryContextType {
  repository: Repository | null;
  setRepository: (repository: Repository | null) => void;
}

const RepositoryContext = createContext<RepositoryContextType | undefined>(
  undefined
);

export function RepositoryProvider({
  children,
}: {
  children: ReactNode;
}) {
  const [repository, setRepository] =
    useState<Repository | null>(null);

  return (
    <RepositoryContext.Provider
      value={{ repository, setRepository }}
    >
      {children}
    </RepositoryContext.Provider>
  );
}

export function useRepository() {
  const context = useContext(RepositoryContext);

  if (!context) {
    throw new Error(
      "useRepository must be used inside RepositoryProvider"
    );
  }

  return context;
}