import {
  createContext,
} from "react";

export interface Repository {
  owner: string;
  repo: string;
  name: string;
  description: string;
  stars: number;
  forks: number;
  language: string;
  branch: string;
}

export interface RepositoryContextType {
  repository: Repository | null;
  setRepository: (
    repository: Repository | null
  ) => void;
}

export const RepositoryContext =
  createContext<
    RepositoryContextType | undefined
  >(undefined);