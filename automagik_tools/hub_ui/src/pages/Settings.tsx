import { useQuery, useMutation } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { api, isAuthenticated } from '@/lib/api';
import { getUserInfo, isSuperAdmin } from '@/lib/auth';
import { DashboardLayout } from '@/components/DashboardLayout';
import { PageHeader } from '@/components/PageHeader';
import { ThemeToggle } from '@/components/ThemeToggle';
import { Settings as SettingsIcon, Shield, Info, Moon, Sun, Building, User, Key, AlertCircle, Rocket } from 'lucide-react';
import { formatDateTime } from '@/lib/utils';

export default function Settings() {
  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: () => api.health(),
  });

  const { data: workspace } = useQuery({
    queryKey: ['workspace'],
    queryFn: () => api.workspace.get(),
    enabled: isAuthenticated(),
  });

  const { data: modeData } = useQuery({
    queryKey: ['app-mode'],
    queryFn: async () => {
      const response = await fetch('/api/setup/mode');
      if (!response.ok) throw new Error('Failed to fetch mode');
      return response.json();
    }
  });

  const user = getUserInfo();
  const isAdmin = isSuperAdmin();
  const isLocalMode = modeData?.mode === 'local';

  return (
    <DashboardLayout>
      <div className="flex flex-col h-full">
        <PageHeader
          title="Settings"
          subtitle="Configure your Tools Hub preferences"
          icon={<SettingsIcon className="h-6 w-6 text-primary" />}
        />

        {/* Main Content */}
        <div className="flex-1 overflow-auto bg-background">
          <div className="p-8 space-y-6 animate-fade-in max-w-4xl">
            {/* User Profile */}
            {user && (
              <Card className="border-border elevation-md">
                <CardHeader>
                  <div className="flex items-center gap-2">
                    <User className="h-5 w-5 text-primary" />
                    <CardTitle>Profile</CardTitle>
                  </div>
                  <CardDescription>Your account information</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex justify-between items-center p-3 bg-muted rounded-lg border border-border">
                    <span className="text-sm font-medium text-foreground">Email</span>
                    <span className="text-sm text-muted-foreground">{user.email}</span>
                  </div>

                  <div className="flex justify-between items-center p-3 bg-muted rounded-lg border border-border">
                    <span className="text-sm font-medium text-foreground">Name</span>
                    <span className="text-sm text-muted-foreground">
                      {user.first_name && user.last_name
                        ? `${user.first_name} ${user.last_name}`
                        : user.first_name || 'Not set'}
                    </span>
                  </div>

                  <div className="flex justify-between items-center p-3 bg-muted rounded-lg border border-border">
                    <span className="text-sm font-medium text-foreground">Role</span>
                    {isAdmin ? (
                      <Badge className="bg-amber-500/10 text-amber-500 border-amber-500/20">
                        Super Admin
                      </Badge>
                    ) : (
                      <Badge variant="outline">Workspace Owner</Badge>
                    )}
                  </div>

                  <div className="flex justify-between items-center p-3 bg-muted rounded-lg border border-border">
                    <span className="text-sm font-medium text-foreground">MFA Status</span>
                    {user.mfa_enabled ? (
                      <Badge className="gradient-success border-0">Enabled</Badge>
                    ) : (
                      <Badge variant="outline">Not enabled</Badge>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Workspace */}
            <Card className="border-border elevation-md">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Building className="h-5 w-5 text-primary" />
                  <CardTitle>Workspace</CardTitle>
                </div>
                <CardDescription>Your workspace settings</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between items-center p-3 bg-muted rounded-lg border border-border">
                  <span className="text-sm font-medium text-foreground">Name</span>
                  <span className="text-sm text-muted-foreground">
                    {workspace?.name || user?.workspace_name || 'Loading...'}
                  </span>
                </div>

                <div className="flex justify-between items-center p-3 bg-muted rounded-lg border border-border">
                  <span className="text-sm font-medium text-foreground">Slug</span>
                  <code className="text-sm text-muted-foreground">
                    @{workspace?.slug || user?.workspace_slug || '...'}
                  </code>
                </div>

                {workspace?.stats && (
                  <>
                    <div className="flex justify-between items-center p-3 bg-muted rounded-lg border border-border">
                      <span className="text-sm font-medium text-foreground">Tools</span>
                      <span className="text-sm text-muted-foreground">
                        {workspace.stats.tools.enabled} / {workspace.stats.tools.total} enabled
                      </span>
                    </div>

                    <div className="flex justify-between items-center p-3 bg-muted rounded-lg border border-border">
                      <span className="text-sm font-medium text-foreground">Credentials</span>
                      <span className="text-sm text-muted-foreground">
                        {workspace.stats.credentials} stored
                      </span>
                    </div>

                    <div className="flex justify-between items-center p-3 bg-muted rounded-lg border border-border">
                      <span className="text-sm font-medium text-foreground">Audit Events (30d)</span>
                      <span className="text-sm text-muted-foreground">
                        {workspace.stats.audit_events_30d} events
                      </span>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>

            {/* Team Mode Upgrade */}
            {isLocalMode && (
              <Card className="border-border elevation-md border-amber-500/20 bg-amber-500/5">
                <CardHeader>
                  <div className="flex items-center gap-2">
                    <Rocket className="h-5 w-5 text-amber-500" />
                    <CardTitle>Upgrade to Team Mode</CardTitle>
                  </div>
                  <CardDescription>
                    You're currently in Local Mode (single admin, no password).
                    Upgrade to Team Mode for multi-user workspaces with SSO, MFA, and directory sync.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <Alert className="border-amber-500/30 bg-amber-500/10">
                    <AlertCircle className="h-4 w-4 text-amber-500" />
                    <AlertTitle className="text-amber-500">Warning</AlertTitle>
                    <AlertDescription className="text-amber-600 dark:text-amber-400">
                      This upgrade is <strong>irreversible</strong>. Team mode requires WorkOS credentials.
                    </AlertDescription>
                  </Alert>
                </CardContent>
                <CardFooter>
                  <AlertDialog>
                    <AlertDialogTrigger asChild>
                      <Button className="gradient-primary border-0">
                        <Rocket className="h-4 w-4 mr-2" />
                        Upgrade to Team Mode
                      </Button>
                    </AlertDialogTrigger>
                    <AlertDialogContent>
                      <AlertDialogHeader>
                        <AlertDialogTitle>Ready to upgrade?</AlertDialogTitle>
                        <AlertDialogDescription>
                          You'll be redirected to the setup wizard to configure WorkOS for team mode.
                          This action is irreversible.
                        </AlertDialogDescription>
                      </AlertDialogHeader>
                      <AlertDialogFooter>
                        <AlertDialogCancel>Cancel</AlertDialogCancel>
                        <AlertDialogAction
                          onClick={() => window.location.href = '/app/setup?mode=upgrade'}
                          className="gradient-primary border-0"
                        >
                          Continue to Setup
                        </AlertDialogAction>
                      </AlertDialogFooter>
                    </AlertDialogContent>
                  </AlertDialog>
                </CardFooter>
              </Card>
            )}

            {/* Authentication */}
            <Card className="border-border elevation-md">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Key className="h-5 w-5 text-primary" />
                  <CardTitle>Authentication</CardTitle>
                </div>
                <CardDescription>Your Hub authentication status</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between items-center p-3 bg-muted rounded-lg border border-border">
                  <span className="text-sm font-medium text-foreground">Hub URL</span>
                  <code className="text-sm text-muted-foreground">
                    {import.meta.env.VITE_HUB_URL || 'http://localhost:8000'}
                  </code>
                </div>

                <div className="flex justify-between items-center p-3 bg-muted rounded-lg border border-border">
                  <span className="text-sm font-medium text-foreground">Authentication</span>
                  <span className="text-sm text-muted-foreground">Secure HTTP-only cookies</span>
                </div>

                <div className="flex justify-between items-center p-3 bg-muted rounded-lg border border-border">
                  <span className="text-sm font-medium text-foreground">Hub Status</span>
                  {health ? (
                    <Badge className="gradient-success border-0">
                      {health.status === 'healthy' ? 'Connected' : health.status}
                    </Badge>
                  ) : (
                    <Badge variant="outline">Checking...</Badge>
                  )}
                </div>

                {health?.version && (
                  <div className="flex justify-between items-center p-3 bg-muted rounded-lg border border-border">
                    <span className="text-sm font-medium text-foreground">Hub Version</span>
                    <code className="text-sm text-muted-foreground">{health.version}</code>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Theme Settings */}
            <Card className="border-border elevation-md">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Moon className="h-5 w-5 text-primary dark:hidden" />
                  <Sun className="h-5 w-5 text-primary hidden dark:block" />
                  <CardTitle>Appearance</CardTitle>
                </div>
                <CardDescription>Customize the look and feel of the interface</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between items-center p-3 bg-muted rounded-lg border border-border">
                  <div>
                    <span className="text-sm font-medium text-foreground block">Theme</span>
                    <span className="text-xs text-muted-foreground">
                      Toggle between light and dark mode
                    </span>
                  </div>
                  <ThemeToggle />
                </div>

                <div className="flex justify-between items-center p-3 bg-muted rounded-lg border border-border">
                  <span className="text-sm font-medium text-foreground">Primary Color</span>
                  <div className="flex items-center gap-2">
                    <div className="h-6 w-6 rounded-full gradient-primary border-2 border-border"></div>
                    <code className="text-sm text-muted-foreground">Purple</code>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* About */}
            <Card className="border-border elevation-md">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Info className="h-5 w-5 text-primary" />
                  <CardTitle>About</CardTitle>
                </div>
                <CardDescription>Information about Automagik Tools Hub UI</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between items-center p-3 bg-muted rounded-lg border border-border">
                  <span className="text-sm font-medium text-foreground">Application</span>
                  <span className="text-sm text-muted-foreground">Automagik Tools Hub UI</span>
                </div>

                <div className="flex justify-between items-center p-3 bg-muted rounded-lg border border-border">
                  <span className="text-sm font-medium text-foreground">Version</span>
                  <code className="text-sm text-muted-foreground">0.1.0</code>
                </div>

                <div className="flex justify-between items-center p-3 bg-muted rounded-lg border border-border">
                  <span className="text-sm font-medium text-foreground">Framework</span>
                  <span className="text-sm text-muted-foreground">React 19 + Vite 6</span>
                </div>

                {health?.timestamp && (
                  <div className="flex justify-between items-center p-3 bg-muted rounded-lg border border-border">
                    <span className="text-sm font-medium text-foreground">Last Hub Check</span>
                    <span className="text-sm text-muted-foreground">
                      {formatDateTime(health.timestamp)}
                    </span>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Footer */}
            <div className="pt-6 pb-4">
              <Separator className="mb-4" />
              <p className="text-xs text-center text-muted-foreground">
                Automagik Tools Hub - Your Personal MCP Tool Collection
                <br />
                Built with React, TypeScript, and shadcn/ui
              </p>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
