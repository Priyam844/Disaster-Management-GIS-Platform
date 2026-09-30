"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { MapView } from "@/components/map/MapView";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { DashboardStats } from "@/components/dashboard/DashboardStats";
import { useAuthStore } from "@/lib/stores/authStore";

export default function DashboardPage() {
  const router = useRouter();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const { user, isAuthenticated, isLoading } = useAuthStore();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, isLoading, router]);

  if (isLoading || !isAuthenticated) {
    return null;
  }

  return (
    <div className="h-screen w-full flex overflow-hidden bg-gray-50 dark:bg-gray-900">
      {/* Sidebar */}
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <Header onMenuClick={() => setSidebarOpen(true)} user={user} />

        {/* Dashboard Content */}
        <main className="flex-1 overflow-auto p-4 md:p-6">
          <div className="max-w-7xl mx-auto space-y-6">
            {/* Stats Cards */}
            <DashboardStats />

            {/* Map View */}
            <div className="h-[calc(100vh-300px)] min-h-[500px] rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden shadow-sm">
              <MapView />
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}