export interface UserProfile {
  id: string;
  email: string;
  username: string;
  display_name: string;
  email_verified: boolean;
  created_at: string;
}

export interface DashboardStats {
  total_interviews: number;
  completed_interviews: number;
  active_interviews: number;
  average_score: number | null;
  current_streak: number;
  credits_remaining: number;
}

export interface SubscriptionInfo {
  plan: string | null;
  status: string | null;
  current_period_end: string | null;
}

export interface LatestReport {
  interview_id: string;
  overall_score: number | null;
  hire_verdict: string | null;
  created_at: string | null;
}

export interface DashboardData {
  user: UserProfile;
  stats: DashboardStats;
  subscription: SubscriptionInfo | null;
  latest_report: LatestReport | null;
}

export interface RecentInterview {
  id: string;
  type: string;
  company: string;
  status: string;
  overall_score: number | null;
  completed_at: string | null;
  created_at: string;
}

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
