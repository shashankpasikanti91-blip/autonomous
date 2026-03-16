/**
 * useAuth Hook
 * Manages authentication state and operations
 */

import { useState, useEffect, useCallback, useContext, createContext } from "react";
import { User, Tenant, authService as auth } from "../services";

export interface AuthContextType {
  user: User | null;
  tenant: Tenant | null;
  isLoading: boolean;
  error: string | null;
  isAuthenticated: boolean;
  login: (email: string, password: string, tenantId?: string) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}

export function useAuthState() {
  const [user, setUser] = useState<User | null>(null);
  const [tenant, setTenant] = useState<Tenant | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const login = useCallback(
    async (email: string, password: string, tenantId?: string) => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await auth.login({ email, password, tenant_id: tenantId });
        setUser(response.user);
        setTenant(response.tenant);
      } catch (err) {
        const message = err instanceof Error ? err.message : "Login failed";
        setError(message);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  const logout = useCallback(() => {
    auth.logout();
    setUser(null);
    setTenant(null);
    setError(null);
  }, []);

  const refreshToken = useCallback(async () => {
    setIsLoading(true);
    try {
      const token = auth.getToken();
      if (!token) {
        throw new Error("No token available");
      }

      // Validate token is still valid
      const validatedUser = await auth.validateToken(token);
      setUser(validatedUser);
      setError(null);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Token refresh failed";
      setError(message);
      logout();
    } finally {
      setIsLoading(false);
    }
  }, [logout]);

  // Initialize auth state on mount
  useEffect(() => {
    const initAuth = async () => {
      const token = auth.getToken();
      if (token) {
        try {
          await refreshToken();
        } catch {
          logout();
        }
      } else {
        setIsLoading(false);
      }
    };

    initAuth();
  }, [refreshToken, logout]);

  return {
    user,
    tenant,
    isLoading,
    error,
    isAuthenticated: !!user && !!tenant,
    login,
    logout,
    refreshToken,
  };
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const authState = useAuthState();

  return (
    <AuthContext.Provider value={authState}>{children}</AuthContext.Provider>
  );
};
