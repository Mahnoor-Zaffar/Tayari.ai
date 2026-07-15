"use client";

import { memo } from "react";
import { FileText, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

interface NotesPanelProps {
  isOpen: boolean;
  onClose: () => void;
  notes: string;
  onNotesChange: (text: string) => void;
}

export const NotesPanel = memo(function NotesPanel({
  isOpen,
  onClose,
  notes,
  onNotesChange,
}: NotesPanelProps) {
  if (!isOpen) return null;

  return (
    <aside
      className="flex h-full flex-col border-l border-border bg-card"
      role="complementary"
      aria-label="Interview notes"
    >
      <div className="flex items-center justify-between border-b border-border px-4 py-3">
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4 text-muted-foreground" />
          <h3 className="text-sm font-semibold">Notes</h3>
        </div>
        <Button type="button" variant="ghost" size="icon" onClick={onClose} aria-label="Close notes">
          <X className="h-4 w-4" />
        </Button>
      </div>
      <div className="flex-1 overflow-y-auto p-4">
        <Textarea
          value={notes}
          onChange={(e) => onNotesChange(e.target.value)}
          placeholder="Take notes during the interview..."
          className="h-full min-h-[200px] resize-none border-0 bg-transparent p-0 text-sm focus-visible:ring-0"
          aria-label="Your notes"
        />
      </div>
    </aside>
  );
});
