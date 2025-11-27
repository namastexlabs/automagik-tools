import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { isAuthenticated } from '@/lib/api';
import { setUserInfo, type UserInfo } from '@/lib/auth';

export default function Login() {
  const [searchParams] = useSearchParams();
  const [error, setError] = useState('');
  const navigate = useNavigate();

  // Check if already authenticated
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
      return;
    }

    if (code) {
      handleOAuthCallback(code);
    } else {
      // No code and not authenticated - redirect to WorkOS immediately
      redirectToWorkOS();
    }
  }, [searchParams]);

  const handleOAuthCallback = async (code: string) => {
    try {
      const response = await fetch('/api/auth/callback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code }),
        credentials: 'include',  // Receive HTTP-only session cookie
      });

      if (!response.ok) {
        const error = await response.text();
        throw new Error(error || 'Failed to authenticate');
      }

      const data = await response.json();

      // Session cookie set automatically by server - no client-side token storage needed

      if (data.user) {
        const userInfo: UserInfo = {
          id: data.user.id,
          email: data.user.email,
          first_name: data.user.first_name,
          last_name: data.user.last_name,
          workspace_id: data.user.workspace_id,
          workspace_name: data.user.workspace_name,
          workspace_slug: data.user.workspace_slug,
          is_super_admin: data.user.is_super_admin || false,
          mfa_enabled: data.user.mfa_enabled || false,
        };
        setUserInfo(userInfo);
      }

      navigate('/dashboard');
    } catch (err) {
      console.error('[Login] OAuth callback error:', err);
      setError(err instanceof Error ? err.message : 'Authentication failed');
    }
  };

  const redirectToWorkOS = async () => {
    try {
      const response = await fetch('/api/auth/authorize');

      if (!response.ok) {
        throw new Error('Failed to initiate authentication');
      }

      const { authorization_url } = await response.json();
      window.location.href = authorization_url;
    } catch (err) {
      console.error('[Login] Error initiating login:', err);
      setError(err instanceof Error ? err.message : 'Failed to initiate authentication');
    }
  };

  // Show error if present, otherwise just a loading state
  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-destructive/10 border border-destructive/20 text-destructive p-6 rounded-lg">
          <h2 className="text-lg font-semibold mb-2">Authentication Error</h2>
          <p className="text-sm">{error}</p>
          <button
            onClick={() => redirectToWorkOS()}
            className="mt-4 w-full bg-destructive text-destructive-foreground px-4 py-2 rounded-md hover:bg-destructive/90"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="h-12 w-12 rounded-full border-4 border-primary/20 border-t-primary animate-spin"></div>
    </div>
  );
}
