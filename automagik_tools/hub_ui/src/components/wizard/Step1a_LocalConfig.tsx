/**
 * Step 1a: Local Mode Configuration
 *
 * Configure local mode with API key authentication.
 */
import React from 'react';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Info, ChevronLeft, ChevronRight } from 'lucide-react';

export interface Step1aData {
  // No data needed for local mode
}

interface Step1aProps {
  data: Step1aData;
  onUpdate: (data: Partial<Step1aData>) => void;
  onNext: () => void;
  onBack: () => void;
}

export function Step1a_LocalConfig({ data, onUpdate, onNext, onBack }: Step1aProps) {
  const handleNext = () => {
    // No email needed, just continue
    onNext();
  };

  return (
    <div className="space-y-6 max-w-2xl mx-auto">
      <div className="text-center">
        <h2 className="text-2xl font-bold mb-2">🏠 Local Mode Configuration</h2>
        <p className="text-muted-foreground">
          Single-tenant instance with API key authentication
        </p>
      </div>

      <div className="space-y-4">
        {/* Local Mode Features */}
        <Alert>
          <Info className="h-4 w-4" />
          <AlertTitle>Local Mode Features</AlertTitle>
          <AlertDescription>
            <ul className="list-disc list-inside space-y-1 text-sm mt-2">
              <li>✅ Configuration persists across restarts</li>
              <li>✅ Authenticate using generated API key</li>
              <li>✅ Single admin user (full access)</li>
              <li>✅ Perfect for testing and development</li>
              <li>📦 Uses SQLite database in data/hub.db</li>
            </ul>
          </AlertDescription>
        </Alert>

        {/* Setup Information */}
        <Alert>
          <Info className="h-4 w-4" />
          <AlertDescription>
            <p className="text-sm">
              After setup completes, you'll receive an <strong>Omni API key</strong> that you'll use for authentication.
              Make sure to save it securely - it will only be shown once!
            </p>
          </AlertDescription>
        </Alert>
      </div>

      {/* Navigation */}
      <div className="flex gap-3 justify-between pt-4">
        <Button variant="outline" onClick={onBack}>
          <ChevronLeft className="mr-2 h-4 w-4" />
          Back
        </Button>
        <Button onClick={handleNext}>
          Continue
          <ChevronRight className="ml-2 h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
