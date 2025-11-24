import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { api, UserTool } from '@/lib/api';
import { DashboardLayout } from '@/components/DashboardLayout';
import { PageHeader } from '@/components/PageHeader';
import { Package, Wrench, Activity, TrendingUp, Plus, ArrowRight } from 'lucide-react';

export default function Dashboard() {
  const navigate = useNavigate();

  // Fetch user's tools
  const { data: myTools = [], isLoading: toolsLoading } = useQuery({
    queryKey: ['myTools'],
    queryFn: () => api.tools.list(),
  });

  // Fetch available tools from catalogue
  const { data: catalogue = [], isLoading: catalogueLoading } = useQuery({
    queryKey: ['catalogue'],
    queryFn: () => api.catalogue.list(),
  });

  // Fetch health status
  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: () => api.health(),
    refetchInterval: 30000,
  });

  // Calculate metrics
  const totalTools = catalogue.length || 0;
  const myToolsCount = myTools.length || 0;
  const enabledTools = myTools.filter((t: UserTool) => t.enabled).length || 0;
  const categories = new Set(catalogue.map((t: any) => t.category)).size || 0;

  // Get recently added tools (last 3)
  const recentTools = myTools
    .sort((a: UserTool, b: UserTool) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 3);

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <PageHeader
          title="Dashboard"
          subtitle="Overview of your MCP tool collection"
          action={
            <div className="flex gap-2">
              <div className="px-4 py-2 bg-muted rounded-lg elevation-sm border border-border">
                <span className="text-xs text-muted-foreground">Hub Status: </span>
                <span className={`text-sm font-semibold ${health?.status === 'healthy' ? 'text-success' : 'text-destructive'}`}>
                  {health?.status === 'healthy' ? '● Online' : '● Offline'}
                </span>
              </div>
              <Button onClick={() => navigate('/catalogue')}>
                <Plus className="h-4 w-4 mr-2" />
                Add Tools
              </Button>
            </div>
          }
        />

        {/* Metrics Grid */}
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Available Tools</CardTitle>
              <Package className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{totalTools}</div>
              <p className="text-xs text-muted-foreground">
                {categories} categories
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">My Tools</CardTitle>
              <Wrench className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{myToolsCount}</div>
              <p className="text-xs text-muted-foreground">
                configured tools
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Tools</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{enabledTools}</div>
              <p className="text-xs text-muted-foreground">
                currently enabled
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Status</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-success">Ready</div>
              <p className="text-xs text-muted-foreground">
                all systems operational
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions */}
        <div className="grid gap-6 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
              <CardDescription>Common tasks to get started</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button
                variant="outline"
                className="w-full justify-between"
                onClick={() => navigate('/catalogue')}
              >
                Browse Tool Catalogue
                <ArrowRight className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                className="w-full justify-between"
                onClick={() => navigate('/my-tools')}
              >
                Manage My Tools
                <ArrowRight className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                className="w-full justify-between"
                onClick={() => navigate('/settings')}
              >
                Configure Settings
                <ArrowRight className="h-4 w-4" />
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Recent Tools</CardTitle>
                  <CardDescription>Recently added to your collection</CardDescription>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => navigate('/my-tools')}
                >
                  View All
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {toolsLoading ? (
                <div className="flex items-center justify-center py-8">
                  <div className="h-8 w-8 rounded-full border-4 border-primary/20 border-t-primary animate-spin"></div>
                </div>
              ) : recentTools.length === 0 ? (
                <div className="text-center py-8">
                  <Package className="h-12 w-12 text-muted-foreground mx-auto mb-2" />
                  <p className="text-sm text-muted-foreground">No tools configured yet</p>
                  <Button
                    variant="link"
                    className="mt-2"
                    onClick={() => navigate('/catalogue')}
                  >
                    Browse catalogue
                  </Button>
                </div>
              ) : (
                <div className="space-y-2">
                  {recentTools.map((tool: UserTool) => (
                    <div
                      key={tool.tool_name}
                      className="flex items-center justify-between p-3 rounded-lg border border-border hover:bg-accent cursor-pointer"
                      onClick={() => navigate('/my-tools')}
                    >
                      <div className="flex items-center gap-3">
                        <Wrench className="h-4 w-4 text-muted-foreground" />
                        <div>
                          <p className="text-sm font-medium">{tool.tool_name}</p>
                          <p className="text-xs text-muted-foreground">
                            Added {new Date(tool.created_at).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                      <div
                        className={`h-2 w-2 rounded-full ${
                          tool.enabled ? 'bg-success' : 'bg-muted-foreground'
                        }`}
                      />
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Getting Started */}
        {myToolsCount === 0 && !toolsLoading && (
          <Card className="border-primary/20 bg-primary/5">
            <CardHeader>
              <CardTitle>Get Started with Automagik Tools Hub</CardTitle>
              <CardDescription>
                Your personal MCP tool collection management system
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <div className="flex items-start gap-3">
                  <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-primary-foreground text-xs font-bold">
                    1
                  </div>
                  <div>
                    <p className="font-medium">Browse the Tool Catalogue</p>
                    <p className="text-sm text-muted-foreground">
                      Explore available MCP tools across different categories
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-primary-foreground text-xs font-bold">
                    2
                  </div>
                  <div>
                    <p className="font-medium">Configure Your Tools</p>
                    <p className="text-sm text-muted-foreground">
                      Add tools to your collection with custom configurations
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-primary-foreground text-xs font-bold">
                    3
                  </div>
                  <div>
                    <p className="font-medium">Start Using Your Tools</p>
                    <p className="text-sm text-muted-foreground">
                      Manage and control your tools from the My Tools dashboard
                    </p>
                  </div>
                </div>
              </div>
              <Button className="w-full" onClick={() => navigate('/catalogue')}>
                <Plus className="h-4 w-4 mr-2" />
                Browse Tool Catalogue
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </DashboardLayout>
  );
}
