/**
 * Step 2: Network Configuration
 *
 * Configure bind address and port with conflict detection.
 */
import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import {
  Network,
  Wifi,
  Lock,
  AlertCircle,
  CheckCircle,
  Loader2,
  Info,
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
  }>;
  suggestions: number[];
}

export function Step2_NetworkConfig({ data, onUpdate, onNext, onBack }: Step2Props) {
  const [testing, setTesting] = useState(false);
  const [portStatus, setPortStatus] = useState<PortTestResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Test port on mount and when port changes
  useEffect(() => {
    const timer = setTimeout(() => {
      testPort(data.port);
    }, 500);
    return () => clearTimeout(timer);
  }, [data.port]);

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

  const canProceed = portStatus?.available === true;

  return (
    <div className="space-y-6 max-w-2xl mx-auto">
      <div className="text-center">
        <h2 className="text-2xl font-bold mb-2">🌐 Network Configuration</h2>
        <p className="text-muted-foreground">
          Configure how the Hub will be accessible
        </p>
      </div>

      <div className="space-y-4">
        {/* Bind Address Selection */}
        <div className="space-y-3">
          <Label>Bind Address</Label>

          <div className="grid grid-cols-2 gap-3">
            <Button
              variant={data.bindAddress === 'localhost' ? 'default' : 'outline'}
              className="h-auto py-4 flex-col items-start"
              onClick={() => onUpdate({ bindAddress: 'localhost' })}
            >
              <div className="flex items-center gap-2 mb-1">
                <Lock className="h-4 w-4" />
                <span className="font-semibold">Localhost</span>
              </div>
              <span className="text-xs text-left">
                127.0.0.1 - Local machine only
              </span>
            </Button>

            <Button
              variant={data.bindAddress === 'network' ? 'default' : 'outline'}
              className="h-auto py-4 flex-col items-start"
              onClick={() => onUpdate({ bindAddress: 'network' })}
            >
              <div className="flex items-center gap-2 mb-1">
                <Network className="h-4 w-4" />
                <span className="font-semibold">Network</span>
              </div>
              <span className="text-xs text-left">
                0.0.0.0 - All network interfaces
              </span>
            </Button>
          </div>

          <Alert>
            <Info className="h-4 w-4" />
            <AlertDescription>
              {data.bindAddress === 'localhost' ? (
                <>
                  <strong>Recommended for security.</strong> Hub will only be accessible from this machine.
                </>
              ) : (
                <>
                  <strong>Use with caution.</strong> Hub will be accessible from other devices on your network.
                  Only use if you understand the security implications.
                </>
              )}
            </AlertDescription>
          </Alert>
        </div>

        <Separator />

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
              className="font-mono"
            />

            {testing && (
              <div className="flex items-center px-3">
                <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
              </div>
            )}

            {!testing && portStatus?.available && (
              <div className="flex items-center px-3">
                <CheckCircle className="h-5 w-5 text-green-600" />
              </div>
            )}

            {!testing && portStatus && !portStatus.available && (
              <div className="flex items-center px-3">
                <AlertCircle className="h-5 w-5 text-red-600" />
              </div>
            )}
          </div>

          {/* Port Status Messages */}
          {!testing && portStatus && (
            <>
              {portStatus.available ? (
                <Alert>
                  <CheckCircle className="h-4 w-4 text-green-600" />
                  <AlertDescription className="text-green-600 dark:text-green-400">
                    Port {data.port} is available
                  </AlertDescription>
                </Alert>
              ) : (
                <>
                  <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>
                      Port {data.port} is already in use
                      {portStatus.conflicts.length > 0 && (
                        <>
                          {' '}by{' '}
                          <strong>{portStatus.conflicts[0].process}</strong>
                          {portStatus.conflicts[0].command && (
                            <div className="mt-1 font-mono text-xs">
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
                        Try these available ports:
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
                </>
              )}
            </>
          )}

          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
        </div>

        <Separator />

        {/* Connection URL Preview */}
        <div className="bg-muted/50 rounded-md p-4 space-y-2">
          <Label className="text-xs text-muted-foreground">Hub will be accessible at:</Label>
          <div className="font-mono text-sm">
            http://{data.bindAddress === 'localhost' ? '127.0.0.1' : '<your-ip>'}:{data.port}
          </div>
        </div>
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
