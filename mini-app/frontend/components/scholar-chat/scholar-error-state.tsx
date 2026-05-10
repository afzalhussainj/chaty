import { AlertCircle } from "lucide-react";

export function ScholarErrorState({ message }: { message?: string | null }) {
  return (
    <div className="flex flex-col items-start gap-3 rounded-lg border border-red-100 bg-red-50 p-4 text-red-700">
      <div className="flex items-center gap-2">
        <AlertCircle className="size-5 text-red-500" aria-hidden />
        <span className="font-medium">Something went wrong. Please try again.</span>
      </div>
      <p className="max-w-md text-sm text-red-600/80">
        {message?.trim() ||
          "We could not reach the service right now. Please check your internet and try again in a moment."}
      </p>
    </div>
  );
}
