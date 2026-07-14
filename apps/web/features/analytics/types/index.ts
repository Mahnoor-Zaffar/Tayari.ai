export interface AnalyticsDatapoint {
  period: string;
  interviews: number;
  average_score: number | null;
}

export interface AnalyticsData {
  daily: AnalyticsDatapoint[];
  weekly: AnalyticsDatapoint[];
  monthly: AnalyticsDatapoint[];
}
