/**
 * Restart Transition Component
 *
 * Handles the apply/restart flow for network configuration changes:
 * 1. Pre-apply confirmation with config summary
 * 2. Progress display during restart (saving, stopping, starting, verifying)
 * 3. Reconnection polling to new URL
 * 4. Success state with new URL and continue button
 * 5. Failure state with troubleshooting instructions
 */
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import {
  CheckCircle,
  AlertCircle,
  Loader2,
  RefreshCw,
  ExternalLink,
  Copy,
  Check,
  Network,
  Server,
  Zap,
} from 'lucide-react';

export interface RestartConfig {
  bindAddress: 'localhost' | 'network';
  port: number;
}

interface RestartTransitionProps {
  /** Whether the dialog is open */
  open: boolean;
  /** Callback when dialog should close (cancel or complete) */
  onOpenChange: (open: boolean) => void;
  /** Current configuration to apply */
  config: RestartConfig;
  /** Callback after successful restart and reconnection */
  onSuccess: (newUrl: string) => void;
  /** Optional: skip confirmation and go straight to applying */
  skipConfirmation?: boolean;
}

type Phase = 'confirm' | 'applying' | 'restarting' | 'reconnecting' | 'success' | 'failure';

interface PhaseState {
  phase: Phase;
  progress: number;
  message: string;
  error?: string;
  newUrl?: string;
  instructions?: string;
}

const PHASES = {
  confirm: { progress: 0, message: 'Ready to apply configuration' },
  applying: { progress: 20, message: 'Saving configuration...' },
  restarting: { progress: 40, message: 'Restarting server...' },
  reconnecting: { progress: 60, message: 'Waiting for server...' },
  success: { progress: 100, message: 'Connected to new server!' },
  failure: { progress: 0, message: 'Failed to reconnect' },
};

// Polling configuration
const POLL_INTERVAL_MS = 1000;
const MAX_POLL_ATTEMPTS = 30; // 30 seconds max wait

export function RestartTransition({
  open,
  onOpenChange,
  config,
  onSuccess,
  skipConfirmation = false,
}: RestartTransitionProps) {
  const [state, setState] = useState<PhaseState>({
    phase: 'confirm',
    progress: 0,
    message: PHASES.confirm.message,
  });
  const [copied, setCopied] = useState(false);
  const pollCountRef = useRef(0);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Calculate the new URL based on config
  const getNewUrl = useCallback(() => {
    const host = config.bindAddress === 'localhost' ? 'localhost' : window.location.hostname;
    return `http://${host}:${config.port}`;
  }, [config]);

  // Get display-friendly bind address
  const getBindAddressDisplay = () => {
    return config.bindAddress === 'localhost' ? '127.0.0.1 (localhost only)' : '0.0.0.0 (all interfaces)';
  };

  // Reset state when dialog opens
  useEffect(() => {
    if (open) {
      pollCountRef.current = 0;
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }

      if (skipConfirmation) {
        handleApply();
      } else {
        setState({
          phase: 'confirm',
          progress: 0,
          message: PHASES.confirm.message,
        });
      }
    }

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, [open, skipConfirmation]);

  // Poll for server health on new URL
  const pollForServer = useCallback(async (targetUrl: string) => {
    try {
      const response = await fetch(`${targetUrl}/api/server/health`, {
        method: 'GET',
        mode: 'cors',
        cache: 'no-cache',
      });

      if (response.ok) {
        const data = await response.json();
        // Verify we're connected to a fresh server (uptime < 30 seconds)
        if (data.status === 'ok' && data.uptime_seconds < 30) {
          return true;
        }
        // Server is up but might be old instance, keep polling
        return false;
      }
      return false;
    } catch {
      // Network error, server not up yet
      return false;
    }
  }, []);

  // Start polling for reconnection
  const startPolling = useCallback((targetUrl: string) => {
    pollCountRef.current = 0;

    setState(prev => ({
      ...prev,
      phase: 'reconnecting',
      progress: 60,
      message: 'Waiting for server to restart...',
      newUrl: targetUrl,
    }));

    pollIntervalRef.current = setInterval(async () => {
      pollCountRef.current += 1;

      // Update progress (60-95% during polling)
      const pollProgress = Math.min(95, 60 + (pollCountRef.current / MAX_POLL_ATTEMPTS) * 35);
      setState(prev => ({
        ...prev,
        progress: pollProgress,
        message: `Waiting for server... (${pollCountRef.current}/${MAX_POLL_ATTEMPTS})`,
      }));

      const isUp = await pollForServer(targetUrl);

      if (isUp) {
        // Success!
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current);
          pollIntervalRef.current = null;
        }
        setState({
          phase: 'success',
          progress: 100,
          message: 'Server is ready!',
          newUrl: targetUrl,
        });
        return;
      }

      if (pollCountRef.current >= MAX_POLL_ATTEMPTS) {
        // Timeout
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current);
          pollIntervalRef.current = null;
        }
        setState({
          phase: 'failure',
          progress: 0,
          message: 'Could not connect to server',
          error: 'Server did not respond within 30 seconds',
          newUrl: targetUrl,
          instructions: `Try manually navigating to ${targetUrl} or check if the server is running.`,
        });
      }
    }, POLL_INTERVAL_MS);
  }, [pollForServer]);

  // Apply configuration and trigger restart
  const handleApply = async () => {
    const targetUrl = getNewUrl();

    try {
      // Phase: Applying
      setState({
        phase: 'applying',
        progress: 20,
        message: 'Saving configuration to database...',
      });

      const response = await fetch('/api/server/apply-config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          bind_address: config.bindAddress === 'localhost' ? '127.0.0.1' : '0.0.0.0',
          port: config.port,
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to apply configuration');
      }

      const result = await response.json();

      // Phase: Restarting
      setState({
        phase: 'restarting',
        progress: 40,
        message: 'Server is restarting...',
        newUrl: result.new_url || targetUrl,
      });

      // Wait a moment for the old server to stop
      await new Promise(resolve => setTimeout(resolve, 2000));

      // Start polling for the new server
      startPolling(result.new_url || targetUrl);

    } catch (error) {
      setState({
        phase: 'failure',
        progress: 0,
        message: 'Failed to apply configuration',
        error: error instanceof Error ? error.message : 'Unknown error',
        instructions: 'Check the server logs for more details.',
      });
    }
  };

  // Retry connection
  const handleRetry = () => {
    if (state.newUrl) {
      startPolling(state.newUrl);
    } else {
      handleApply();
    }
  };

  // Copy URL to clipboard
  const copyUrl = async () => {
    if (state.newUrl) {
      try {
        await navigator.clipboard.writeText(state.newUrl);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      } catch {
        // Fallback
        const textArea = document.createElement('textarea');
        textArea.value = state.newUrl;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      }
    }
  };

  // Navigate to new URL
  const navigateToNewUrl = () => {
    if (state.newUrl) {
      window.location.href = state.newUrl;
    }
  };

  // Handle success continue
  const handleContinue = () => {
    if (state.newUrl) {
      onSuccess(state.newUrl);
      // If we're on the same origin, just close. Otherwise redirect.
      const currentOrigin = window.location.origin;
      const newOrigin = new URL(state.newUrl).origin;
      if (currentOrigin !== newOrigin) {
        window.location.href = state.newUrl;
      } else {
        onOpenChange(false);
      }
    }
  };

  // Render content based on phase
  const renderContent = () => {
    switch (state.phase) {
      case 'confirm':
        return (
          <>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Server className="h-5 w-5" />
                Apply Network Configuration
              </DialogTitle>
              <DialogDescription>
                The server will restart to apply these changes. This will briefly interrupt service.
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-4">
              <div className="bg-muted/50 rounded-lg p-4 space-y-3">
                <h4 className="font-medium flex items-center gap-2">
                  <Network className="h-4 w-4" />
                  New Configuration
                </h4>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <span className="text-muted-foreground">Bind Address:</span>
                  <span className="font-mono">{getBindAddressDisplay()}</span>
                  <span className="text-muted-foreground">Port:</span>
                  <span className="font-mono">{config.port}</span>
                  <span className="text-muted-foreground">New URL:</span>
                  <span className="font-mono">{getNewUrl()}</span>
                </div>
              </div>

              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  After restart, you'll be automatically redirected to the new URL.
                  If the connection fails, you can manually navigate to the server.
                </AlertDescription>
              </Alert>
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={() => onOpenChange(false)}>
                Cancel
              </Button>
              <Button onClick={handleApply}>
                <Zap className="mr-2 h-4 w-4" />
                Apply & Restart
              </Button>
            </DialogFooter>
          </>
        );

      case 'applying':
      case 'restarting':
      case 'reconnecting':
        return (
          <>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Loader2 className="h-5 w-5 animate-spin" />
                {state.phase === 'applying' && 'Applying Configuration'}
                {state.phase === 'restarting' && 'Restarting Server'}
                {state.phase === 'reconnecting' && 'Reconnecting'}
              </DialogTitle>
              <DialogDescription>
                Please wait while the server restarts with the new configuration.
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-6 py-6">
              <Progress value={state.progress} className="h-2" />

              <div className="text-center space-y-2">
                <p className="text-sm text-muted-foreground">{state.message}</p>
                {state.newUrl && (
                  <p className="text-xs text-muted-foreground">
                    Target: <span className="font-mono">{state.newUrl}</span>
                  </p>
                )}
              </div>

              {/* Progress steps */}
              <div className="space-y-2">
                <ProgressStep
                  label="Save configuration"
                  status={state.phase === 'applying' ? 'active' : 'complete'}
                />
                <ProgressStep
                  label="Restart server"
                  status={
                    state.phase === 'applying'
                      ? 'pending'
                      : state.phase === 'restarting'
                        ? 'active'
                        : 'complete'
                  }
                />
                <ProgressStep
                  label="Verify connection"
                  status={
                    state.phase === 'reconnecting' ? 'active' :
                    state.phase === 'applying' || state.phase === 'restarting' ? 'pending' : 'complete'
                  }
                />
              </div>
            </div>
          </>
        );

      case 'success':
        return (
          <>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2 text-green-600">
                <CheckCircle className="h-5 w-5" />
                Server Ready!
              </DialogTitle>
              <DialogDescription>
                The server has restarted successfully with the new configuration.
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-4">
              <Alert className="border-green-200 bg-green-50 dark:bg-green-950 dark:border-green-800">
                <CheckCircle className="h-4 w-4 text-green-600" />
                <AlertTitle className="text-green-800 dark:text-green-200">Connected</AlertTitle>
                <AlertDescription className="text-green-700 dark:text-green-300">
                  Successfully connected to the server at the new address.
                </AlertDescription>
              </Alert>

              <div className="flex items-center gap-2">
                <div className="flex-1 bg-muted rounded-md border px-4 py-3 font-mono text-sm">
                  {state.newUrl}
                </div>
                <Button variant="outline" size="icon" onClick={copyUrl}>
                  {copied ? (
                    <Check className="h-4 w-4 text-green-600" />
                  ) : (
                    <Copy className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>

            <DialogFooter>
              <Button onClick={handleContinue}>
                Continue
                <ExternalLink className="ml-2 h-4 w-4" />
              </Button>
            </DialogFooter>
          </>
        );

      case 'failure':
        return (
          <>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2 text-red-600">
                <AlertCircle className="h-5 w-5" />
                Connection Failed
              </DialogTitle>
              <DialogDescription>
                Could not connect to the server at the new address.
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-4">
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertTitle>Error</AlertTitle>
                <AlertDescription>{state.error}</AlertDescription>
              </Alert>

              {state.instructions && (
                <Alert>
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{state.instructions}</AlertDescription>
                </Alert>
              )}

              {state.newUrl && (
                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground">Target URL:</p>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 bg-muted rounded-md border px-4 py-3 font-mono text-sm">
                      {state.newUrl}
                    </div>
                    <Button variant="outline" size="icon" onClick={copyUrl}>
                      {copied ? (
                        <Check className="h-4 w-4 text-green-600" />
                      ) : (
                        <Copy className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                </div>
              )}
            </div>

            <DialogFooter className="flex-col sm:flex-row gap-2">
              <Button variant="outline" onClick={() => onOpenChange(false)}>
                Cancel
              </Button>
              <Button variant="outline" onClick={handleRetry}>
                <RefreshCw className="mr-2 h-4 w-4" />
                Retry Connection
              </Button>
              {state.newUrl && (
                <Button onClick={navigateToNewUrl}>
                  Open Manually
                  <ExternalLink className="ml-2 h-4 w-4" />
                </Button>
              )}
            </DialogFooter>
          </>
        );
    }
  };

  return (
    <Dialog open={open} onOpenChange={(isOpen) => {
      // Prevent closing during active phases
      if (state.phase === 'applying' || state.phase === 'restarting' || state.phase === 'reconnecting') {
        return;
      }
      onOpenChange(isOpen);
    }}>
      <DialogContent
        className="sm:max-w-md"
        onInteractOutside={(e) => {
          // Prevent closing by clicking outside during active phases
          if (state.phase === 'applying' || state.phase === 'restarting' || state.phase === 'reconnecting') {
            e.preventDefault();
          }
        }}
      >
        {renderContent()}
      </DialogContent>
    </Dialog>
  );
}

// Helper component for progress steps
interface ProgressStepProps {
  label: string;
  status: 'pending' | 'active' | 'complete';
}

function ProgressStep({ label, status }: ProgressStepProps) {
  return (
    <div className="flex items-center gap-3">
      <div className={`
        h-6 w-6 rounded-full flex items-center justify-center text-xs
        ${status === 'pending' ? 'bg-muted text-muted-foreground' : ''}
        ${status === 'active' ? 'bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-400' : ''}
        ${status === 'complete' ? 'bg-green-100 dark:bg-green-900 text-green-600 dark:text-green-400' : ''}
      `}>
        {status === 'active' && <Loader2 className="h-3 w-3 animate-spin" />}
        {status === 'complete' && <CheckCircle className="h-3 w-3" />}
        {status === 'pending' && <span className="text-[10px]">○</span>}
      </div>
      <span className={`text-sm ${status === 'pending' ? 'text-muted-foreground' : ''}`}>
        {label}
      </span>
    </div>
  );
}
