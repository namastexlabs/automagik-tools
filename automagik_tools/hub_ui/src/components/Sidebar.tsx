import { Link, useLocation } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { isSuperAdmin, getUserInfo, getUserDisplayName, getUserInitials } from '@/lib/auth';
import {
  LayoutDashboard,
  Package,
  Wrench,
  Settings,
  LogOut,
  FileText,
  Shield,
} from 'lucide-react';

interface SidebarProps {
  onLogout: () => void;
}

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Catalogue', href: '/catalogue', icon: Package },
  { name: 'My Tools', href: '/my-tools', icon: Wrench },
  { name: 'Audit Logs', href: '/audit-logs', icon: FileText },
  { name: 'Settings', href: '/settings', icon: Settings },
];

const adminNavigation = [
  { name: 'Admin', href: '/admin', icon: Shield },
];

export function Sidebar({ onLogout }: SidebarProps) {
  const location = useLocation();
  const isAdmin = isSuperAdmin();
  const user = getUserInfo();
  const displayName = getUserDisplayName();
  const initials = getUserInitials();

  // Combine navigation items
  const allNavigation = isAdmin ? [...navigation, ...adminNavigation] : navigation;

  return (
    <div className="flex h-full w-64 flex-col bg-card border-r border-border elevation-sm">
      {/* Logo - Match dashboard header height exactly */}
      <div className="flex items-center justify-center border-b border-border px-6 py-3">
        <div className="flex items-center space-x-2">
          <Package className="h-8 w-8 text-primary" />
          <div className="flex flex-col">
            <span className="text-lg font-bold text-foreground">Automagik</span>
            <span className="text-xs text-muted-foreground">Tools Hub</span>
          </div>
        </div>
      </div>

      {/* User Info */}
      {user && (
        <div className="px-4 py-3 border-b border-border">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center text-primary font-semibold text-sm">
              {initials}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">{displayName}</p>
              <p className="text-xs text-muted-foreground truncate">{user.email}</p>
            </div>
          </div>
          {isAdmin && (
            <div className="mt-2 flex items-center gap-1.5 text-xs text-amber-500">
              <Shield className="h-3 w-3" />
              <span>Super Admin</span>
            </div>
          )}
        </div>
      )}

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-3 py-6 overflow-y-auto">
        {allNavigation.map((item) => {
          const isActive = location.pathname === item.href;
          return (
            <Link
              key={item.name}
              to={item.href}
              className={cn(
                'group flex items-center space-x-3 rounded-lg px-4 py-3 text-sm font-medium transition-all duration-200',
                isActive
                  ? 'bg-primary text-primary-foreground elevation-md'
                  : 'text-foreground hover:bg-accent hover:text-accent-foreground'
              )}
            >
              <item.icon className={cn(
                'h-5 w-5 transition-transform group-hover:scale-110',
                isActive ? 'text-primary-foreground' : 'text-muted-foreground group-hover:text-accent-foreground'
              )} />
              <span>{item.name}</span>
              {isActive && (
                <div className="ml-auto h-2 w-2 rounded-full bg-primary-foreground/80 animate-pulse"></div>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Workspace Info */}
      {user && (
        <div className="px-3 py-4 space-y-3">
          <div className="rounded-lg bg-primary/5 p-4 border border-primary/10">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium text-primary">Workspace</span>
            </div>
            <p className="text-sm font-semibold truncate">{user.workspace_name}</p>
            <p className="text-xs text-muted-foreground mt-1">@{user.workspace_slug}</p>
          </div>
        </div>
      )}

      {/* Stats/Info Section */}
      <div className="px-3 pb-4 space-y-3">
        <div className="rounded-lg bg-success/10 p-4 border border-success/20">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-success">Hub Status</span>
            <div className="h-2 w-2 bg-success rounded-full animate-pulse"></div>
          </div>
          <p className="text-sm font-semibold text-success">Connected</p>
          <p className="text-xs text-success/80 mt-1">Tools ready</p>
        </div>
      </div>

      {/* Footer */}
      <div className="border-t border-border p-4">
        <button
          onClick={onLogout}
          className="flex w-full items-center space-x-3 rounded-lg px-4 py-3 text-sm font-medium text-destructive hover:bg-destructive/10 transition-all group focus-ring"
        >
          <LogOut className="h-5 w-5 group-hover:scale-110 transition-transform" />
          <span>Logout</span>
        </button>
      </div>
    </div>
  );
}
