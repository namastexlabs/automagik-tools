import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { api } from '@/lib/api';
import { DashboardLayout } from '@/components/DashboardLayout';
import { PageHeader } from '@/components/PageHeader';
import {
  FileText,
  CheckCircle,
  XCircle,
  User,
  Wrench,
  Key,
  Shield,
  Building,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { formatDateTime } from '@/lib/utils';

const CATEGORIES = [
  { value: 'all', label: 'All Categories' },
  { value: 'auth', label: 'Authentication' },
  { value: 'tool', label: 'Tools' },
  { value: 'credential', label: 'Credentials' },
  { value: 'admin', label: 'Admin' },
  { value: 'workspace', label: 'Workspace' },
];

const PAGE_SIZE = 20;

function getCategoryIcon(category: string) {
  switch (category) {
    case 'auth':
      return <Shield className="h-4 w-4" />;
    case 'tool':
      return <Wrench className="h-4 w-4" />;
    case 'credential':
      return <Key className="h-4 w-4" />;
    case 'admin':
      return <User className="h-4 w-4" />;
    case 'workspace':
      return <Building className="h-4 w-4" />;
    default:
      return <FileText className="h-4 w-4" />;
  }
}

function getCategoryColor(category: string) {
  switch (category) {
    case 'auth':
      return 'bg-blue-500/10 text-blue-500 border-blue-500/20';
    case 'tool':
      return 'bg-purple-500/10 text-purple-500 border-purple-500/20';
    case 'credential':
      return 'bg-amber-500/10 text-amber-500 border-amber-500/20';
    case 'admin':
      return 'bg-red-500/10 text-red-500 border-red-500/20';
    case 'workspace':
      return 'bg-green-500/10 text-green-500 border-green-500/20';
    default:
      return 'bg-gray-500/10 text-gray-500 border-gray-500/20';
  }
}

export default function AuditLogs() {
  const [category, setCategory] = useState('all');
  const [page, setPage] = useState(0);

  const { data: logs = [], isLoading, refetch } = useQuery({
    queryKey: ['auditLogs', category, page],
    queryFn: () =>
      api.auditLogs.list({
        category: category === 'all' ? undefined : category,
        limit: PAGE_SIZE,
        offset: page * PAGE_SIZE,
      }),
  });

  const handleCategoryChange = (value: string) => {
    setCategory(value);
    setPage(0);
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <PageHeader
          title="Audit Logs"
          subtitle="Track all activity in your workspace"
          icon={<FileText className="h-6 w-6 text-primary" />}
          action={
            <div className="flex gap-2">
              <Select value={category} onValueChange={handleCategoryChange}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Select category" />
                </SelectTrigger>
                <SelectContent>
                  {CATEGORIES.map((cat) => (
                    <SelectItem key={cat.value} value={cat.value}>
                      {cat.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button variant="outline" size="icon" onClick={() => refetch()}>
                <RefreshCw className="h-4 w-4" />
              </Button>
            </div>
          }
        />

        <Card>
          <CardHeader>
            <CardTitle>Activity Log</CardTitle>
            <CardDescription>
              Recent events in your workspace (showing {logs.length} entries)
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="flex items-center justify-center py-12">
                <div className="h-8 w-8 rounded-full border-4 border-primary/20 border-t-primary animate-spin"></div>
              </div>
            ) : logs.length === 0 ? (
              <div className="text-center py-12">
                <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-2" />
                <p className="text-sm text-muted-foreground">No audit logs found</p>
              </div>
            ) : (
              <div className="space-y-2">
                {logs.map((log) => (
                  <div
                    key={log.id}
                    className="flex items-start gap-4 p-4 rounded-lg border border-border hover:bg-accent/50 transition-colors"
                  >
                    {/* Status & Category */}
                    <div className="flex flex-col items-center gap-2">
                      {log.success ? (
                        <CheckCircle className="h-5 w-5 text-success" />
                      ) : (
                        <XCircle className="h-5 w-5 text-destructive" />
                      )}
                      <Badge
                        variant="outline"
                        className={`text-xs ${getCategoryColor(log.category)}`}
                      >
                        {getCategoryIcon(log.category)}
                      </Badge>
                    </div>

                    {/* Details */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-medium text-sm">{log.action}</span>
                        <span className="text-xs text-muted-foreground">
                          {formatDateTime(log.occurred_at)}
                        </span>
                      </div>

                      <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
                        {log.actor.email && (
                          <span className="flex items-center gap-1">
                            <User className="h-3 w-3" />
                            {log.actor.email}
                          </span>
                        )}
                        {log.target && (
                          <span className="flex items-center gap-1">
                            {getCategoryIcon(log.target.type)}
                            {log.target.name || log.target.id || log.target.type}
                          </span>
                        )}
                      </div>

                      {log.error_message && (
                        <p className="mt-2 text-xs text-destructive bg-destructive/10 p-2 rounded">
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
                    disabled={page === 0}
                    onClick={() => setPage((p) => Math.max(0, p - 1))}
                  >
                    <ChevronLeft className="h-4 w-4 mr-1" />
                    Previous
                  </Button>
                  <span className="text-sm text-muted-foreground">Page {page + 1}</span>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={logs.length < PAGE_SIZE}
                    onClick={() => setPage((p) => p + 1)}
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
