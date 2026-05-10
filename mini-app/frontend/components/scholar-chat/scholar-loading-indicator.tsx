export function ScholarLoadingIndicator() {
  return (
    <div className="flex items-center gap-1.5 px-1 py-2">
      <div
        className="size-2 animate-bounce rounded-full bg-slate-400"
        style={{ animationDelay: "0ms" }}
      />
      <div
        className="size-2 animate-bounce rounded-full bg-slate-400"
        style={{ animationDelay: "150ms" }}
      />
      <div
        className="size-2 animate-bounce rounded-full bg-slate-400"
        style={{ animationDelay: "300ms" }}
      />
    </div>
  );
}
