/**
 * CreateFolderDialog Component
 *
 * Dialog for creating new folders within the project directory.
 */
import React, { useState, useEffect } from 'react';
import { FolderPlus, AlertCircle, Loader2 } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from './ui/dialog';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Alert, AlertDescription } from './ui/alert';

interface CreateFolderDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  parentPath: string;
}

export function CreateFolderDialog({
  isOpen,
  onClose,
  onSuccess,
  parentPath,
}: CreateFolderDialogProps) {
  const [folderName, setFolderName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      setFolderName('');
      setError(null);
    }
  }, [isOpen]);

  const handleCreate = async () => {
    if (!folderName.trim()) {
      setError('Folder name is required');
      return;
    }

    // Validate folder name (no special characters, no path separators)
    if (!/^[a-zA-Z0-9_\-. ]+$/.test(folderName)) {
      setError('Folder name can only contain letters, numbers, spaces, dots, dashes, and underscores');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Construct full path
      const newFolderPath = parentPath
        ? `${parentPath}/${folderName}`
        : folderName;

      const response = await fetch('/api/filesystem/create-folder', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          path: newFolderPath,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create folder');
      }

      // Success
      onSuccess();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create folder');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !loading) {
      handleCreate();
    }
  };

  const fullPath = parentPath
    ? `${parentPath}/${folderName || '...'}`
    : folderName || '...';

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FolderPlus className="h-5 w-5" />
            Create New Folder
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Parent path display */}
          <div className="bg-muted/50 rounded-md p-3 font-mono text-sm">
            <div className="text-xs text-muted-foreground mb-1">Parent:</div>
            <div>{parentPath || '(project root)'}</div>
          </div>

          {/* Folder name input */}
          <div className="space-y-2">
            <Label htmlFor="folder-name">Folder Name</Label>
            <Input
              id="folder-name"
              value={folderName}
              onChange={(e) => setFolderName(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="my-folder"
              autoFocus
              disabled={loading}
            />
          </div>

          {/* Full path preview */}
          <div className="bg-muted/30 rounded-md p-3 font-mono text-xs">
            <div className="text-muted-foreground mb-1">Will create:</div>
            <div className="text-foreground">{fullPath}</div>
          </div>

          {/* Error message */}
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
        </div>

        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={onClose}
            disabled={loading}
          >
            Cancel
          </Button>
          <Button
            type="button"
            onClick={handleCreate}
            disabled={loading || !folderName.trim()}
          >
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Creating...
              </>
            ) : (
              <>
                <FolderPlus className="mr-2 h-4 w-4" />
                Create
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
