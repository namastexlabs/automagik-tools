import { DashboardLayout } from '@/components/DashboardLayout';
import { PageHeader } from '@/components/PageHeader';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Bot } from 'lucide-react';

export default function Agents() {
  return (
    <DashboardLayout>
      <PageHeader
        title="Agents"
        description="Configure agent toolkits and permissions"
      />

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Bot className="h-5 w-5 text-muted-foreground" />
            <CardTitle>Agent Management</CardTitle>
          </div>
          <CardDescription>
            View and configure toolkits for discovered .genie agents
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-12 text-muted-foreground">
            <p className="text-lg mb-2">🚧 Coming Soon</p>
            <p className="text-sm">
              Agent toolkit configuration UI is under development.
              API endpoints are ready at <code className="bg-muted px-2 py-1 rounded">/api/discovery/agents</code>
            </p>
          </div>
        </CardContent>
      </Card>
    </DashboardLayout>
  );
}
