/**
 * FolderPicker Component
 *
 * Beautiful folder browser with create folder support.
 * Inspired by automagik-forge's file picker design.
 */
import React, { useState, useEffect } from 'react';
import { Folder, ChevronRight, Home, HardDrive } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Separator } from './ui/separator';
import { DirectoryBrowser } from './DirectoryBrowser';
import { CreateFolderDialog } from './CreateFolderDialog';

interface FolderPickerProps {
  label: string;
  value: string;
  onChange: (path: string) => void;
  placeholder?: string;
  description?: string;
}

export function FolderPicker({
  label,
  value,
  onChange,
  placeholder = 'Select a folder...',
  description,
}: FolderPickerProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedPath, setSelectedPath] = useState(value);

  useEffect(() => {
    setSelectedPath(value);
  }, [value]);

  const handleSelect = (path: string) => {
    setSelectedPath(path);
    onChange(path);
    setIsOpen(false);
  };

  const displayPath = selectedPath || placeholder;

  return (
    <div className="space-y-2">
      <Label htmlFor="folder-picker">{label}</Label>

      <div className="flex gap-2">
        <div className="flex-1 relative">
          <Input
            id="folder-picker"
            value={displayPath}
            readOnly
            onClick={() => setIsOpen(true)}
            className="cursor-pointer pr-10 font-mono text-sm"
            placeholder={placeholder}
          />
          <Folder className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        </div>

        <Button
          type="button"
          variant="outline"
          onClick={() => setIsOpen(true)}
        >
          Browse...
        </Button>
      </div>

      {description && (
        <p className="text-sm text-muted-foreground">{description}</p>
      )}

      {isOpen && (
        <DirectoryBrowser
          isOpen={isOpen}
          onClose={() => setIsOpen(false)}
          onSelect={handleSelect}
          initialPath={selectedPath}
        />
      )}
    </div>
  );
}
