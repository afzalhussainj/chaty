"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import * as React from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function ChatLandingPage() {
  const router = useRouter();
  const [slug, setSlug] = React.useState("");

  function go(e: React.FormEvent) {
    e.preventDefault();
    const s = slug.trim().toLowerCase().replace(/\s+/g, "-");
    if (!s) return;
    router.push(`/chat/${encodeURIComponent(s)}`);
  }

  return (
    <div className="mx-auto flex w-full max-w-md flex-col gap-8 px-4 py-12">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-neutral-900">
          Campus assistant
        </h1>
        <p className="mt-2 text-sm leading-relaxed text-neutral-600">
          Open your institution&apos;s assistant with the link they provided, or enter your
          campus <span className="font-medium">slug</span> (short name in the address bar).
        </p>
      </div>
      <form onSubmit={go} className="space-y-4 rounded-lg border border-neutral-200 bg-white p-4 shadow-sm">
        <div className="space-y-2">
          <Label htmlFor="slug">Campus slug</Label>
          <Input
            id="slug"
            placeholder="e.g. westfield-uni"
            value={slug}
            onChange={(e) => setSlug(e.target.value)}
            autoComplete="off"
            spellCheck={false}
          />
        </div>
        <Button type="submit" className="w-full" disabled={!slug.trim()}>
          Continue
        </Button>
      </form>
      <p className="text-center text-xs text-neutral-500">
        <Link href="/" className="underline hover:text-neutral-800">
          Back to home
        </Link>
      </p>
    </div>
  );
}
