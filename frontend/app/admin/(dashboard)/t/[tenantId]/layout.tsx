"use client";

import { useParams, useRouter } from "next/navigation";
import * as React from "react";

import { useAdmin } from "@/components/admin/admin-context";

export default function TenantScopeLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const params = useParams();
  const router = useRouter();
  const { me, loading } = useAdmin();
  const tenantId = Number(params.tenantId);

  React.useEffect(() => {
    if (loading || !me || Number.isNaN(tenantId)) return;
    if (me.role !== "super_admin" && me.tenant_id !== tenantId) {
      router.replace("/admin");
    }
  }, [me, loading, tenantId, router]);

  if (!Number.isNaN(tenantId) && !loading && me && me.role !== "super_admin" && me.tenant_id !== tenantId) {
    return (
      <p className="text-sm text-neutral-500">You do not have access to this tenant.</p>
    );
  }

  return children;
}
