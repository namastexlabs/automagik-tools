import { DashboardLayout } from '@/components/DashboardLayout';
import { PageHeader } from '@/components/PageHeader';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { FolderGit2 } from 'lucide-react';

export default function Projects() {
  return (
    <DashboardLayout>
      <PageHeader
        title="Projects"
        description="Discover and manage .genie projects"
      />

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <FolderGit2 className="h-5 w-5 text-muted-foreground" />
            <CardTitle>Project Discovery</CardTitle>
          </div>
          <CardDescription>
            Scan your base folders for git repositories containing .genie agents
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-12 text-muted-foreground">
            <p className="text-lg mb-2">🚧 Coming Soon</p>
            <p className="text-sm">
              Project discovery features are under development.
              API endpoints are ready at <code className="bg-muted px-2 py-1 rounded">/api/discovery/projects</code>
            </p>
          </div>
        </CardContent>
      </Card>
    </DashboardLayout>
  );
}
