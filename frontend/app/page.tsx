import Link from "next/link";

export default function HomePage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col justify-center gap-8 px-6">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">University Chatbot Platform</h1>
        <p className="mt-2 text-muted-foreground text-neutral-600">
          Multi-tenant RAG over crawled university sites. Structure only — features come in later
          phases.
        </p>
      </div>
      <nav className="flex flex-col gap-3 text-sm">
        <Link className="text-blue-600 underline hover:text-blue-800" href="/admin">
          Admin
        </Link>
        <Link className="text-blue-600 underline hover:text-blue-800" href="/chat">
          Public chatbot
        </Link>
      </nav>
    </main>
  );
}
