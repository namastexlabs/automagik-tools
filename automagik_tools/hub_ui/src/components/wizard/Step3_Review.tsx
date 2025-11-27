/**
 * Step 3: Review and Complete
 *
 * Review all configuration before final submission.
 */
import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';
import {
  CheckCircle,
  AlertCircle,
  Loader2,
  Home,
  Users,
  Network,
  Folder,
  Mail,
  Key,
  Globe,
} from 'lucide-react';

interface ReviewProps {
  mode: 'local' | 'workos';
  localEmail?: string;
  databasePath?: string;
  bindAddress: 'localhost' | 'network';
  port: number;
  workosClientId?: string;
  workosApiKey?: string;
  workosAuthkitDomain?: string;
  workosAdminEmails?: string[];
  workosSetupType?: 'quick' | 'custom';
  onBack: () => void;
  onComplete: () => Promise<void>;
  isUpgrade?: boolean;
}

export function Step3_Review({
  mode,
  localEmail,
  databasePath,
  bindAddress,
  port,
  workosClientId,
  workosApiKey,
  workosAuthkitDomain,
  workosAdminEmails,
  workosSetupType,
  onBack,
  onComplete,
  isUpgrade = false,
}: ReviewProps) {
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleComplete = async () => {
    setSubmitting(true);
    setError(null);

    try {
      await onComplete();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Setup failed');
    } finally {
      setSubmitting(false);
    }
  };

  const modeConfig = mode === 'local' ? {
    icon: Home,
    title: '🏠 Local Mode',
    color: 'text-blue-600',
    bgColor: 'bg-blue-100 dark:bg-blue-950',
  } : {
    icon: Users,
    title: '🏢 Team Mode',
    color: 'text-purple-600',
    bgColor: 'bg-purple-100 dark:bg-purple-950',
  };

  return (
    <div className="space-y-6 max-w-2xl mx-auto">
      <div className="text-center">
        <h2 className="text-2xl font-bold mb-2">
          {isUpgrade ? '🚀 Ready to Upgrade' : '✨ Review Configuration'}
        </h2>
        <p className="text-muted-foreground">
          {isUpgrade
            ? 'Please review your upgrade settings'
            : 'Please review your settings before completing setup'}
        </p>
      </div>

      <div className="space-y-4">
        {/* Mode Selection */}
        <div className={`rounded-lg border p-4 ${modeConfig.bgColor} border-${modeConfig.color.split('-')[1]}-200`}>
          <div className="flex items-center gap-3">
            <modeConfig.icon className={`h-6 w-6 ${modeConfig.color}`} />
            <div>
              <div className="font-semibold">{modeConfig.title}</div>
              <div className="text-sm text-muted-foreground">
                {mode === 'local' ? 'Single admin, passwordless' : 'Enterprise SSO with WorkOS'}
              </div>
            </div>
          </div>
        </div>

        <Separator />

        {/* Mode-specific Configuration */}
        {mode === 'local' ? (
          <>
            {/* Local Mode Config */}
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-sm font-medium">
                <Mail className="h-4 w-4" />
                Admin Email
              </div>
              <div className="bg-muted/50 rounded-md p-3 font-mono text-sm">
                {localEmail}
              </div>
            </div>

            {databasePath && (
              <div className="space-y-3">
                <div className="flex items-center gap-2 text-sm font-medium">
                  <Folder className="h-4 w-4" />
                  Database Path
                </div>
                <div className="bg-muted/50 rounded-md p-3 font-mono text-sm">
                  {databasePath}
                </div>
              </div>
            )}

            <Alert>
              <AlertCircle className="h-4 w-4 text-amber-500" />
              <AlertDescription className="text-amber-600 dark:text-amber-400">
                <strong>Remember:</strong> Local mode is not persistent. Configuration will reset on server restart.
              </AlertDescription>
            </Alert>
          </>
        ) : (
          <>
            {/* WorkOS Config */}
            <div className="space-y-4">
              {workosSetupType && (
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-sm font-medium">
                    Setup Type
                  </div>
                  <Badge variant="outline" className="text-sm">
                    {workosSetupType === 'quick' ? '⚡ Quick Start' : '🎨 Custom App'}
                  </Badge>
                </div>
              )}

              <div className="space-y-3">
                <div className="flex items-center gap-2 text-sm font-medium">
                  <Key className="h-4 w-4" />
                  Client ID
                </div>
                <div className="bg-muted/50 rounded-md p-3 font-mono text-sm">
                  {workosClientId}
                </div>
              </div>

              <div className="space-y-3">
                <div className="flex items-center gap-2 text-sm font-medium">
                  <Key className="h-4 w-4" />
                  API Key
                </div>
                <div className="bg-muted/50 rounded-md p-3 font-mono text-sm">
                  {workosApiKey ? '••••••••••••' + workosApiKey.slice(-4) : ''}
                </div>
              </div>

              <div className="space-y-3">
                <div className="flex items-center gap-2 text-sm font-medium">
                  <Globe className="h-4 w-4" />
                  AuthKit Domain
                </div>
                <div className="bg-muted/50 rounded-md p-3 font-mono text-sm">
                  {workosAuthkitDomain}
                </div>
              </div>

              <div className="space-y-3">
                <div className="flex items-center gap-2 text-sm font-medium">
                  <Mail className="h-4 w-4" />
                  Super Admins
                </div>
                <div className="bg-muted/50 rounded-md p-3 space-y-1">
                  {workosAdminEmails?.map((email) => (
                    <div key={email} className="font-mono text-sm">
                      {email}
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <Alert>
              <AlertCircle className="h-4 w-4 text-amber-500" />
              <AlertDescription className="text-amber-600 dark:text-amber-400">
                <strong>Warning:</strong> WorkOS mode is irreversible. You cannot downgrade to local mode.
              </AlertDescription>
            </Alert>
          </>
        )}

        <Separator />

        {/* Network Configuration */}
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-sm font-medium">
            <Network className="h-4 w-4" />
            Network Configuration
          </div>
          <div className="bg-muted/50 rounded-md p-3 space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Bind Address:</span>
              <span className="font-mono">
                {bindAddress === 'localhost' ? '127.0.0.1 (localhost)' : '0.0.0.0 (all interfaces)'}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Port:</span>
              <span className="font-mono">{port}</span>
            </div>
            <Separator />
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">URL:</span>
              <span className="font-mono">
                http://{bindAddress === 'localhost' ? '127.0.0.1' : '<your-ip>'}:{port}
              </span>
            </div>
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
      </div>

      {/* Navigation */}
      <div className="flex gap-3 justify-between pt-4">
        <Button variant="outline" onClick={onBack} disabled={submitting}>
          Back
        </Button>
        <Button onClick={handleComplete} disabled={submitting} className="min-w-[140px]">
          {submitting ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              {isUpgrade ? 'Upgrading...' : 'Setting up...'}
            </>
          ) : (
            <>
              <CheckCircle className="mr-2 h-4 w-4" />
              {isUpgrade ? 'Upgrade Now' : 'Complete Setup'}
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
