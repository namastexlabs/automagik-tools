/**
 * Step 1b: WorkOS Configuration
 *
 * Configure WorkOS with Quick Start or Custom App options.
 */
import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import {
  Zap,
  Palette,
  AlertCircle,
  Info,
  CheckCircle,
  Loader2,
  ExternalLink,
  Mail,
  Key,
  Globe,
} from 'lucide-react';

export interface Step1bData {
  setupType: 'quick' | 'custom' | null;
  clientId: string;
  apiKey: string;
  authkitDomain: string;
  adminEmails: string;
}

interface Step1bProps {
  data: Step1bData;
  onUpdate: (data: Partial<Step1bData>) => void;
  onNext: () => void;
  onBack: () => void;
}

export function Step1b_WorkOSConfig({ data, onUpdate, onNext, onBack }: Step1bProps) {
  const [validating, setValidating] = useState(false);
  const [validationResult, setValidationResult] = useState<{
    valid: boolean;
    error?: string;
  } | null>(null);

  const handleSetupTypeSelect = (type: 'quick' | 'custom') => {
    onUpdate({ setupType: type });
  };

  const validateCredentials = async () => {
    if (!data.clientId || !data.apiKey || !data.authkitDomain) {
      setValidationResult({
        valid: false,
        error: 'Please fill in all required fields',
      });
      return;
    }

    setValidating(true);
    setValidationResult(null);

    try {
      const response = await fetch('/api/setup/workos/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          client_id: data.clientId,
          api_key: data.apiKey,
          authkit_domain: data.authkitDomain,
        }),
      });

      const result = await response.json();
      setValidationResult(result);

      if (result.valid) {
        // Auto-advance if all fields are valid
        setTimeout(() => handleNext(), 500);
      }
    } catch (err) {
      setValidationResult({
        valid: false,
        error: err instanceof Error ? err.message : 'Validation failed',
      });
    } finally {
      setValidating(false);
    }
  };

  const handleNext = () => {
    const emails = data.adminEmails
      .split(',')
      .map((e) => e.trim())
      .filter(Boolean);

    if (emails.length === 0) {
      setValidationResult({
        valid: false,
        error: 'Please enter at least one admin email',
      });
      return;
    }

    if (!data.clientId || !data.apiKey || !data.authkitDomain) {
      setValidationResult({
        valid: false,
        error: 'Please fill in all WorkOS credentials',
      });
      return;
    }

    onNext();
  };

  // Show setup type selection if not chosen
  if (!data.setupType) {
    return (
      <div className="space-y-6 max-w-2xl mx-auto">
        <div className="text-center">
          <h2 className="text-2xl font-bold mb-2">🏢 WorkOS Setup</h2>
          <p className="text-muted-foreground">
            Choose your WorkOS integration approach
          </p>
        </div>

        <div className="grid gap-4">
          <div
            className="border rounded-lg p-6 cursor-pointer transition-all hover:border-purple-500 hover:shadow-lg"
            onClick={() => handleSetupTypeSelect('quick')}
          >
            <div className="flex items-start gap-4">
              <div className="p-3 bg-yellow-100 dark:bg-yellow-950 rounded-lg">
                <Zap className="h-6 w-6 text-yellow-600 dark:text-yellow-400" />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <h3 className="text-lg font-semibold">⚡ Quick Start</h3>
                  <Badge variant="outline" className="text-xs">Recommended</Badge>
                </div>
                <p className="text-sm text-muted-foreground mb-3">
                  Use WorkOS managed authentication UI. Zero frontend code required.
                </p>
                <ul className="space-y-1 text-sm">
                  <li className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <span>Hosted login page</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <span>Automatic updates</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <span>5-minute setup</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>

          <div
            className="border rounded-lg p-6 cursor-pointer transition-all hover:border-purple-500 hover:shadow-lg"
            onClick={() => handleSetupTypeSelect('custom')}
          >
            <div className="flex items-start gap-4">
              <div className="p-3 bg-purple-100 dark:bg-purple-950 rounded-lg">
                <Palette className="h-6 w-6 text-purple-600 dark:text-purple-400" />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <h3 className="text-lg font-semibold">🎨 Custom App</h3>
                  <Badge variant="outline" className="text-xs">Advanced</Badge>
                </div>
                <p className="text-sm text-muted-foreground mb-3">
                  Integrate WorkOS into your own custom authentication UI.
                </p>
                <ul className="space-y-1 text-sm">
                  <li className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <span>Full UI control</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <span>Custom branding</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <AlertCircle className="h-4 w-4 text-amber-500" />
                    <span>Requires frontend development</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        <div className="flex gap-3 justify-between pt-4">
          <Button variant="outline" onClick={onBack}>
            Back
          </Button>
        </div>
      </div>
    );
  }

  // Show credentials form
  return (
    <div className="space-y-6 max-w-2xl mx-auto">
      <div className="text-center">
        <h2 className="text-2xl font-bold mb-2">
          {data.setupType === 'quick' ? '⚡ Quick Start Setup' : '🎨 Custom App Setup'}
        </h2>
        <p className="text-muted-foreground">
          Enter your WorkOS credentials
        </p>
      </div>

      <div className="space-y-4">
        {/* Setup Type Badge */}
        <div className="flex items-center justify-center gap-2">
          <Badge variant="outline" className="text-sm">
            {data.setupType === 'quick' ? '⚡ Quick Start' : '🎨 Custom App'}
          </Badge>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onUpdate({ setupType: null })}
          >
            Change
          </Button>
        </div>

        {/* Instructions */}
        <Alert>
          <Info className="h-4 w-4" />
          <AlertDescription>
            <p className="mb-2">Get your credentials from WorkOS Dashboard:</p>
            <a
              href="https://dashboard.workos.com/get-started"
              target="_blank"
              rel="noopener noreferrer"
              className="text-purple-600 dark:text-purple-400 hover:underline inline-flex items-center gap-1"
            >
              Open WorkOS Dashboard
              <ExternalLink className="h-3 w-3" />
            </a>
          </AlertDescription>
        </Alert>

        <Separator />

        {/* Client ID */}
        <div className="space-y-2">
          <Label htmlFor="client-id" className="flex items-center gap-2">
            <Key className="h-4 w-4" />
            Client ID
          </Label>
          <Input
            id="client-id"
            placeholder="client_..."
            value={data.clientId}
            onChange={(e) => onUpdate({ clientId: e.target.value })}
            className="font-mono"
          />
          <p className="text-xs text-muted-foreground">
            Found in Dashboard → Settings → Environment
          </p>
        </div>

        {/* API Key */}
        <div className="space-y-2">
          <Label htmlFor="api-key" className="flex items-center gap-2">
            <Key className="h-4 w-4" />
            API Key
          </Label>
          <Input
            id="api-key"
            type="password"
            placeholder="sk_..."
            value={data.apiKey}
            onChange={(e) => onUpdate({ apiKey: e.target.value })}
            className="font-mono"
          />
          <p className="text-xs text-muted-foreground">
            Found in Dashboard → Settings → API Keys
          </p>
        </div>

        {/* AuthKit Domain */}
        <div className="space-y-2">
          <Label htmlFor="authkit-domain" className="flex items-center gap-2">
            <Globe className="h-4 w-4" />
            AuthKit Domain
          </Label>
          <Input
            id="authkit-domain"
            placeholder="https://auth.example.com"
            value={data.authkitDomain}
            onChange={(e) => onUpdate({ authkitDomain: e.target.value })}
            className="font-mono"
          />
          <p className="text-xs text-muted-foreground">
            {data.setupType === 'quick'
              ? 'Found in Dashboard → Authentication → AuthKit → Configuration'
              : 'Your custom authentication domain'}
          </p>
        </div>

        <Separator />

        {/* Admin Emails */}
        <div className="space-y-2">
          <Label htmlFor="admin-emails" className="flex items-center gap-2">
            <Mail className="h-4 w-4" />
            Super Admin Emails
          </Label>
          <Input
            id="admin-emails"
            placeholder="admin1@example.com, admin2@example.com"
            value={data.adminEmails}
            onChange={(e) => onUpdate({ adminEmails: e.target.value })}
          />
          <p className="text-sm text-muted-foreground">
            Comma-separated list of email addresses with full admin access
          </p>
        </div>

        {/* Validation Result */}
        {validationResult && (
          <Alert variant={validationResult.valid ? 'default' : 'destructive'}>
            {validationResult.valid ? (
              <CheckCircle className="h-4 w-4 text-green-600" />
            ) : (
              <AlertCircle className="h-4 w-4" />
            )}
            <AlertDescription>
              {validationResult.valid
                ? 'Credentials validated successfully!'
                : validationResult.error || 'Validation failed'}
            </AlertDescription>
          </Alert>
        )}

        {/* Irreversible Warning */}
        <Alert>
          <AlertCircle className="h-4 w-4 text-amber-500" />
          <AlertDescription className="text-amber-600 dark:text-amber-400">
            <strong>Warning:</strong> WorkOS mode is irreversible. You cannot downgrade to local mode after setup.
          </AlertDescription>
        </Alert>
      </div>

      {/* Navigation */}
      <div className="flex gap-3 justify-between pt-4">
        <Button variant="outline" onClick={onBack} disabled={validating}>
          Back
        </Button>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={validateCredentials}
            disabled={validating || !data.clientId || !data.apiKey || !data.authkitDomain}
          >
            {validating ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Validating...
              </>
            ) : (
              'Validate'
            )}
          </Button>
          <Button onClick={handleNext} disabled={validating}>
            Next
          </Button>
        </div>
      </div>
    </div>
  );
}
