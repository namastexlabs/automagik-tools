import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { setAccessToken, isAuthenticated } from '@/lib/api';
import { Package, Lock, Loader2 } from 'lucide-react';

export default function Login() {
  const [searchParams] = useSearchParams();
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  // Check if already authenticated on mount
  useEffect(() => {
    if (isAuthenticated()) {
      navigate('/dashboard');
    }
  }, [navigate]);

  // Handle OAuth callback
  useEffect(() => {
    const code = searchParams.get('code');
    const errorParam = searchParams.get('error');
    const errorDescription = searchParams.get('error_description');

    if (errorParam) {
      setError(errorDescription || 'Authentication failed');
      setLoading(false);
      return;
    }

    if (code) {
      handleOAuthCallback(code);
    }
  }, [searchParams]);

  const handleOAuthCallback = async (code: string) => {
    setLoading(true);
    setError('');

    try {
      // Exchange code for access token
      const response = await fetch('/api/auth/callback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ code }),
      });

      if (!response.ok) {
        const error = await response.text();
        throw new Error(error || 'Failed to authenticate');
      }

      const { access_token } = await response.json();

      // Store token and navigate to dashboard
      setAccessToken(access_token);
      navigate('/dashboard');
    } catch (err) {
      console.error('[Login] OAuth callback error:', err);
      setError(err instanceof Error ? err.message : 'Authentication failed');
      setLoading(false);
    }
  };

  const handleLogin = async () => {
    setLoading(true);
    setError('');

    try {
      // Get WorkOS AuthKit authorization URL from backend
      const response = await fetch('/api/auth/authorize');

      if (!response.ok) {
        throw new Error('Failed to initiate authentication');
      }

      const { authorization_url } = await response.json();

      // Redirect to WorkOS AuthKit
      window.location.href = authorization_url;
    } catch (err) {
      console.error('[Login] Error initiating login:', err);
      setError(err instanceof Error ? err.message : 'Failed to initiate authentication');
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden bg-gradient-to-br from-primary/10 via-background to-secondary/10">
      {/* Animated gradient background */}
      <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiNmZmZmZmYiIGZpbGwtb3BhY2l0eT0iMC4wNSI+PHBhdGggZD0iTTM2IDM0YzAtMiAyLTQgMi00czIgMiAyIDR2MTBjMCAyLTIgNC0yIDRzLTItMi0yLTR2LTEweiIvPjwvZz48L2c+PC9zdmc+')] opacity-50"></div>

      {/* Floating orbs for depth */}
      <div className="absolute top-20 left-20 w-72 h-72 bg-primary/20 rounded-full mix-blend-multiply filter blur-3xl opacity-50 animate-pulse"></div>
      <div className="absolute bottom-20 right-20 w-72 h-72 bg-secondary/20 rounded-full mix-blend-multiply filter blur-3xl opacity-50 animate-pulse"></div>

      {/* Login card */}
      <Card className="w-full max-w-md relative z-10 shadow-2xl">
        <CardHeader className="space-y-3 text-center pb-6">
          <div className="flex justify-center mb-2">
            <div className="relative">
              <div className="h-16 w-16 rounded-2xl bg-primary flex items-center justify-center shadow-lg">
                <Package className="h-8 w-8 text-primary-foreground" />
              </div>
              <div className="absolute -top-1 -right-1 h-6 w-6 bg-success rounded-full border-4 border-card flex items-center justify-center">
                <div className="h-2 w-2 bg-white rounded-full animate-pulse"></div>
              </div>
            </div>
          </div>
          <CardTitle className="text-3xl font-bold">
            Automagik Tools Hub
          </CardTitle>
          <CardDescription className="text-base">
            Your personal MCP tool collection
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {error && (
            <div className="flex items-center gap-2 text-sm text-destructive bg-destructive/10 p-3 rounded-lg border border-destructive/20">
              <svg className="h-4 w-4 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              {error}
            </div>
          )}

          <Button
            onClick={handleLogin}
            className="w-full h-12 text-base font-semibold"
            disabled={loading}
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <Loader2 className="h-5 w-5 animate-spin" />
                {searchParams.get('code') ? 'Completing sign in...' : 'Redirecting...'}
              </span>
            ) : (
              <span className="flex items-center gap-2">
                <Lock className="h-5 w-5" />
                Sign In with WorkOS
              </span>
            )}
          </Button>

          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-card px-2 text-muted-foreground">Secure Authentication</span>
            </div>
          </div>

          <div className="space-y-2 text-xs text-center text-muted-foreground bg-muted/50 p-4 rounded-lg">
            <div className="flex items-center justify-center gap-2">
              <Lock className="h-3 w-3" />
              <span className="font-medium">Enterprise-grade security</span>
            </div>
            <p>
              Powered by WorkOS AuthKit for secure, reliable authentication.
              Your credentials are never stored on our servers.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
