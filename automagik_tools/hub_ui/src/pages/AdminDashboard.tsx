import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { api } from '@/lib/api';
import { isSuperAdmin } from '@/lib/auth';
import { DashboardLayout } from '@/components/DashboardLayout';
import { PageHeader } from '@/components/PageHeader';
import {
  Shield,
  Building,
  Users,
  FileText,
  AlertTriangle,
  CheckCircle,
  XCircle,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
} from 'lucide-react';
import { formatDateTime } from '@/lib/utils';

const PAGE_SIZE = 20;

export default function AdminDashboard() {
  const navigate = useNavigate();
  const [selectedWorkspace, setSelectedWorkspace] = useState<string>('all');
  const [auditPage, setAuditPage] = useState(0);

  // Check super admin access
  const hasAccess = isSuperAdmin();

  // Fetch all workspaces
  const { data: workspaces = [], isLoading: workspacesLoading } = useQuery({
    queryKey: ['adminWorkspaces'],
    queryFn: () => api.admin.listWorkspaces({ limit: 100 }),
    enabled: hasAccess,
  });

  // Fetch all audit logs
  const {
    data: auditLogs = [],
    isLoading: logsLoading,
    refetch: refetchLogs,
  } = useQuery({
    queryKey: ['adminAuditLogs', selectedWorkspace, auditPage],
    queryFn: () =>
      api.admin.listAllAuditLogs({
        workspace_id: selectedWorkspace === 'all' ? undefined : selectedWorkspace,
        limit: PAGE_SIZE,
        offset: auditPage * PAGE_SIZE,
      }),
    enabled: hasAccess,
  });

  // Redirect if not super admin
  if (!hasAccess) {
    return (
      <DashboardLayout>
        <div className="flex flex-col items-center justify-center h-full space-y-4">
          <AlertTriangle className="h-16 w-16 text-destructive" />
          <h1 className="text-2xl font-bold">Access Denied</h1>
          <p className="text-muted-foreground">
            You don't have permission to access the admin dashboard.
          </p>
          <Button onClick={() => navigate('/dashboard')}>Return to Dashboard</Button>
        </div>
      </DashboardLayout>
    );
  }

  // Calculate stats
  const totalWorkspaces = workspaces.length;
  const recentLogs = auditLogs.filter((log) => {
    const logDate = new Date(log.occurred_at);
    const dayAgo = new Date();
    dayAgo.setDate(dayAgo.getDate() - 1);
    return logDate > dayAgo;
  }).length;
  const failedLogs = auditLogs.filter((log) => !log.success).length;

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <PageHeader
          title="Admin Dashboard"
          subtitle="Platform-wide management and monitoring"
          icon={<Shield className="h-6 w-6 text-primary" />}
        />

        {/* Stats Cards */}
        <div className="grid gap-6 md:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Workspaces</CardTitle>
              <Building className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {workspacesLoading ? '...' : totalWorkspaces}
              </div>
              <p className="text-xs text-muted-foreground">Active workspaces</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Users</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{totalWorkspaces}</div>
              <p className="text-xs text-muted-foreground">Registered users</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Events (24h)</CardTitle>
              <FileText className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{recentLogs}</div>
              <p className="text-xs text-muted-foreground">Audit events</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Failed Events</CardTitle>
              <AlertTriangle className="h-4 w-4 text-destructive" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-destructive">{failedLogs}</div>
              <p className="text-xs text-muted-foreground">In current view</p>
            </CardContent>
          </Card>
        </div>

        {/* Workspaces List */}
        <Card>
          <CardHeader>
            <CardTitle>All Workspaces</CardTitle>
            <CardDescription>
              Manage all workspaces on the platform
            </CardDescription>
          </CardHeader>
          <CardContent>
            {workspacesLoading ? (
              <div className="flex items-center justify-center py-8">
                <div className="h-8 w-8 rounded-full border-4 border-primary/20 border-t-primary animate-spin"></div>
              </div>
            ) : workspaces.length === 0 ? (
              <div className="text-center py-8">
                <Building className="h-12 w-12 text-muted-foreground mx-auto mb-2" />
                <p className="text-sm text-muted-foreground">No workspaces found</p>
              </div>
            ) : (
              <div className="space-y-2">
                {workspaces.slice(0, 10).map((workspace) => (
                  <div
                    key={workspace.id}
                    className="flex items-center justify-between p-4 rounded-lg border border-border hover:bg-accent/50 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <Building className="h-5 w-5 text-muted-foreground" />
                      <div>
                        <p className="font-medium">{workspace.name}</p>
                        <p className="text-xs text-muted-foreground">
                          @{workspace.slug} • Created{' '}
                          {new Date(workspace.created_at).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                    <Badge variant="outline">Active</Badge>
                  </div>
                ))}
                {workspaces.length > 10 && (
                  <p className="text-center text-sm text-muted-foreground pt-2">
                    Showing 10 of {workspaces.length} workspaces
                  </p>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Platform Audit Logs */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Platform Audit Logs</CardTitle>
                <CardDescription>
                  Monitor all activity across the platform
                </CardDescription>
              </div>
              <div className="flex gap-2">
                <Select
                  value={selectedWorkspace}
                  onValueChange={(v) => {
                    setSelectedWorkspace(v);
                    setAuditPage(0);
                  }}
                >
                  <SelectTrigger className="w-[200px]">
                    <SelectValue placeholder="Filter by workspace" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Workspaces</SelectItem>
                    {workspaces.map((ws) => (
                      <SelectItem key={ws.id} value={ws.id}>
                        {ws.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Button variant="outline" size="icon" onClick={() => refetchLogs()}>
                  <RefreshCw className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {logsLoading ? (
              <div className="flex items-center justify-center py-8">
                <div className="h-8 w-8 rounded-full border-4 border-primary/20 border-t-primary animate-spin"></div>
              </div>
            ) : auditLogs.length === 0 ? (
              <div className="text-center py-8">
                <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-2" />
                <p className="text-sm text-muted-foreground">No audit logs found</p>
              </div>
            ) : (
              <div className="space-y-2">
                {auditLogs.map((log) => (
                  <div
                    key={log.id}
                    className="flex items-start gap-4 p-3 rounded-lg border border-border hover:bg-accent/50 transition-colors"
                  >
                    {log.success ? (
                      <CheckCircle className="h-4 w-4 text-success mt-1" />
                    ) : (
                      <XCircle className="h-4 w-4 text-destructive mt-1" />
                    )}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-sm">{log.action}</span>
                        <Badge variant="outline" className="text-xs">
                          {log.category}
                        </Badge>
                      </div>
                      <div className="flex flex-wrap gap-2 text-xs text-muted-foreground mt-1">
                        <span>{formatDateTime(log.occurred_at)}</span>
                        {log.actor.email && <span>• {log.actor.email}</span>}
                        {log.target?.name && <span>• {log.target.name}</span>}
                      </div>
                      {log.error_message && (
                        <p className="mt-1 text-xs text-destructive">
                          {log.error_message}
                        </p>
                      )}
                    </div>
                  </div>
                ))}

                {/* Pagination */}
                <div className="flex items-center justify-between pt-4 border-t border-border">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={auditPage === 0}
                    onClick={() => setAuditPage((p) => Math.max(0, p - 1))}
                  >
                    <ChevronLeft className="h-4 w-4 mr-1" />
                    Previous
                  </Button>
                  <span className="text-sm text-muted-foreground">
                    Page {auditPage + 1}
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={auditLogs.length < PAGE_SIZE}
                    onClick={() => setAuditPage((p) => p + 1)}
                  >
                    Next
                    <ChevronRight className="h-4 w-4 ml-1" />
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
