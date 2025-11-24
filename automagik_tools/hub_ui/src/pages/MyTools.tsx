import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Play, Square, RefreshCw, Settings, Trash2, Plus } from 'lucide-react';
import { toast } from 'sonner';
import { useNavigate } from 'react-router-dom';
import { DashboardLayout } from '../components/DashboardLayout';
import { PageHeader } from '../components/PageHeader';
import { api, UserTool } from '../lib/api';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '../components/ui/alert-dialog';
import { useState } from 'react';

export default function MyTools() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [deleteDialog, setDeleteDialog] = useState(false);
  const [toolToDelete, setToolToDelete] = useState<string | null>(null);

  // Fetch user's tools
  const { data: tools = [], isLoading } = useQuery({
    queryKey: ['myTools'],
    queryFn: () => api.tools.list(),
  });

  // Mutations
  const startMutation = useMutation({
    mutationFn: (toolName: string) => api.lifecycle.start(toolName),
    onSuccess: (_, toolName) => {
      toast.success(`Tool started successfully`);
      queryClient.invalidateQueries({ queryKey: ['myTools'] });
    },
    onError: (error) => {
      toast.error(`Failed to start tool: ${error instanceof Error ? error.message : 'Unknown error'}`);
    },
  });

  const stopMutation = useMutation({
    mutationFn: (toolName: string) => api.lifecycle.stop(toolName),
    onSuccess: (_, toolName) => {
      toast.success(`Tool stopped successfully`);
      queryClient.invalidateQueries({ queryKey: ['myTools'] });
    },
    onError: (error) => {
      toast.error(`Failed to stop tool: ${error instanceof Error ? error.message : 'Unknown error'}`);
    },
  });

  const refreshMutation = useMutation({
    mutationFn: (toolName: string) => api.lifecycle.refresh(toolName),
    onSuccess: (_, toolName) => {
      toast.success(`Tool refreshed successfully`);
      queryClient.invalidateQueries({ queryKey: ['myTools'] });
    },
    onError: (error) => {
      toast.error(`Failed to refresh tool: ${error instanceof Error ? error.message : 'Unknown error'}`);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (toolName: string) => api.tools.delete(toolName),
    onSuccess: () => {
      toast.success(`Tool removed successfully`);
      queryClient.invalidateQueries({ queryKey: ['myTools'] });
      setDeleteDialog(false);
      setToolToDelete(null);
    },
    onError: (error) => {
      toast.error(`Failed to remove tool: ${error instanceof Error ? error.message : 'Unknown error'}`);
    },
  });

  const handleDelete = (toolName: string) => {
    setToolToDelete(toolName);
    setDeleteDialog(true);
  };

  const confirmDelete = () => {
    if (toolToDelete) {
      deleteMutation.mutate(toolToDelete);
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <PageHeader
          title="My Tools"
          subtitle="Manage your personal tool collection"
          action={
            <Button onClick={() => navigate('/catalogue')}>
              <Plus className="h-4 w-4 mr-2" />
              Add Tool
            </Button>
          }
        />

        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[...Array(3)].map((_, i) => (
              <Card key={i} className="animate-pulse">
                <CardHeader>
                  <div className="h-6 bg-muted rounded w-3/4" />
                  <div className="h-4 bg-muted rounded w-full mt-2" />
                </CardHeader>
                <CardContent>
                  <div className="h-20 bg-muted rounded" />
                </CardContent>
              </Card>
            ))}
          </div>
        ) : tools.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <div className="rounded-full bg-muted p-4 mb-4">
                <Plus className="h-8 w-8 text-muted-foreground" />
              </div>
              <p className="text-lg font-medium">No tools configured yet</p>
              <p className="text-sm text-muted-foreground mb-4">
                Get started by adding tools from the catalogue
              </p>
              <Button onClick={() => navigate('/catalogue')}>
                <Plus className="h-4 w-4 mr-2" />
                Browse Catalogue
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {tools.map((tool: UserTool) => (
              <Card key={tool.tool_name} className="flex flex-col">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <CardTitle className="text-lg">{tool.tool_name}</CardTitle>
                    <Badge variant={tool.enabled ? 'default' : 'secondary'}>
                      {tool.enabled ? 'Enabled' : 'Disabled'}
                    </Badge>
                  </div>
                  <CardDescription>
                    Added: {new Date(tool.created_at).toLocaleDateString()}
                  </CardDescription>
                </CardHeader>

                <CardContent className="flex-1">
                  <div className="space-y-2 text-sm">
                    <div>
                      <span className="text-muted-foreground">Last Updated:</span>
                      <span className="ml-2">
                        {new Date(tool.updated_at).toLocaleDateString()}
                      </span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Configuration:</span>
                      <span className="ml-2">
                        {Object.keys(tool.config).length} settings
                      </span>
                    </div>
                  </div>
                </CardContent>

                <CardFooter className="flex flex-col gap-2">
                  <div className="grid grid-cols-3 gap-2 w-full">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => startMutation.mutate(tool.tool_name)}
                      disabled={startMutation.isPending}
                    >
                      <Play className="h-4 w-4" />
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => stopMutation.mutate(tool.tool_name)}
                      disabled={stopMutation.isPending}
                    >
                      <Square className="h-4 w-4" />
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => refreshMutation.mutate(tool.tool_name)}
                      disabled={refreshMutation.isPending}
                    >
                      <RefreshCw className="h-4 w-4" />
                    </Button>
                  </div>
                  <div className="grid grid-cols-2 gap-2 w-full">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => navigate(`/tools/${tool.tool_name}/configure`)}
                    >
                      <Settings className="h-4 w-4 mr-2" />
                      Configure
                    </Button>
                    <Button
                      size="sm"
                      variant="destructive"
                      onClick={() => handleDelete(tool.tool_name)}
                    >
                      <Trash2 className="h-4 w-4 mr-2" />
                      Remove
                    </Button>
                  </div>
                </CardFooter>
              </Card>
            ))}
          </div>
        )}

        {/* Delete Confirmation Dialog */}
        <AlertDialog open={deleteDialog} onOpenChange={setDeleteDialog}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Remove Tool</AlertDialogTitle>
              <AlertDialogDescription>
                Are you sure you want to remove this tool from your collection? This action cannot be undone.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction
                onClick={confirmDelete}
                className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              >
                Remove
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    </DashboardLayout>
  );
}
