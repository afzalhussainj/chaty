"use client";

import * as React from "react";

import { getMe } from "@/lib/admin-api";
import { getStoredToken } from "@/lib/api";
import type { AdminMe } from "@/types/admin";

const AdminContext = React.createContext<{
  me: AdminMe | null;
  loading: boolean;
  reload: () => Promise<void>;
} | null>(null);

export function AdminProvider({ children }: { children: React.ReactNode }) {
  const [me, setMe] = React.useState<AdminMe | null>(null);
  const [loading, setLoading] = React.useState(true);

  const reload = React.useCallback(async () => {
    const token = getStoredToken();
    if (!token) {
      setMe(null);
      setLoading(false);
      return;
    }
    try {
      const u = await getMe(token);
      setMe(u);
    } catch {
      setMe(null);
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    void reload();
  }, [reload]);

  return (
    <AdminContext.Provider value={{ me, loading, reload }}>
      {children}
    </AdminContext.Provider>
  );
}

export function useAdmin() {
  const ctx = React.useContext(AdminContext);
  if (!ctx) {
    throw new Error("useAdmin must be used within AdminProvider");
  }
  return ctx;
}
