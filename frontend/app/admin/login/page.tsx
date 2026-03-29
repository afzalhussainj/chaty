"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import * as React from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { getMe, postLogin } from "@/lib/admin-api";
import { getStoredToken, setStoredToken } from "@/lib/api";

export default function AdminLoginPage() {
  const router = useRouter();
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [loading, setLoading] = React.useState(false);

  React.useEffect(() => {
    const t = getStoredToken();
    if (t) {
      void (async () => {
        try {
          const me = await getMe(t);
          if (me.role === "super_admin") router.replace("/admin");
          else if (me.tenant_id) router.replace(`/admin/t/${me.tenant_id}`);
          else router.replace("/admin");
        } catch {
          setStoredToken(null);
        }
      })();
    }
  }, [router]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      const tok = await postLogin(email, password);
      setStoredToken(tok.access_token);
      const me = await getMe(tok.access_token);
      toast.success("Signed in");
      if (me.role === "super_admin") router.replace("/admin");
      else if (me.tenant_id) router.replace(`/admin/t/${me.tenant_id}`);
      else router.replace("/admin");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Login failed";
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-neutral-50 px-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Admin sign in</CardTitle>
          <CardDescription>Use your staff credentials.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={onSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                autoComplete="username"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "Signing in…" : "Sign in"}
            </Button>
          </form>
          <p className="mt-4 text-center text-sm text-neutral-500">
            <Link href="/" className="underline hover:text-neutral-800">
              Back to site
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
