import { useState } from "react";

interface InfoTooltipProps {
  text: string;
}

export function InfoTooltip({ text }: InfoTooltipProps) {
  const [open, setOpen] = useState(false);

  return (
    <span className="relative inline-block ml-1.5 align-middle">
      <button
        onClick={() => setOpen(!open)}
        className="text-muted-foreground hover:text-foreground transition-colors text-xs leading-none"
        aria-label="More info"
      >
        &#9432;
      </button>
      {open && (
        <div className="absolute z-10 left-0 top-full mt-2 w-64 p-3 rounded-lg border border-zinc-700 bg-zinc-900 text-xs text-muted-foreground shadow-lg leading-relaxed">
          {text}
        </div>
      )}
    </span>
  );
}
