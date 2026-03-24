import { BrowserRouter, Routes, Route } from "react-router";
import { QueryClientProvider } from "@tanstack/react-query";
import { queryClient } from "@/lib/query-client";
import { TooltipProvider } from "@/components/ui/tooltip";
import { AppLayout } from "@/components/layout/AppLayout";
import { ThisWeekPage } from "@/pages/ThisWeekPage";
import { AccuracyPage } from "@/pages/AccuracyPage";
import { ExperimentsPage } from "@/pages/ExperimentsPage";
import { HistoryPage } from "@/pages/HistoryPage";

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <BrowserRouter>
          <Routes>
            <Route element={<AppLayout />}>
              <Route index element={<ThisWeekPage />} />
              <Route path="accuracy" element={<AccuracyPage />} />
              <Route path="experiments" element={<ExperimentsPage />} />
              <Route path="history" element={<HistoryPage />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </TooltipProvider>
    </QueryClientProvider>
  );
}
