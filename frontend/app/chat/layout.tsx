export default function ChatLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <div className="flex min-h-[100dvh] flex-col bg-neutral-100">
      <div className="flex min-h-0 flex-1 flex-col">{children}</div>
    </div>
  );
}
