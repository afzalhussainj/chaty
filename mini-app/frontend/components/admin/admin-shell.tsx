"use client";

import {
  BookOpen,
  Bot,
  ChevronDown,
  Cog,
  FileSearch,
  FolderTree,
  LayoutDashboard,
  ListChecks,
  LogOut,
  Play,
  ScrollText,
  Search,
  Users,
} from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import * as React from "react";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Separator } from "@/components/ui/separator";
import { listTenants } from "@/lib/admin-api";
import { getStoredToken, setStoredToken } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { Tenant } from "@/types/admin";

import { useAdmin } from "./admin-context";

function NavLink({
  href,
  active,
  children,
}: {
  href: string;
  active: boolean;
  children: React.ReactNode;
}) {
  return (
    <Link
      href={href}
      className={cn(
        "flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors",
        active
          ? "bg-neutral-200 text-neutral-950"
          : "text-neutral-600 hover:bg-neutral-100 hover:text-neutral-900",
      )}
    >
      {children}
    </Link>
  );
}

export function AdminShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { me, loading } = useAdmin();
  const [tenants, setTenants] = React.useState<Tenant[]>([]);

  React.useEffect(() => {
    const token = getStoredToken();
    if (!token || !me || me.role !== "super_admin") return;
    void (async () => {
      try {
        setTenants(await listTenants(token));
      } catch {
        setTenants([]);
      }
    })();
  }, [me]);

  const tenantMatch = pathname?.match(/^\/admin\/t\/(\d+)/);
  const activeTenantId = tenantMatch ? Number(tenantMatch[1]) : null;

  const tenantBase = activeTenantId ? `/admin/t/${activeTenantId}` : null;

  function logout() {
    setStoredToken(null);
    router.replace("/admin/login");
  }

  return (
    <div className="flex min-h-screen bg-neutral-50">
      <aside className="hidden w-56 shrink-0 flex-col border-r border-neutral-200 bg-white md:flex">
        <div className="flex h-14 items-center border-b border-neutral-200 px-4">
          <span className="text-sm font-semibold text-neutral-900">Admin</span>
        </div>
        <nav className="flex flex-1 flex-col gap-1 p-3">
          <NavLink href="/admin" active={pathname === "/admin"}>
            <LayoutDashboard className="size-4" />
            Home
          </NavLink>
          {me?.role === "super_admin" ? (
            <>
              <NavLink href="/admin/tenants" active={pathname?.startsWith("/admin/tenants") ?? false}>
                <Users className="size-4" />
                Tenants
              </NavLink>
              <NavLink href="/admin/audit" active={pathname === "/admin/audit"}>
                <ScrollText className="size-4" />
                Audit (global)
              </NavLink>
            </>
          ) : null}
          {tenantBase ? (
            <>
              <Separator className="my-2" />
              <p className="px-3 text-xs font-medium uppercase tracking-wide text-neutral-400">
                Workspace
              </p>
              <NavLink href={tenantBase} active={pathname === tenantBase}>
                <FolderTree className="size-4" />
                Overview
              </NavLink>
              <NavLink
                href={`${tenantBase}/crawl-configs`}
                active={pathname?.startsWith(`${tenantBase}/crawl-configs`) ?? false}
              >
                <Cog className="size-4" />
                Crawl configs
              </NavLink>
              <NavLink
                href={`${tenantBase}/crawl`}
                active={pathname?.startsWith(`${tenantBase}/crawl`) ?? false}
              >
                <Play className="size-4" />
                Crawl actions
              </NavLink>
              <NavLink
                href={`${tenantBase}/sources`}
                active={pathname?.startsWith(`${tenantBase}/sources`) ?? false}
              >
                <BookOpen className="size-4" />
                Sources
              </NavLink>
              <NavLink
                href={`${tenantBase}/jobs/crawl`}
                active={pathname?.startsWith(`${tenantBase}/jobs/crawl`) ?? false}
              >
                <ListChecks className="size-4" />
                Crawl jobs
              </NavLink>
              <NavLink
                href={`${tenantBase}/jobs/index`}
                active={pathname?.startsWith(`${tenantBase}/jobs/index`) ?? false}
              >
                <ListChecks className="size-4" />
                Index jobs
              </NavLink>
              <NavLink
                href={`${tenantBase}/retrieval`}
                active={pathname?.startsWith(`${tenantBase}/retrieval`) ?? false}
              >
                <Search className="size-4" />
                Retrieval test
              </NavLink>
              <NavLink
                href={`${tenantBase}/chat`}
                active={pathname?.startsWith(`${tenantBase}/chat`) ?? false}
              >
                <Bot className="size-4" />
                Chat test
              </NavLink>
              <NavLink
                href={`${tenantBase}/audit`}
                active={pathname?.startsWith(`${tenantBase}/audit`) ?? false}
              >
                <FileSearch className="size-4" />
                Tenant audit
              </NavLink>
            </>
          ) : null}
        </nav>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-14 items-center justify-between gap-4 border-b border-neutral-200 bg-white px-4">
          <div className="flex min-w-0 items-center gap-3">
            {me?.role === "super_admin" && tenants.length > 0 ? (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="outline" size="sm" className="gap-1">
                    {activeTenantId
                      ? tenants.find((t) => t.id === activeTenantId)?.name ??
                        `Tenant ${activeTenantId}`
                      : "Select tenant"}
                    <ChevronDown className="size-4 opacity-60" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="start" className="w-56">
                  <DropdownMenuLabel>Open workspace</DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  {tenants.map((t) => (
                    <DropdownMenuItem
                      key={t.id}
                      onClick={() => router.push(`/admin/t/${t.id}`)}
                    >
                      {t.name}
                    </DropdownMenuItem>
                  ))}
                </DropdownMenuContent>
              </DropdownMenu>
            ) : me?.tenant_id ? (
              <Button
                variant="outline"
                size="sm"
                onClick={() => router.push(`/admin/t/${me.tenant_id}`)}
              >
                Workspace
              </Button>
            ) : null}
            {!loading && me ? (
              <span className="truncate text-sm text-neutral-600">
                {me.email}
                <span className="ml-2 text-neutral-400">({me.role})</span>
              </span>
            ) : (
              <span className="text-sm text-neutral-400">…</span>
            )}
          </div>
          <Button variant="ghost" size="sm" onClick={logout} className="gap-2">
            <LogOut className="size-4" />
            Sign out
          </Button>
        </header>
        <main className="flex-1 overflow-auto p-6 md:p-8">
          <div className="mx-auto max-w-6xl">{children}</div>
        </main>
      </div>
    </div>
  );
}
