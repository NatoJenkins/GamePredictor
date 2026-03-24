import {
  Tooltip,
  TooltipTrigger,
  TooltipContent,
} from "@/components/ui/tooltip";

interface InfoTooltipProps {
  text: string;
}

export function InfoTooltip({ text }: InfoTooltipProps) {
  return (
    <Tooltip>
      <TooltipTrigger className="ml-1.5 align-middle text-muted-foreground hover:text-foreground transition-colors text-xs leading-none cursor-help">
        &#9432;
      </TooltipTrigger>
      <TooltipContent side="bottom" align="start" className="max-w-xs leading-relaxed">
        {text}
      </TooltipContent>
    </Tooltip>
  );
}
