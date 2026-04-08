import { TenantChatPage } from "@/components/chat/tenant-chat-page";

export default function HomePage() {
  const slug = process.env.NEXT_PUBLIC_SITE_SLUG ?? "default";
  return (
    <main className="flex min-h-screen flex-col">
      <TenantChatPage slug={slug} />
    </main>
  );
}
