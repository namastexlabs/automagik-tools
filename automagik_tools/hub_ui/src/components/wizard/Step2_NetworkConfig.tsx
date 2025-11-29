/**
 * Step 2: Network Configuration
 *
 * Zero-config approach: Default port 8884 works out of the box.
 * Advanced settings (port, bind address) collapsed by default.
 */
import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import {
  Network,
  Lock,
  AlertCircle,
  CheckCircle,
  Loader2,
  ChevronDown,
  ChevronRight,
  Copy,
  Check,
} from 'lucide-react';

export interface Step2Data {
  bindAddress: 'localhost' | 'network';
  port: number;
}

interface Step2Props {
  data: Step2Data;
  onUpdate: (data: Partial<Step2Data>) => void;
  onNext: () => void;
  onBack: () => void;
}

interface PortTestResult {
  available: boolean;
  conflicts: Array<{
    pid: number;
    process: string;
    command?: string;
    is_self?: boolean;  // True if this is the wizard itself
  }>;
  suggestions: number[];
}

const DEFAULT_PORT = 8884;

export function Step2_NetworkConfig({ data, onUpdate, onNext, onBack }: Step2Props) {
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const [testing, setTesting] = useState(false);
  const [portStatus, setPortStatus] = useState<PortTestResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  // Only test port when advanced is open and port changes
  useEffect(() => {
    if (!advancedOpen) {
      // When advanced is closed, assume default port is available
      setPortStatus({ available: true, conflicts: [], suggestions: [] });
      return;
    }

    const timer = setTimeout(() => {
      testPort(data.port);
    }, 500);
    return () => clearTimeout(timer);
  }, [data.port, advancedOpen]);

  // Test default port on mount
  useEffect(() => {
    testPort(data.port);
  }, []);

  const testPort = async (port: number) => {
    if (port < 1024 || port > 65535) {
      setPortStatus(null);
      setError('Port must be between 1024 and 65535');
      return;
    }

    setTesting(true);
    setError(null);

    try {
      const response = await fetch('/api/network/test-port', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ port }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to test port');
      }

      const result: PortTestResult = await response.json();
      setPortStatus(result);

      // Only auto-open advanced if there's a REAL conflict (not ourselves)
      const allConflictsAreSelf = result.conflicts.length > 0 &&
        result.conflicts.every(c => c.is_self === true);

      if (!result.available && !advancedOpen && !allConflictsAreSelf) {
        setAdvancedOpen(true);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to test port');
      setPortStatus(null);
    } finally {
      setTesting(false);
    }
  };

  const handlePortChange = (value: string) => {
    const port = parseInt(value);
    if (!isNaN(port)) {
      onUpdate({ port });
    }
  };

  const handleNext = () => {
    if (portStatus?.available) {
      onNext();
    }
  };

  const getHubUrl = () => {
    const host = data.bindAddress === 'localhost' ? 'localhost' : '0.0.0.0';
    return `http://${host}:${data.port}`;
  };

  const copyUrl = async () => {
    try {
      await navigator.clipboard.writeText(getHubUrl());
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      // Fallback for older browsers
      const textArea = document.createElement('textarea');
      textArea.value = getHubUrl();
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  // Allow proceeding if port is available OR if ALL conflicts are ourselves (the wizard)
  const isSelfConflict = portStatus?.conflicts?.length > 0 &&
    portStatus.conflicts.every(c => c.is_self === true);
  const canProceed = portStatus?.available === true || isSelfConflict;
  const isDefaultConfig = data.port === DEFAULT_PORT && data.bindAddress === 'localhost';

  return (
    <div className="space-y-6 max-w-2xl mx-auto">
      {/* Header */}
      <div className="text-center">
        <h2 className="text-2xl font-bold mb-2">🌐 Network Configuration</h2>
        <p className="text-muted-foreground">
          Configure how the Hub will be accessible
        </p>
      </div>

      {/* Main Content */}
      <div className="space-y-4">
        {/* Hub URL Preview - Always Visible */}
        <div className="bg-muted/50 rounded-lg p-6 space-y-3">
          <Label className="text-sm text-muted-foreground">Hub will be accessible at:</Label>

          <div className="flex items-center gap-2">
            <div className="flex-1 bg-background rounded-md border px-4 py-3 font-mono text-sm">
              {getHubUrl()}
            </div>
            <Button
              variant="outline"
              size="icon"
              onClick={copyUrl}
              title="Copy URL"
            >
              {copied ? (
                <Check className="h-4 w-4 text-green-600" />
              ) : (
                <Copy className="h-4 w-4" />
              )}
            </Button>
          </div>

          {/* Status indicator */}
          <div className="flex items-center gap-2 text-sm">
            {testing ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                <span className="text-muted-foreground">Checking port availability...</span>
              </>
            ) : portStatus?.available ? (
              <>
                <CheckCircle className="h-4 w-4 text-green-600" />
                <span className="text-green-600 dark:text-green-400">
                  {isDefaultConfig
                    ? 'Default settings work for most users'
                    : `Port ${data.port} is available`}
                </span>
              </>
            ) : isSelfConflict ? (
              <>
                <CheckCircle className="h-4 w-4 text-green-600" />
                <span className="text-green-600 dark:text-green-400">
                  Port {data.port} is ready (used by this setup wizard)
                </span>
              </>
            ) : portStatus && !portStatus.available ? (
              <>
                <AlertCircle className="h-4 w-4 text-red-600" />
                <span className="text-red-600">
                  Port {data.port} is in use
                  {portStatus.conflicts[0]?.process && (
                    <> by {portStatus.conflicts[0].process}</>
                  )}
                </span>
              </>
            ) : null}
          </div>
        </div>

        {/* Advanced Settings - Collapsed by Default */}
        <Collapsible open={advancedOpen} onOpenChange={setAdvancedOpen}>
          <CollapsibleTrigger asChild>
            <Button
              variant="ghost"
              className="w-full justify-start text-muted-foreground hover:text-foreground"
            >
              {advancedOpen ? (
                <ChevronDown className="h-4 w-4 mr-2" />
              ) : (
                <ChevronRight className="h-4 w-4 mr-2" />
              )}
              Advanced Settings
            </Button>
          </CollapsibleTrigger>

          <CollapsibleContent className="space-y-4 pt-4">
            {/* Bind Address Selection */}
            <div className="space-y-3">
              <Label>Who can access the Hub?</Label>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <Button
                  variant={data.bindAddress === 'localhost' ? 'default' : 'outline'}
                  className="h-auto py-4 flex-col items-start text-left"
                  onClick={() => onUpdate({ bindAddress: 'localhost' })}
                >
                  <div className="flex items-center gap-2 mb-1">
                    <Lock className="h-4 w-4" />
                    <span className="font-semibold">Just This Computer</span>
                  </div>
                  <span className="text-xs opacity-80">
                    Most secure. Only you can access.
                  </span>
                </Button>

                <Button
                  variant={data.bindAddress === 'network' ? 'default' : 'outline'}
                  className="h-auto py-4 flex-col items-start text-left"
                  onClick={() => onUpdate({ bindAddress: 'network' })}
                >
                  <div className="flex items-center gap-2 mb-1">
                    <Network className="h-4 w-4" />
                    <span className="font-semibold">Other Devices on Network</span>
                  </div>
                  <span className="text-xs opacity-80">
                    Allow phones, tablets, other computers.
                  </span>
                </Button>
              </div>

              {data.bindAddress === 'network' && (
                <Alert>
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    <strong>Security warning:</strong> Hub will be accessible from any device on your network.
                    Make sure your network is trusted.
                  </AlertDescription>
                </Alert>
              )}
            </div>

            {/* Port Configuration */}
            <div className="space-y-3">
              <Label htmlFor="port">Port</Label>

              <div className="flex gap-2">
                <Input
                  id="port"
                  type="number"
                  value={data.port}
                  onChange={(e) => handlePortChange(e.target.value)}
                  min={1024}
                  max={65535}
                  className="font-mono max-w-32"
                />

                {testing && (
                  <div className="flex items-center px-3">
                    <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                  </div>
                )}

                {!testing && (portStatus?.available || isSelfConflict) && (
                  <div className="flex items-center px-3">
                    <CheckCircle className="h-5 w-5 text-green-600" />
                  </div>
                )}

                {!testing && portStatus && !portStatus.available && !isSelfConflict && (
                  <div className="flex items-center px-3">
                    <AlertCircle className="h-5 w-5 text-red-600" />
                  </div>
                )}
              </div>

              {/* Port Conflict Details */}
              {!testing && portStatus && !portStatus.available && !isSelfConflict && (
                <div className="space-y-3">
                  <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>
                      Port {data.port} is already in use
                      {portStatus.conflicts.length > 0 && (
                        <>
                          {' '}by <strong>{portStatus.conflicts[0].process}</strong>
                          {portStatus.conflicts[0].command && (
                            <div className="mt-1 font-mono text-xs truncate">
                              {portStatus.conflicts[0].command}
                            </div>
                          )}
                        </>
                      )}
                    </AlertDescription>
                  </Alert>

                  {portStatus.suggestions.length > 0 && (
                    <div className="space-y-2">
                      <p className="text-sm text-muted-foreground">
                        Try one of these available ports:
                      </p>
                      <div className="flex gap-2 flex-wrap">
                        {portStatus.suggestions.map((port) => (
                          <Button
                            key={port}
                            variant="outline"
                            size="sm"
                            onClick={() => onUpdate({ port })}
                            className="font-mono"
                          >
                            {port}
                          </Button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Self-conflict info (when wizard detects itself) */}
              {!testing && isSelfConflict && (
                <Alert>
                  <CheckCircle className="h-4 w-4 text-green-600" />
                  <AlertDescription>
                    This port is currently used by the setup wizard itself.
                    After setup completes, the Hub will take over this port seamlessly.
                  </AlertDescription>
                </Alert>
              )}

              {error && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}
            </div>
          </CollapsibleContent>
        </Collapsible>
      </div>

      {/* Navigation */}
      <div className="flex gap-3 justify-between pt-4">
        <Button variant="outline" onClick={onBack}>
          Back
        </Button>
        <Button onClick={handleNext} disabled={!canProceed}>
          Next
        </Button>
      </div>
    </div>
  );
}
