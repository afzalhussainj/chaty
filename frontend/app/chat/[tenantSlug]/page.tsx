"use client";

import { useParams } from "next/navigation";

import { TenantChatPage } from "@/components/chat/tenant-chat-page";

export default function PublicChatBySlugPage() {
  const params = useParams();
  const raw = params.tenantSlug;
  const slug = typeof raw === "string" ? raw : raw?.[0];
  if (!slug) {
    return (
      <p className="px-4 py-8 text-center text-sm text-neutral-600">
        Invalid address.
      </p>
    );
  }
  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <TenantChatPage slug={slug} />
    </div>
  );
}
