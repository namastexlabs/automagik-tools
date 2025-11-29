/**
 * Setup Wizard - Refactored Multi-Step Version
 *
 * Beautiful multi-step wizard with proper state management.
 * Phases covered:
 * - Phase 4: Multi-step wizard UI
 * - Phase 5: LOCAL mode with folder picker
 * - Phase 6: WorkOS hybrid setup (Quick Start + Custom App)
 */
import { useState, useEffect, useReducer } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Card, CardContent } from '@/components/ui/card';
import { StepIndicator, type Step } from '@/components/StepIndicator';
import { Step0_ModeSelection, type Step0Data } from '@/components/wizard/Step0_ModeSelection';
import { Step1b_WorkOSConfig, type Step1bData } from '@/components/wizard/Step1b_WorkOSConfig';
import { Step2_NetworkConfig, type Step2Data } from '@/components/wizard/Step2_NetworkConfig';
import { Step3_Review, ApiKeyDialog } from '@/components/wizard/Step3_Review';
import { RestartTransition, type RestartConfig } from '@/components/wizard/RestartTransition';

// Wizard state type
interface WizardState extends Step0Data, Step1bData, Step2Data {
  currentStep: number;
  completedSteps: Set<number>;
}

// Wizard actions
type WizardAction =
  | { type: 'UPDATE_DATA'; payload: Partial<WizardState> }
  | { type: 'NEXT_STEP' }
  | { type: 'PREV_STEP' }
  | { type: 'COMPLETE_STEP'; step: number }
  | { type: 'GO_TO_STEP'; step: number };

// Initial state
const initialState: WizardState = {
  // Step 0
  mode: null,
  // Step 1b (WorkOS)
  setupType: null,
  clientId: '',
  apiKey: '',
  authkitDomain: '',
  adminEmails: '',
  // Step 2 (Network)
  bindAddress: 'localhost',
  port: 8000,
  // State management
  currentStep: 0,
  completedSteps: new Set(),
};

// Reducer
function wizardReducer(state: WizardState, action: WizardAction): WizardState {
  switch (action.type) {
    case 'UPDATE_DATA':
      return { ...state, ...action.payload };

    case 'NEXT_STEP':
      return {
        ...state,
        currentStep: state.currentStep + 1,
        completedSteps: new Set([...state.completedSteps, state.currentStep]),
      };

    case 'PREV_STEP':
      return {
        ...state,
        currentStep: Math.max(0, state.currentStep - 1),
      };

    case 'COMPLETE_STEP':
      return {
        ...state,
        completedSteps: new Set([...state.completedSteps, action.step]),
      };

    case 'GO_TO_STEP':
      return {
        ...state,
        currentStep: action.step,
      };

    default:
      return state;
  }
}

export default function SetupNew() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [state, dispatch] = useReducer(wizardReducer, initialState);
  const [apiKey, setApiKey] = useState<string | null>(null);
  const [showApiKey, setShowApiKey] = useState(false);
  const [showRestartDialog, setShowRestartDialog] = useState(false);
  const [pendingRestartConfig, setPendingRestartConfig] = useState<RestartConfig | null>(null);
  const [authError, setAuthError] = useState<string | null>(null);
  const isUpgrade = searchParams.get('mode') === 'upgrade';

  // Set local mode user info so isAuthenticated() returns true
  // Key must match USER_STORAGE_KEY in auth.ts = 'hub_user'
  // Returns boolean for success/failure - RACE CONDITION FIX
  const setLocalModeUser = (): boolean => {
    try {
      const user = {
        id: 'local',
        email: 'local@localhost',
        first_name: 'Local',
        last_name: 'User',
        workspace_id: 'local',
        workspace_name: 'Local Mode',
        workspace_slug: 'local',
        is_super_admin: true,
        mfa_enabled: false
      };
      localStorage.setItem('hub_user', JSON.stringify(user));

      // RACE CONDITION FIX: Verify write committed by reading back
      // This forces browser to flush the pending setItem before we redirect
      const stored = localStorage.getItem('hub_user');
      if (!stored) {
        console.error('localStorage write verification failed - storage may be restricted');
        return false;
      }
      return true;
    } catch (e) {
      console.error('setLocalModeUser failed:', e);
      return false;
    }
  };

  // Check if setup is already complete
  useEffect(() => {
    fetch('/api/setup/status')
      .then((res) => res.json())
      .then((data) => {
        if (!data.is_setup_required && !isUpgrade) {
          navigate('/dashboard');
        }
      })
      .catch(console.error);
  }, [navigate, isUpgrade]);

  // Define steps based on mode
  const getSteps = (): Step[] => {
    const baseSteps: Step[] = [
      { id: 'mode', title: 'Mode', description: 'Choose setup type' },
    ];

    if (state.mode === 'workos') {
      baseSteps.push({ id: 'workos-config', title: 'WorkOS', description: 'Credentials' });
    }

    if (state.mode) {
      baseSteps.push(
        { id: 'network', title: 'Network', description: 'Server config' },
        { id: 'review', title: 'Review', description: 'Confirm setup' }
      );
    }

    return baseSteps;
  };

  const steps = getSteps();

  // Check if network config change requires restart
  const checkRestartRequired = async (): Promise<boolean> => {
    try {
      const response = await fetch('/api/server/status');
      if (!response.ok) return false;
      const status = await response.json();

      // Compare running config with desired config
      const runningBindAddress = status.running.bind_address;
      const runningPort = status.running.port;
      const desiredBindAddress = state.bindAddress === 'localhost' ? '127.0.0.1' : '0.0.0.0';

      return runningBindAddress !== desiredBindAddress || runningPort !== state.port;
    } catch {
      // If we can't check, assume no restart needed (first-time setup)
      return false;
    }
  };

  // Handle complete setup
  const handleComplete = async () => {
    if (state.mode === 'local') {
      // Local mode setup
      const response = await fetch('/api/setup/local', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Local setup failed');
      }

      const data = await response.json();

      // Save network config (this just saves to DB, doesn't apply yet)
      await fetch('/api/setup/network-config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          bind_address: state.bindAddress,
          port: state.port,
        }),
      });

      // Check if restart is needed to apply network config
      const needsRestart = await checkRestartRequired();

      // Capture API key and show dialog
      if (data.api_key) {
        setApiKey(data.api_key);
        setShowApiKey(true);
        // If restart is needed, we'll trigger it after API key dialog closes
        if (needsRestart) {
          setPendingRestartConfig({
            bindAddress: state.bindAddress,
            port: state.port,
          });
        }
      } else if (needsRestart) {
        // No API key to show, go straight to restart
        setPendingRestartConfig({
          bindAddress: state.bindAddress,
          port: state.port,
        });
        setShowRestartDialog(true);
      } else {
        // No restart needed, redirect to dashboard
        if (setLocalModeUser()) {
          window.location.href = '/app/dashboard';
        } else {
          setAuthError('Failed to save authentication. Check browser privacy settings or try a different browser.');
        }
      }
    } else if (state.mode === 'workos') {
      // WorkOS mode setup
      const adminEmailsArray = state.adminEmails
        .split(',')
        .map((e) => e.trim())
        .filter(Boolean);

      const endpoint = isUpgrade ? '/api/setup/upgrade-to-workos' : '/api/setup/workos';
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          client_id: state.clientId,
          api_key: state.apiKey,
          authkit_domain: state.authkitDomain,
          super_admin_emails: adminEmailsArray,
          setup_type: state.setupType,
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'WorkOS setup failed');
      }

      // Save network config
      await fetch('/api/setup/network-config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          bind_address: state.bindAddress,
          port: state.port,
        }),
      });

      // Check if restart is needed
      const needsRestart = await checkRestartRequired();

      if (needsRestart) {
        setPendingRestartConfig({
          bindAddress: state.bindAddress,
          port: state.port,
        });
        setShowRestartDialog(true);
      } else {
        // Redirect to login
        window.location.href = '/app/login';
      }
    }
  };

  // Handle restart success
  const handleRestartSuccess = (newUrl: string) => {
    // Redirect to appropriate page on new URL
    if (state.mode === 'workos') {
      window.location.href = `${newUrl}/app/login`;
    } else {
      if (setLocalModeUser()) {
        window.location.href = `${newUrl}/app/dashboard`;
      } else {
        setAuthError('Failed to save authentication. Check browser privacy settings or try a different browser.');
        setShowRestartDialog(false);
      }
    }
  };

  // Render current step
  const renderStep = () => {
    const stepIndex = state.currentStep;

    // Step 0: Mode Selection
    if (stepIndex === 0) {
      return (
        <Step0_ModeSelection
          data={{ mode: state.mode }}
          onUpdate={(data) => dispatch({ type: 'UPDATE_DATA', payload: data })}
          onNext={() => dispatch({ type: 'NEXT_STEP' })}
          isUpgrade={isUpgrade}
        />
      );
    }

    // Step 1b: WorkOS Config (if mode is workos)
    if (state.mode === 'workos' && stepIndex === 1) {
      return (
        <Step1b_WorkOSConfig
          data={{
            setupType: state.setupType,
            clientId: state.clientId,
            apiKey: state.apiKey,
            authkitDomain: state.authkitDomain,
            adminEmails: state.adminEmails,
          }}
          onUpdate={(data) => dispatch({ type: 'UPDATE_DATA', payload: data })}
          onNext={() => dispatch({ type: 'NEXT_STEP' })}
          onBack={() => dispatch({ type: 'PREV_STEP' })}
        />
      );
    }

    // Step 2: Network Config
    if ((state.mode === 'local' && stepIndex === 1) || (state.mode === 'workos' && stepIndex === 2)) {
      return (
        <Step2_NetworkConfig
          data={{
            bindAddress: state.bindAddress,
            port: state.port,
          }}
          onUpdate={(data) => dispatch({ type: 'UPDATE_DATA', payload: data })}
          onNext={() => dispatch({ type: 'NEXT_STEP' })}
          onBack={() => dispatch({ type: 'PREV_STEP' })}
        />
      );
    }

    // Step 3: Review
    if ((state.mode === 'local' && stepIndex === 2) || (state.mode === 'workos' && stepIndex === 3)) {
      return (
        <Step3_Review
          mode={state.mode}
          bindAddress={state.bindAddress}
          port={state.port}
          workosClientId={state.clientId}
          workosApiKey={state.apiKey}
          workosAuthkitDomain={state.authkitDomain}
          workosAdminEmails={state.adminEmails.split(',').map((e) => e.trim()).filter(Boolean)}
          workosSetupType={state.setupType || undefined}
          onBack={() => dispatch({ type: 'PREV_STEP' })}
          onComplete={handleComplete}
          isUpgrade={isUpgrade}
        />
      );
    }

    return null;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-600 to-purple-900 flex items-center justify-center p-4">
      <Card className="w-full max-w-4xl">
        <CardContent className="p-8">
          {/* Step Indicator */}
          {state.mode !== null && (
            <div className="mb-8">
              <StepIndicator
                steps={steps}
                currentStep={state.currentStep}
                completedSteps={state.completedSteps}
              />
            </div>
          )}

          {/* Current Step */}
          {renderStep()}
        </CardContent>
      </Card>

      {/* Auth Error Display */}
      {authError && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md mx-4 shadow-xl">
            <h3 className="text-lg font-semibold text-red-600 mb-2">Authentication Error</h3>
            <p className="text-gray-600 mb-4">{authError}</p>
            <button
              onClick={() => setAuthError(null)}
              className="w-full bg-purple-600 text-white py-2 px-4 rounded hover:bg-purple-700"
            >
              Try Again
            </button>
          </div>
        </div>
      )}

      {/* API Key Dialog for Local Mode */}
      {apiKey && (
        <ApiKeyDialog
          apiKey={apiKey}
          open={showApiKey}
          onContinue={() => {
            setShowApiKey(false);
            // Check if restart is pending
            if (pendingRestartConfig) {
              setShowRestartDialog(true);
            } else {
              if (setLocalModeUser()) {
                window.location.href = '/app/dashboard';
              } else {
                setAuthError('Failed to save authentication. Check browser privacy settings or try a different browser.');
              }
            }
          }}
        />
      )}

      {/* Restart Transition Dialog */}
      {pendingRestartConfig && (
        <RestartTransition
          open={showRestartDialog}
          onOpenChange={setShowRestartDialog}
          config={pendingRestartConfig}
          onSuccess={handleRestartSuccess}
        />
      )}
    </div>
  );
}
