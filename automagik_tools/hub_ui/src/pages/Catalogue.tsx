import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { Plus, Search, Filter, X } from 'lucide-react';
import { toast } from 'sonner';
import { DashboardLayout } from '../components/DashboardLayout';
import { PageHeader } from '../components/PageHeader';
import { api, type Tool } from '../lib/api';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import { Label } from '../components/ui/label';

export default function Catalogue() {
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [selectedTool, setSelectedTool] = useState<Tool | null>(null);
  const [configDialog, setConfigDialog] = useState(false);
  const [config, setConfig] = useState<Record<string, any>>({});

  // Fetch tool catalogue
  const { data: tools = [], isLoading } = useQuery({
    queryKey: ['catalogue'],
    queryFn: () => api.catalogue.list(),
  });

  // Get unique categories
  const categories = ['all', ...new Set(tools.map((t) => t.category))];

  // Filter tools
  const filteredTools = tools.filter((tool) => {
    const matchesSearch =
      tool.tool_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      tool.display_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      tool.description.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesCategory = categoryFilter === 'all' || tool.category === categoryFilter;

    return matchesSearch && matchesCategory;
  });

  // Handle tool configuration
  const handleConfigureTool = (tool: Tool) => {
    setSelectedTool(tool);
    setConfig({});
    setConfigDialog(true);
  };

  const handleSaveConfig = async () => {
    if (!selectedTool) return;

    try {
      await api.tools.configure(selectedTool.tool_name, config);
      toast.success(`${selectedTool.display_name} configured successfully!`);
      setConfigDialog(false);
      setSelectedTool(null);
      setConfig({});
    } catch (error) {
      toast.error(`Failed to configure tool: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <PageHeader
          title="Tool Catalogue"
          subtitle="Browse and configure tools from the repository"
        />

        {/* Search and Filters */}
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search tools..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
            {searchQuery && (
              <Button
                variant="ghost"
                size="sm"
                className="absolute right-1 top-1/2 -translate-y-1/2 h-7"
                onClick={() => setSearchQuery('')}
              >
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>

          <div className="flex gap-2">
            <Button
              variant={categoryFilter === 'all' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setCategoryFilter('all')}
            >
              <Filter className="h-4 w-4 mr-2" />
              All
            </Button>
            {categories.filter((c) => c !== 'all').map((category) => (
              <Button
                key={category}
                variant={categoryFilter === category ? 'default' : 'outline'}
                size="sm"
                onClick={() => setCategoryFilter(category)}
              >
                {category}
              </Button>
            ))}
          </div>
        </div>

        {/* Tool Grid */}
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[...Array(6)].map((_, i) => (
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
        ) : filteredTools.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <Search className="h-12 w-12 text-muted-foreground mb-4" />
              <p className="text-lg font-medium text-muted-foreground">No tools found</p>
              <p className="text-sm text-muted-foreground">
                Try adjusting your search or filters
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredTools.map((tool) => (
              <Card key={tool.tool_name} className="flex flex-col">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <CardTitle className="text-lg">{tool.display_name}</CardTitle>
                    <Badge variant="secondary">{tool.category}</Badge>
                  </div>
                  <CardDescription className="line-clamp-2">
                    {tool.description}
                  </CardDescription>
                </CardHeader>
                <CardContent className="flex-1">
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center gap-2">
                      <span className="text-muted-foreground">Auth:</span>
                      <Badge variant="outline">{tool.auth_type}</Badge>
                    </div>
                    {tool.required_oauth && tool.required_oauth.length > 0 && (
                      <div className="flex items-center gap-2">
                        <span className="text-muted-foreground">OAuth:</span>
                        <div className="flex flex-wrap gap-1">
                          {tool.required_oauth.map((scope) => (
                            <Badge key={scope} variant="outline" className="text-xs">
                              {scope}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </CardContent>
                <CardFooter>
                  <Button
                    className="w-full"
                    onClick={() => handleConfigureTool(tool)}
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    Add Tool
                  </Button>
                </CardFooter>
              </Card>
            ))}
          </div>
        )}

        {/* Configuration Dialog */}
        <Dialog open={configDialog} onOpenChange={setConfigDialog}>
          <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Configure {selectedTool?.display_name}</DialogTitle>
              <DialogDescription>
                {selectedTool?.description}
              </DialogDescription>
            </DialogHeader>

            {selectedTool && (
              <div className="space-y-4">
                {Object.entries(selectedTool.config_schema.properties || {}).map(([key, schema]: [string, any]) => (
                  <div key={key} className="space-y-2">
                    <Label htmlFor={key}>
                      {schema.title || key}
                      {selectedTool.config_schema.required?.includes(key) && (
                        <span className="text-destructive ml-1">*</span>
                      )}
                    </Label>
                    {schema.description && (
                      <p className="text-sm text-muted-foreground">{schema.description}</p>
                    )}
                    <Input
                      id={key}
                      type={schema.type === 'integer' || schema.type === 'number' ? 'number' : 'text'}
                      placeholder={schema.default || ''}
                      value={config[key] || ''}
                      onChange={(e) => setConfig({ ...config, [key]: e.target.value })}
                    />
                  </div>
                ))}
              </div>
            )}

            <DialogFooter>
              <Button variant="outline" onClick={() => setConfigDialog(false)}>
                Cancel
              </Button>
              <Button onClick={handleSaveConfig}>
                Save Configuration
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  );
}
