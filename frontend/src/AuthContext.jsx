import { createContext, useContext, useEffect, useState } from "react";
import { api, getToken, setToken } from "./api";

const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(!!getToken());

  useEffect(() => {
    if (!getToken()) return;
    api
      .get("/api/auth/me")
      .then(setUser)
      .catch(() => setToken(null))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    const onExpired = () => setUser(null);
    window.addEventListener("auth-expired", onExpired);
    return () => window.removeEventListener("auth-expired", onExpired);
  }, []);

  const login = async (email, password) => {
    const { access_token } = await api.login(email, password);
    setToken(access_token);
    setUser(await api.get("/api/auth/me"));
  };
  const logout = () => {
    setToken(null);
    setUser(null);
  };

  const isAdmin = user?.role === "admin";
  const isManager = user?.role === "manager";
  const value = { user, loading, login, logout, isAdmin, isManager, canManage: isAdmin || isManager };
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
