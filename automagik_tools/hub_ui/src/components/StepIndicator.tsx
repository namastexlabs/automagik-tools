/**
 * StepIndicator Component
 *
 * Visual progress indicator for multi-step wizard.
 */
import React from 'react';
import { Check } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface Step {
  id: string;
  title: string;
  description?: string;
}

interface StepIndicatorProps {
  steps: Step[];
  currentStep: number;
  completedSteps: Set<number>;
}

export function StepIndicator({ steps, currentStep, completedSteps }: StepIndicatorProps) {
  return (
    <nav aria-label="Progress">
      <ol role="list" className="flex items-center justify-center gap-2 sm:gap-4">
        {steps.map((step, index) => {
          const isCompleted = completedSteps.has(index);
          const isCurrent = index === currentStep;
          const isUpcoming = index > currentStep;

          return (
            <li key={step.id} className="relative flex items-center">
              {/* Connector line */}
              {index > 0 && (
                <div
                  className={cn(
                    'absolute right-full w-8 sm:w-16 h-0.5 -translate-x-2 sm:-translate-x-4',
                    isCompleted ? 'bg-purple-600' : 'bg-gray-300 dark:bg-gray-700'
                  )}
                />
              )}

              {/* Step circle */}
              <div className="flex flex-col items-center gap-1">
                <div
                  className={cn(
                    'relative flex h-10 w-10 items-center justify-center rounded-full border-2 transition-all',
                    isCompleted && 'border-purple-600 bg-purple-600',
                    isCurrent && 'border-purple-600 bg-white dark:bg-gray-900',
                    isUpcoming && 'border-gray-300 bg-white dark:border-gray-700 dark:bg-gray-900'
                  )}
                >
                  {isCompleted ? (
                    <Check className="h-5 w-5 text-white" />
                  ) : (
                    <span
                      className={cn(
                        'text-sm font-semibold',
                        isCurrent && 'text-purple-600',
                        isUpcoming && 'text-gray-400 dark:text-gray-600'
                      )}
                    >
                      {index + 1}
                    </span>
                  )}
                </div>

                {/* Step title (hidden on mobile for space) */}
                <div className="hidden sm:block text-center">
                  <div
                    className={cn(
                      'text-xs font-medium',
                      isCurrent && 'text-purple-600',
                      isCompleted && 'text-purple-600',
                      isUpcoming && 'text-gray-500 dark:text-gray-500'
                    )}
                  >
                    {step.title}
                  </div>
                  {step.description && (
                    <div className="text-xs text-gray-500 dark:text-gray-500 max-w-[100px] truncate">
                      {step.description}
                    </div>
                  )}
                </div>
              </div>
            </li>
          );
        })}
      </ol>

      {/* Current step title on mobile */}
      <div className="mt-4 text-center sm:hidden">
        <div className="text-sm font-medium text-purple-600">
          {steps[currentStep]?.title}
        </div>
        {steps[currentStep]?.description && (
          <div className="text-xs text-gray-500 dark:text-gray-500">
            {steps[currentStep].description}
          </div>
        )}
      </div>
    </nav>
  );
}
