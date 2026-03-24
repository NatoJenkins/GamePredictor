import { useState } from "react";
import { ChevronUp, ChevronDown } from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { ExperimentDetail } from "@/components/experiments/ExperimentDetail";
import type { ExperimentResponse } from "@/lib/types";

type SortField = "experiment_id" | "val_accuracy_2023";
type SortDir = "asc" | "desc";

interface ExperimentTableProps {
  experiments: ExperimentResponse[];
}

export function ExperimentTable({ experiments }: ExperimentTableProps) {
  const [sortField, setSortField] = useState<SortField>("experiment_id");
  const [sortDir, setSortDir] = useState<SortDir>("desc");
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortDir("desc");
    }
  };

  const sorted = Array.from(experiments).sort((a, b) => {
    const aVal = a[sortField];
    const bVal = b[sortField];
    const multiplier = sortDir === "asc" ? 1 : -1;
    return (aVal - bVal) * multiplier;
  });

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) return null;
    return sortDir === "asc" ? (
      <ChevronUp className="inline h-4 w-4" />
    ) : (
      <ChevronDown className="inline h-4 w-4" />
    );
  };

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead
            className="w-12 cursor-pointer"
            onClick={() => handleSort("experiment_id")}
          >
            # <SortIcon field="experiment_id" />
          </TableHead>
          <TableHead>Hypothesis</TableHead>
          <TableHead
            className="w-[100px] cursor-pointer"
            onClick={() => handleSort("val_accuracy_2023")}
          >
            2023 Val Acc <SortIcon field="val_accuracy_2023" />
          </TableHead>
          <TableHead className="w-20">2022 Val</TableHead>
          <TableHead className="w-20">2021 Val</TableHead>
          <TableHead className="w-20">Log Loss</TableHead>
          <TableHead className="w-20">Status</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {sorted.map((exp) => (
          <Collapsible
            key={exp.experiment_id}
            open={expandedId === exp.experiment_id}
            onOpenChange={(open) =>
              setExpandedId(open ? exp.experiment_id : null)
            }
          >
            <CollapsibleTrigger
              render={
                <TableRow className="hover:bg-secondary/50 cursor-pointer transition-colors" />
              }
            >
              <TableCell className="font-mono text-xs">
                {exp.experiment_id}
              </TableCell>
              <TableCell>
                <span className="truncate max-w-[300px] block">
                  {exp.hypothesis.length > 60
                    ? exp.hypothesis.slice(0, 60) + "..."
                    : exp.hypothesis}
                </span>
              </TableCell>
              <TableCell>
                {(exp.val_accuracy_2023 * 100).toFixed(1)}%
              </TableCell>
              <TableCell>
                {(exp.val_accuracy_2022 * 100).toFixed(1)}%
              </TableCell>
              <TableCell>
                {(exp.val_accuracy_2021 * 100).toFixed(1)}%
              </TableCell>
              <TableCell>{exp.log_loss.toFixed(4)}</TableCell>
              <TableCell>
                {exp.keep ? (
                  <Badge className="bg-status-success/15 text-status-success border-0">
                    Kept
                  </Badge>
                ) : (
                  <Badge className="bg-status-error/15 text-status-error border-0">
                    Reverted
                  </Badge>
                )}
              </TableCell>
            </CollapsibleTrigger>
            <CollapsibleContent
              render={<TableRow className="bg-background/50" />}
            >
              <TableCell colSpan={7} className="p-0">
                <ExperimentDetail experiment={exp} />
              </TableCell>
            </CollapsibleContent>
          </Collapsible>
        ))}
      </TableBody>
    </Table>
  );
}
