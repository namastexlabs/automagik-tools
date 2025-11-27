/**
 * Step 0: Mode Selection
 *
 * Choose between Local Mode (quick start) and Team Mode (WorkOS).
 */
import React from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Home, Users, Check } from 'lucide-react';

export interface Step0Data {
  mode: 'local' | 'workos' | null;
}

interface Step0Props {
  data: Step0Data;
  onUpdate: (data: Partial<Step0Data>) => void;
  onNext: () => void;
  isUpgrade?: boolean;
}

export function Step0_ModeSelection({ data, onUpdate, onNext, isUpgrade = false }: Step0Props) {
  const handleModeSelect = (mode: 'local' | 'workos') => {
    onUpdate({ mode });
    // Auto-advance to next step
    setTimeout(() => onNext(), 100);
  };

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold mb-2">
          {isUpgrade ? '🚀 Upgrade to Team Mode' : '⚙️ Welcome to Automagik Tools Hub'}
        </h2>
        <p className="text-muted-foreground">
          {isUpgrade
            ? 'Upgrade your workspace to team mode with WorkOS authentication'
            : 'Choose how you want to configure your Tools Hub'}
        </p>
      </div>

      <div className="grid gap-4 max-w-2xl mx-auto">
        {!isUpgrade && (
          <Card
            className="cursor-pointer transition-all hover:border-purple-500 hover:shadow-lg"
            onClick={() => handleModeSelect('local')}
          >
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-blue-100 dark:bg-blue-950 rounded-lg">
                    <Home className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                  </div>
                  <div>
                    <CardTitle className="text-xl">🏠 Local Mode</CardTitle>
                    <CardDescription className="mt-1">
                      Quick setup for personal use
                    </CardDescription>
                  </div>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-sm">
                <li className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-green-600" />
                  <span>API key authentication</span>
                </li>
                <li className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-green-600" />
                  <span>Persistent SQLite storage</span>
                </li>
                <li className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-green-600" />
                  <span>Perfect for testing and development</span>
                </li>
                <li className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-green-600" />
                  <span>Single admin user (full access)</span>
                </li>
              </ul>
            </CardContent>
          </Card>
        )}

        <Card
          className="cursor-pointer transition-all hover:border-purple-500 hover:shadow-lg"
          onClick={() => handleModeSelect('workos')}
        >
          <CardHeader>
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-purple-100 dark:bg-purple-950 rounded-lg">
                  <Users className="h-6 w-6 text-purple-600 dark:text-purple-400" />
                </div>
                <div>
                  <CardTitle className="text-xl">🏢 Team Mode</CardTitle>
                  <CardDescription className="mt-1">
                    Enterprise-grade multi-user workspace
                  </CardDescription>
                </div>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2 text-sm">
              <li className="flex items-center gap-2">
                <Check className="h-4 w-4 text-green-600" />
                <span>WorkOS SSO with MFA support</span>
              </li>
              <li className="flex items-center gap-2">
                <Check className="h-4 w-4 text-green-600" />
                <span>Directory sync (SCIM, Azure AD, Okta)</span>
              </li>
              <li className="flex items-center gap-2">
                <Check className="h-4 w-4 text-green-600" />
                <span>Audit logs and compliance</span>
              </li>
              <li className="flex items-center gap-2 text-amber-600 dark:text-amber-400">
                <span className="font-medium">⚠️ Irreversible (cannot downgrade)</span>
              </li>
            </ul>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
