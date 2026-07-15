"use client";

import { memo, useCallback, useRef, useEffect } from "react";
import Editor, { OnMount, type BeforeMount } from "@monaco-editor/react";
import { Loader2 } from "lucide-react";
import { TAYARI_THEME } from "@/features/coding/lib/monaco-theme";
import { LANGUAGE_MONACO_IDS } from "@/features/coding/lib/code-templates";

interface CodeEditorProps {
  language: string;
  value: string;
  onChange: (value: string) => void;
  onMount?: () => void;
  readOnly?: boolean;
  height?: string;
}

export const CodeEditor = memo(function CodeEditor({
  language,
  value,
  onChange,
  onMount,
  readOnly = false,
  height = "100%",
}: CodeEditorProps) {
  const editorRef = useRef<Parameters<OnMount>[0] | null>(null);

  const handleBeforeMount: BeforeMount = useCallback((monaco) => {
    monaco.editor.defineTheme("tayari-dark", TAYARI_THEME);
  }, []);

  const handleMount: OnMount = useCallback((editor) => {
    editorRef.current = editor;
    editor.focus();
    onMount?.();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleChange = useCallback((val: string | undefined) => {
    if (val !== undefined) onChange(val);
  }, [onChange]);

  const monacoLang = LANGUAGE_MONACO_IDS[language] ?? "plaintext";

  return (
    <Editor
      height={height}
      language={monacoLang}
      value={value}
      onChange={handleChange}
      beforeMount={handleBeforeMount}
      onMount={handleMount}
      theme="tayari-dark"
      loading={<div className="flex h-full items-center justify-center"><Loader2 className="h-5 w-5 animate-spin text-muted-foreground" /></div>}
      options={{
        fontSize: 14,
        fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
        lineNumbers: "on",
        minimap: { enabled: false },
        scrollBeyondLastLine: false,
        automaticLayout: true,
        tabSize: 4,
        insertSpaces: true,
        wordWrap: "on",
        readOnly,
        renderWhitespace: "selection",
        bracketPairColorization: { enabled: true },
        padding: { top: 12 },
        smoothScrolling: true,
        cursorBlinking: "smooth",
        cursorSmoothCaretAnimation: "on",
      }}
      aria-label="Code editor"
    />
  );
});
