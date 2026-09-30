"use client";

import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { analyticsApi } from "@/lib/api";
import { formatNumber, formatCurrency } from "@/lib/utils";
import {
  Users,
  AlertTriangle,
  Building2,
  MapPin,
  TrendingUp,
  TrendingDown,
  Activity,
} from "lucide-react";

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  trend?: { value: number; label: string };
  iconColor: string;
}

function StatCard({ title, value, icon, trend, iconColor }: StatCardProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
        <div className={iconColor}>{icon}</div>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {trend && (
          <p className="text-xs text-muted-foreground flex items-center gap-1 mt-1">
            {trend.value >= 0 ? (
              <TrendingUp className="h-3 w-3 text-green-500" />
            ) : (
              <TrendingDown className="h-3 w-3 text-red-500" />
            )}
            <span className={trend.value >= 0 ? "text-green-500" : "text-red-500"}>
              {Math.abs(trend.value)}%
            </span>
            <span>{trend.label}</span>
          </p>
        )}
      </CardContent>
    </Card>
  );
}

export function DashboardStats() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["dashboard-summary"],
    queryFn: () => analyticsApi.getDashboardSummary(),
    staleTime: 60000,
  });

  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i}>
            <CardContent className="h-24 animate-shimmer" />
          </Card>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardContent className="h-24 flex items-center justify-center text-red-500">
            Failed to load dashboard stats
          </CardContent>
        </Card>
      </div>
    );
  }

  const stats = data?.data;

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <StatCard
        title="Total Habitations"
        value={stats?.total_habitations ? formatNumber(stats.total_habitations) : "—"}
        icon={<Users className="h-5 w-5" />}
        iconColor="text-blue-500"
        trend={stats ? { value: 2.3, label: "vs last month" } : undefined}
      />
      <StatCard
        title="Population at Risk"
        value={stats?.population_at_risk ? formatNumber(stats.population_at_risk) : "—"}
        icon={<Activity className="h-5 w-5" />}
        iconColor="text-red-500"
        trend={stats ? { value: -1.2, label: "vs last month" } : undefined}
      />
      <StatCard
        title="Active Red Zones"
        value={stats?.active_red_zones ? formatNumber(stats.active_red_zones) : "—"}
        icon={<AlertTriangle className="h-5 w-5" />}
        iconColor="text-orange-500"
        trend={stats ? { value: 5.1, label: "vs last month" } : undefined}
      />
      <StatCard
        title="High Vulnerability"
        value={stats?.high_vulnerability_habitations ? formatNumber(stats.high_vulnerability_habitations) : "—"}
        icon={<MapPin className="h-5 w-5" />}
        iconColor="text-purple-500"
      />
      <StatCard
        title="Relocation Sites"
        value={stats?.total_relocation_sites ? formatNumber(stats.total_relocation_sites) : "—"}
        icon={<Building2 className="h-5 w-5" />}
        iconColor="text-green-500"
      />
      <StatCard
        title="Total Capacity"
        value={stats?.total_capacity ? formatNumber(stats.total_capacity) : "—"}
        icon={<Users className="h-5 w-5" />}
        iconColor="text-teal-500"
      />
      <StatCard
        title="Immediate Priority"
        value={stats?.immediate_priority_count ? formatNumber(stats.immediate_priority_count) : "—"}
        icon={<AlertTriangle className="h-5 w-5" />}
        iconColor="text-red-600"
      />
      <StatCard
        title="Short Term Priority"
        value={stats?.short_term_priority_count ? formatNumber(stats.short_term_priority_count) : "—"}
        icon={<AlertTriangle className="h-5 w-5" />}
        iconColor="text-orange-600"
      />
    </div>
  );
}