"use client";

import { useRouter } from "next/navigation";
import * as React from "react";

import { getStoredToken } from "@/lib/api";

import { AdminProvider } from "./admin-context";

export function RequireAuth({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [ready, setReady] = React.useState(false);

  React.useEffect(() => {
    const t = getStoredToken();
    if (!t) {
      router.replace("/admin/login");
      return;
    }
    setReady(true);
  }, [router]);

  if (!ready) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-neutral-50 text-sm text-neutral-500">
        Loading session…
      </div>
    );
  }

  return <AdminProvider>{children}</AdminProvider>;
}
