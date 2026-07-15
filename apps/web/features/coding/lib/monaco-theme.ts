import type { editor } from "monaco-editor";

export const TAYARI_THEME: editor.IStandaloneThemeData = {
  base: "vs-dark",
  inherit: true,
  rules: [
    { token: "comment", foreground: "6A9955" },
    { token: "keyword", foreground: "569CD6" },
    { token: "string", foreground: "CE9178" },
    { token: "number", foreground: "B5CEA8" },
    { token: "function", foreground: "DCDCAA" },
    { token: "type", foreground: "4EC9B0" },
    { token: "variable", foreground: "9CDCFE" },
    { token: "constant", foreground: "4FC1FF" },
    { token: "operator", foreground: "D4D4D4" },
  ],
  colors: {
    "editor.background": "#1e1e2e",
    "editor.foreground": "#cdd6f4",
    "editor.lineHighlightBackground": "#2a2a3e",
    "editor.selectionBackground": "#45475a",
    "editorCursor.foreground": "#f5e0dc",
    "editorLineNumber.foreground": "#6c7086",
    "editorLineNumber.activeForeground": "#cdd6f4",
  },
};
