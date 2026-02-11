import { useAuthContext } from "../context/AuthContext";
import type { AuthState } from "../context/AuthContext";

export type { AuthState };

export function useAuth(): AuthState {
  return useAuthContext();
}
