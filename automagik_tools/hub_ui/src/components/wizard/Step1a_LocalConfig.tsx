/**
 * Step 1a: Local Mode Configuration
 *
 * Configure local admin and database path.
 */
import React from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { FolderPicker } from '@/components/FolderPicker';
import { Info, AlertCircle } from 'lucide-react';

export interface Step1aData {
  adminEmail: string;
  databasePath: string;
}

interface Step1aProps {
  data: Step1aData;
  onUpdate: (data: Partial<Step1aData>) => void;
  onNext: () => void;
  onBack: () => void;
}

export function Step1a_LocalConfig({ data, onUpdate, onNext, onBack }: Step1aProps) {
  const handleNext = () => {
    if (data.adminEmail && data.databasePath) {
      onNext();
    }
  };

  const isValidEmail = data.adminEmail.includes('@');
  const canProceed = data.adminEmail && isValidEmail && data.databasePath;

  return (
    <div className="space-y-6 max-w-2xl mx-auto">
      <div className="text-center">
        <h2 className="text-2xl font-bold mb-2">🏠 Local Mode Configuration</h2>
        <p className="text-muted-foreground">
          Quick setup for personal use. No password required.
        </p>
      </div>

      <div className="space-y-4">
        {/* Admin Email */}
        <div className="space-y-2">
          <Label htmlFor="admin-email">Admin Email</Label>
          <Input
            id="admin-email"
            type="email"
            placeholder="admin@example.com"
            value={data.adminEmail}
            onChange={(e) => onUpdate({ adminEmail: e.target.value })}
          />
          <p className="text-sm text-muted-foreground">
            This email will be used for identification only. No password needed.
          </p>
        </div>

        {/* Database Path */}
        <div className="space-y-2">
          <FolderPicker
            label="Database Location"
            value={data.databasePath}
            onChange={(path) => onUpdate({ databasePath: path })}
            placeholder="Select folder for database..."
            description="Choose where to store the Hub database file (hub.db)"
          />
        </div>

        {/* Local Mode Warning */}
        <Alert>
          <AlertCircle className="h-4 w-4 text-amber-500" />
          <AlertDescription className="text-amber-600 dark:text-amber-400">
            <strong>Note:</strong> Local mode is not persistent. Your configuration will reset on server restart.
            To preserve your setup, upgrade to Team Mode later.
          </AlertDescription>
        </Alert>

        {/* Information */}
        <Alert>
          <Info className="h-4 w-4" />
          <AlertDescription>
            <ul className="list-disc list-inside space-y-1 text-sm">
              <li>No password authentication</li>
              <li>Perfect for testing and development</li>
              <li>Single admin user</li>
              <li>Can upgrade to Team Mode anytime</li>
            </ul>
          </AlertDescription>
        </Alert>
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
