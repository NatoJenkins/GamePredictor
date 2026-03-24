import { NavLink } from "react-router";
import { Calendar, BarChart3, FlaskConical, History } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { useModelInfo } from "@/hooks/useModelInfo";
import { cn } from "@/lib/utils";

const navItems = [
  { to: "/", icon: Calendar, label: "This Week" },
  { to: "/accuracy", icon: BarChart3, label: "Accuracy" },
  { to: "/experiments", icon: FlaskConical, label: "Experiments" },
  { to: "/history", icon: History, label: "History" },
] as const;

function ModelStatusBar() {
  const { data, isLoading, isError } = useModelInfo();

  if (isError) return null;

  return (
    <div>
      <Separator className="bg-border" />
      <div className="p-4">
        <Card className="border-border bg-background/50">
          <CardContent className="p-3">
            {isLoading ? (
              <div className="space-y-2">
                <Skeleton className="h-3 w-20" />
                <Skeleton className="h-3 w-28" />
              </div>
            ) : data ? (
              <div className="space-y-1">
                <p className="text-xs text-muted-foreground">
                  Exp #{data.experiment_id}
                </p>
                <p className="text-xs text-muted-foreground">
                  {(data.val_accuracy_2023 * 100).toFixed(1)}% val accuracy
                </p>
              </div>
            ) : null}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export function Sidebar() {
  return (
    <>
      {/* Desktop / Tablet sidebar */}
      <aside className="fixed left-0 top-0 hidden h-screen flex-col justify-between border-r border-border bg-card md:flex md:w-[180px] lg:w-60">
        <div>
          <div className="p-6">
            <span className="text-sm font-normal text-foreground">
              NFL Predictor
            </span>
          </div>
          <nav className="flex flex-col gap-1 px-3">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === "/"}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-2 rounded-md px-3 py-2 text-xs transition-colors duration-150",
                    isActive
                      ? "bg-accent text-accent-foreground"
                      : "text-muted-foreground hover:bg-secondary",
                  )
                }
              >
                <item.icon className="h-5 w-5" />
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>
        <ModelStatusBar />
      </aside>

      {/* Mobile top nav */}
      <nav className="fixed left-0 right-0 top-0 z-50 flex h-14 items-center gap-4 border-b border-border bg-card px-4 md:hidden">
        <span className="mr-2 text-sm font-normal text-foreground">
          NFL Predictor
        </span>
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-1 rounded-md px-2 py-1 text-xs transition-colors duration-150",
                isActive
                  ? "bg-accent text-accent-foreground"
                  : "text-muted-foreground hover:bg-secondary",
              )
            }
          >
            <item.icon className="h-4 w-4" />
            {item.label}
          </NavLink>
        ))}
      </nav>
    </>
  );
}
