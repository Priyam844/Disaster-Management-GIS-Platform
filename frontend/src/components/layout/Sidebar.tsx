"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  LayoutDashboard,
  Map,
  Layers,
  Building2,
  AlertTriangle,
  ListChecks,
  BarChart3,
  Settings,
  HelpCircle,
  ChevronLeft,
  ChevronRight,
  Menu,
  X,
} from "lucide-react";

const navigation = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard },
  { name: "Hazard Explorer", href: "/hazards", icon: AlertTriangle },
  { name: "Red Zones", href: "/hazards/red-zones", icon: Layers },
  { name: "Relocation Sites", href: "/sites", icon: Building2 },
  { name: "Prioritization", href: "/prioritization", icon: ListChecks },
  { name: "Habitations", href: "/habitations", icon: Map },
  { name: "Analytics", href: "/analytics", icon: BarChart3 },
  { name: "Settings", href: "/settings", icon: Settings },
];

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export function Sidebar({ isOpen, onClose }: SidebarProps) {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <>
      {/* Overlay for mobile */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed lg:static inset-y-0 left-0 z-50 flex flex-col bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700 transition-all duration-300 ease-in-out",
          isOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0",
          collapsed ? "w-16" : "w-64"
        )}
      >
        {/* Logo & Collapse Toggle */}
        <div className={cn("flex h-16 items-center justify-between px-4 border-b border-gray-200 dark:border-gray-700", collapsed && "justify-center")}>
          {!collapsed && (
            <Link href="/" className="flex items-center gap-2 font-bold text-lg text-primary">
              <AlertTriangle className="h-6 w-6" />
              <span>GIS Disaster Platform</span>
            </Link>
          )}
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setCollapsed(!collapsed)}
            className="text-gray-500 hover:text-gray-900 dark:hover:text-gray-100"
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {collapsed ? <ChevronRight className="h-5 w-5" /> : <ChevronLeft className="h-5 w-5" />}
          </Button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto p-4 space-y-1" aria-label="Main navigation">
          {navigation.map((item) => {
            const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                  isActive
                    ? "bg-primary text-primary-foreground"
                    : "text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800",
                  collapsed && "justify-center"
                )}
                onClick={onClose}
                aria-current={isActive ? "page" : undefined}
              >
                <item.icon className="h-5 w-5 flex-shrink-0" aria-hidden="true" />
                {!collapsed && <span>{item.name}</span>}
              </Link>
            );
          })}
        </nav>

        {/* Footer */}
        <div className={cn("p-4 border-t border-gray-200 dark:border-gray-700", collapsed && "hidden")}>
          <div className="text-xs text-gray-500 dark:text-gray-400 space-y-1">
            <p>GIS Disaster Management Platform v1.0.0</p>
            <p>For SDMA Official Use Only</p>
          </div>
        </div>
      </aside>
    </>
  );
}