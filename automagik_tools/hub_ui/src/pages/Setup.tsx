import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, CheckCircle, AlertCircle } from 'lucide-react';

export default function Setup() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [mode, setMode] = useState<'local' | 'workos' | null>(null);
  const [localEmail, setLocalEmail] = useState('');
  const [workosClientId, setWorkosClientId] = useState('');
  const [workosApiKey, setWorkosApiKey] = useState('');
  const [workosAuthkitDomain, setWorkosAuthkitDomain] = useState('');
  const [workosAdminEmails, setWorkosAdminEmails] = useState('');

  const isUpgrade = searchParams.get('mode') === 'upgrade';

  useEffect(() => {
    // Check if setup is already complete
    fetch('/api/setup/status')
      .then(res => res.json())
      .then(data => {
        if (!data.is_setup_required && !isUpgrade) {
          // Already configured, redirect to dashboard
          navigate('/dashboard');
        }
      })
      .catch(console.error);
  }, [navigate, isUpgrade]);

  const handleLocalSetup = async () => {
    if (!localEmail) {
      setError('Please enter an admin email');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch('/api/setup/local', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ admin_email: localEmail })
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Setup failed');
      }

      // Redirect to dashboard
      window.location.href = '/app/dashboard';
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleWorkOSSetup = async () => {
    if (!workosClientId || !workosApiKey || !workosAuthkitDomain || !workosAdminEmails) {
      setError('Please fill in all WorkOS fields');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const adminEmailsArray = workosAdminEmails.split(',').map(e => e.trim()).filter(Boolean);

      const endpoint = isUpgrade ? '/api/setup/upgrade-to-workos' : '/api/setup/workos';
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          client_id: workosClientId,
          api_key: workosApiKey,
          authkit_domain: workosAuthkitDomain,
          super_admin_emails: adminEmailsArray
        })
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Setup failed');
      }

      // Redirect to login
      window.location.href = '/app/login';
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (mode === null) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-600 to-purple-900 flex items-center justify-center p-4">
        <Card className="w-full max-w-lg">
          <CardHeader>
            <CardTitle className="text-2xl">
              {isUpgrade ? '🚀 Upgrade to Team Mode' : '⚙️ Setup Automagik Tools Hub'}
            </CardTitle>
            <CardDescription>
              {isUpgrade
                ? 'Upgrade your workspace to team mode with WorkOS authentication'
                : 'Choose how you want to configure your Tools Hub'}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {!isUpgrade && (
              <Button
                onClick={() => setMode('local')}
                className="w-full justify-start h-auto py-4"
                variant="outline"
              >
                <div className="text-left">
                  <div className="font-semibold">🏠 Local Mode</div>
                  <div className="text-sm text-muted-foreground mt-1">
                    Single admin, passwordless access (not persistent between restarts)
                  </div>
                </div>
              </Button>
            )}
            <Button
              onClick={() => setMode('workos')}
              className="w-full justify-start h-auto py-4"
              variant="outline"
            >
              <div className="text-left">
                <div className="font-semibold">🏢 Team Mode</div>
                <div className="text-sm text-muted-foreground mt-1">
                  Multi-user workspace with WorkOS SSO, MFA & directory sync (irreversible)
                </div>
              </div>
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (mode === 'local') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-600 to-purple-900 flex items-center justify-center p-4">
        <Card className="w-full max-w-lg">
          <CardHeader>
            <CardTitle className="text-2xl">🏠 Local Mode Setup</CardTitle>
            <CardDescription>
              Quick setup for personal use. No password required.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <div className="space-y-2">
              <Label htmlFor="email">Admin Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="admin@example.com"
                value={localEmail}
                onChange={(e) => setLocalEmail(e.target.value)}
                disabled={loading}
              />
              <p className="text-sm text-muted-foreground">
                This email will be used for identification only. No password needed.
              </p>
            </div>

            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                Local mode is not persistent. Your configuration will reset on server restart.
              </AlertDescription>
            </Alert>
          </CardContent>
          <CardFooter className="flex gap-2">
            <Button variant="outline" onClick={() => setMode(null)} disabled={loading}>
              Back
            </Button>
            <Button onClick={handleLocalSetup} disabled={loading} className="flex-1">
              {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Complete Setup
            </Button>
          </CardFooter>
        </Card>
      </div>
    );
  }

  if (mode === 'workos') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-600 to-purple-900 flex items-center justify-center p-4">
        <Card className="w-full max-w-lg">
          <CardHeader>
            <CardTitle className="text-2xl">
              {isUpgrade ? '🚀 Upgrade to Team Mode' : '🏢 Team Mode Setup'}
            </CardTitle>
            <CardDescription>
              Configure WorkOS for enterprise authentication
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <div className="space-y-2">
              <Label htmlFor="clientId">WorkOS Client ID</Label>
              <Input
                id="clientId"
                placeholder="client_..."
                value={workosClientId}
                onChange={(e) => setWorkosClientId(e.target.value)}
                disabled={loading}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="apiKey">WorkOS API Key</Label>
              <Input
                id="apiKey"
                type="password"
                placeholder="sk_..."
                value={workosApiKey}
                onChange={(e) => setWorkosApiKey(e.target.value)}
                disabled={loading}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="authkitDomain">AuthKit Domain</Label>
              <Input
                id="authkitDomain"
                placeholder="https://auth.example.com"
                value={workosAuthkitDomain}
                onChange={(e) => setWorkosAuthkitDomain(e.target.value)}
                disabled={loading}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="adminEmails">Super Admin Emails</Label>
              <Input
                id="adminEmails"
                placeholder="admin1@example.com, admin2@example.com"
                value={workosAdminEmails}
                onChange={(e) => setWorkosAdminEmails(e.target.value)}
                disabled={loading}
              />
              <p className="text-sm text-muted-foreground">
                Comma-separated list of super admin email addresses
              </p>
            </div>

            <Alert>
              <AlertCircle className="h-4 w-4 text-amber-500" />
              <AlertDescription className="text-amber-600 dark:text-amber-400">
                This configuration is <strong>irreversible</strong>. You cannot downgrade to local mode.
              </AlertDescription>
            </Alert>
          </CardContent>
          <CardFooter className="flex gap-2">
            {!isUpgrade && (
              <Button variant="outline" onClick={() => setMode(null)} disabled={loading}>
                Back
              </Button>
            )}
            <Button onClick={handleWorkOSSetup} disabled={loading} className="flex-1">
              {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {isUpgrade ? 'Upgrade Now' : 'Complete Setup'}
            </Button>
          </CardFooter>
        </Card>
      </div>
    );
  }

  return null;
}
