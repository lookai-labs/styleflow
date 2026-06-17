'use client';

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { getAccessToken, getUser, setAuth as saveAuth, clearAuth as removeAuth, AuthUser } from '@/lib/auth';

type AuthContextType = {
  user: AuthUser | null;
  isLoggedIn: boolean;
  login: (access: string, refresh: string, user: AuthUser) => void;
  logout: () => void;
};

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);

  useEffect(() => {
    if (getAccessToken()) setUser(getUser());
  }, []);

  const login = (access: string, refresh: string, userData: AuthUser) => {
    saveAuth(access, refresh, userData);
    setUser(userData);
  };

  const logout = () => {
    removeAuth();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, isLoggedIn: !!user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
