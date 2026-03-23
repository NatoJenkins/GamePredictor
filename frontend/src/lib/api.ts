import type {
  WeekPredictionsResponse,
  PredictionHistoryResponse,
  ModelInfoResponse,
  ExperimentResponse,
  SpreadWeekResponse,
  SpreadHistoryResponse,
} from "@/lib/types";

const API_BASE = import.meta.env.VITE_API_URL ?? "";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }

  /** True when the server is up but has no model/data yet (503, 404). */
  get isNotReady() {
    return this.status === 503 || this.status === 404;
  }
}

async function apiFetch<T>(path: string): Promise<T> {
  const res = await fetch(API_BASE + path);
  if (!res.ok) {
    throw new ApiError(res.status, `API error: ${res.status} ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

export const fetchCurrentPredictions = (): Promise<WeekPredictionsResponse> =>
  apiFetch<WeekPredictionsResponse>("/api/predictions/current");

export const fetchWeekPredictions = (
  week: number,
  season?: number,
): Promise<WeekPredictionsResponse> => {
  const params = season != null ? `?season=${season}` : "";
  return apiFetch<WeekPredictionsResponse>(
    `/api/predictions/week/${week}${params}`,
  );
};

export const fetchPredictionHistory = (
  season?: number,
  team?: string,
): Promise<PredictionHistoryResponse> => {
  const params = new URLSearchParams();
  if (season != null) params.set("season", String(season));
  if (team) params.set("team", team);
  const qs = params.toString();
  return apiFetch<PredictionHistoryResponse>(
    `/api/predictions/history${qs ? `?${qs}` : ""}`,
  );
};

export const fetchModelInfo = (): Promise<ModelInfoResponse> =>
  apiFetch<ModelInfoResponse>("/api/model/info");

export const fetchExperiments = (): Promise<ExperimentResponse[]> =>
  apiFetch<ExperimentResponse[]>("/api/experiments");

export const fetchSpreadPredictions = (
  season: number,
  week: number,
): Promise<SpreadWeekResponse> =>
  apiFetch<SpreadWeekResponse>(
    `/api/predictions/spreads/week/${season}/${week}`,
  );

export const fetchSpreadHistory = (
  season?: number,
): Promise<SpreadHistoryResponse> => {
  const params = season != null ? `?season=${season}` : "";
  return apiFetch<SpreadHistoryResponse>(
    `/api/predictions/spreads/history${params}`,
  );
};
