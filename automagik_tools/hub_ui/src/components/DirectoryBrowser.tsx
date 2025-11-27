/**
 * DirectoryBrowser Component
 *
 * Modal dialog for browsing and selecting directories.
 * Features:
 * - Navigate through filesystem
 * - Create new folders
 * - Show git repos with badge
 * - Security: Only browse within project root
 */
import React, { useState, useEffect } from 'react';
import {
  Folder,
  FolderOpen,
  ChevronRight,
  Home,
  ArrowUp,
  FolderPlus,
  GitBranch,
  AlertCircle,
  Loader2,
} from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from './ui/dialog';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Alert, AlertDescription } from './ui/alert';
import { Separator } from './ui/separator';
import { CreateFolderDialog } from './CreateFolderDialog';

interface DirectoryEntry {
  name: string;
  path: string;
  is_directory: boolean;
  writable: boolean;
  is_git_repo?: boolean;
}

interface DirectoryListResponse {
  current_path: string;
  parent_path: string | null;
  directories: DirectoryEntry[];
  files: DirectoryEntry[];
}

interface DirectoryBrowserProps {
  isOpen: boolean;
  onClose: () => void;
  onSelect: (path: string) => void;
  initialPath?: string;
}

export function DirectoryBrowser({
  isOpen,
  onClose,
  onSelect,
  initialPath = '',
}: DirectoryBrowserProps) {
  const [currentPath, setCurrentPath] = useState(initialPath);
  const [directories, setDirectories] = useState<DirectoryEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [parentPath, setParentPath] = useState<string | null>(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [selectedForCreation, setSelectedForCreation] = useState<string>('');

  useEffect(() => {
    if (isOpen) {
      loadDirectory(currentPath);
    }
  }, [isOpen, currentPath]);

  const loadDirectory = async (path: string) => {
    setLoading(true);
    setError(null);

    try {
      const queryParams = path ? `?path=${encodeURIComponent(path)}` : '';
      const response = await fetch(`/api/filesystem/directory${queryParams}`);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to load directory');
      }

      const data: DirectoryListResponse = await response.json();
      setDirectories(data.directories);
      setParentPath(data.parent_path);
      setCurrentPath(data.current_path);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load directory');
    } finally {
      setLoading(false);
    }
  };

  const handleNavigate = (path: string) => {
    setCurrentPath(path);
  };

  const handleGoUp = () => {
    if (parentPath !== null) {
      setCurrentPath(parentPath);
    }
  };

  const handleGoHome = () => {
    setCurrentPath('');
  };

  const handleSelect = () => {
    onSelect(currentPath);
  };

  const handleCreateFolder = (parentPath: string) => {
    setSelectedForCreation(parentPath);
    setShowCreateDialog(true);
  };

  const handleFolderCreated = () => {
    setShowCreateDialog(false);
    // Reload current directory to show new folder
    loadDirectory(currentPath);
  };

  // Breadcrumb navigation
  const pathParts = currentPath ? currentPath.split('/').filter(Boolean) : [];

  return (
    <>
      <Dialog open={isOpen} onOpenChange={onClose}>
        <DialogContent className="max-w-3xl max-h-[80vh] flex flex-col">
          <DialogHeader>
            <DialogTitle>Select Folder</DialogTitle>
          </DialogHeader>

          {/* Breadcrumb Navigation */}
          <div className="flex items-center gap-2 text-sm mb-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleGoHome}
              className="h-8 px-2"
            >
              <Home className="h-4 w-4" />
            </Button>

            {pathParts.map((part, index) => {
              const partPath = pathParts.slice(0, index + 1).join('/');
              return (
                <React.Fragment key={index}>
                  <ChevronRight className="h-4 w-4 text-muted-foreground" />
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleNavigate(partPath)}
                    className="h-8 px-2 font-mono"
                  >
                    {part}
                  </Button>
                </React.Fragment>
              );
            })}

            {pathParts.length === 0 && (
              <>
                <ChevronRight className="h-4 w-4 text-muted-foreground" />
                <span className="text-muted-foreground font-mono">(project root)</span>
              </>
            )}
          </div>

          <Separator />

          {/* Directory List */}
          <div className="flex-1 overflow-y-auto min-h-[300px] max-h-[400px]">
            {loading ? (
              <div className="flex items-center justify-center h-full">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              </div>
            ) : error ? (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            ) : (
              <div className="space-y-1">
                {/* Parent directory button */}
                {parentPath !== null && (
                  <Button
                    variant="ghost"
                    className="w-full justify-start h-12"
                    onClick={handleGoUp}
                  >
                    <ArrowUp className="h-4 w-4 mr-3 text-muted-foreground" />
                    <span className="font-mono text-muted-foreground">..</span>
                  </Button>
                )}

                {/* Directory list */}
                {directories.length === 0 ? (
                  <div className="text-center py-12 text-muted-foreground">
                    <Folder className="h-12 w-12 mx-auto mb-3 opacity-50" />
                    <p>No subdirectories</p>
                  </div>
                ) : (
                  directories.map((dir) => (
                    <Button
                      key={dir.path}
                      variant="ghost"
                      className="w-full justify-start h-12 group hover:bg-accent"
                      onClick={() => handleNavigate(dir.path)}
                    >
                      <FolderOpen className="h-4 w-4 mr-3 text-blue-500 group-hover:text-blue-600" />
                      <span className="flex-1 text-left font-mono text-sm">
                        {dir.name}
                      </span>
                      {dir.is_git_repo && (
                        <Badge variant="outline" className="ml-2 text-xs">
                          <GitBranch className="h-3 w-3 mr-1" />
                          git
                        </Badge>
                      )}
                      <ChevronRight className="h-4 w-4 ml-2 text-muted-foreground" />
                    </Button>
                  ))
                )}
              </div>
            )}
          </div>

          <Separator />

          {/* Current selection display */}
          <div className="bg-muted/50 rounded-md p-3 font-mono text-sm">
            <div className="text-xs text-muted-foreground mb-1">Selected:</div>
            <div className="flex items-center gap-2">
              <Folder className="h-4 w-4 text-blue-500" />
              <span className="flex-1">
                {currentPath || '(project root)'}
              </span>
            </div>
          </div>

          <DialogFooter className="flex items-center justify-between sm:justify-between">
            <Button
              type="button"
              variant="outline"
              onClick={() => handleCreateFolder(currentPath)}
              className="gap-2"
            >
              <FolderPlus className="h-4 w-4" />
              New Folder
            </Button>

            <div className="flex gap-2">
              <Button type="button" variant="outline" onClick={onClose}>
                Cancel
              </Button>
              <Button type="button" onClick={handleSelect}>
                Select Folder
              </Button>
            </div>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Create Folder Dialog */}
      <CreateFolderDialog
        isOpen={showCreateDialog}
        onClose={() => setShowCreateDialog(false)}
        onSuccess={handleFolderCreated}
        parentPath={selectedForCreation}
      />
    </>
  );
}
