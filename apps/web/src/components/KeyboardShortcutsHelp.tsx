/**
 * M8: Keyboard Navigation - Keyboard shortcuts help modal
 *
 * Displays available keyboard shortcuts to users.
 */

import * as React from "react";
import { FocusTrap } from "focus-trap-react";
import { X, Keyboard } from "lucide-react";
import { Button } from "./ui/Button";
import { Card } from "./ui/Card";
import { COMMON_SHORTCUTS } from "../hooks/useKeyboardShortcuts";

interface KeyboardShortcutsHelpProperties {
  isOpen: boolean;
  onClose: () => void;
}

export function KeyboardShortcutsHelp({
  isOpen,
  onClose,
}: KeyboardShortcutsHelpProperties) {
  const cardReference = React.useRef<HTMLDivElement>(null);

  if (!isOpen) return null;

  const shortcuts = [
    {
      category: "Navigation",
      items: [
        { ...COMMON_SHORTCUTS.GO_TO_DASHBOARD, keys: "Ctrl+D" },
        { ...COMMON_SHORTCUTS.GO_TO_JOBS, keys: "Ctrl+J" },
        { ...COMMON_SHORTCUTS.GO_TO_APPLICATIONS, keys: "Ctrl+A" },
        { ...COMMON_SHORTCUTS.GO_TO_SETTINGS, keys: "Ctrl+," },
      ],
    },
    {
      category: "Actions",
      items: [
        { ...COMMON_SHORTCUTS.SEARCH, keys: "Ctrl+K" },
        { ...COMMON_SHORTCUTS.NEW_APPLICATION, keys: "Ctrl+N" },
      ],
    },
    {
      category: "UI",
      items: [
        { ...COMMON_SHORTCUTS.TOGGLE_DARK_MODE, keys: "Ctrl+Shift+D" },
        { ...COMMON_SHORTCUTS.CLOSE_MODAL, keys: "Esc" },
      ],
    },
  ];

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 dark:bg-black/70"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="keyboard-shortcuts-title"
    >
      <FocusTrap
        active={isOpen}
        focusTrapOptions={{
          initialFocus: () =>
            cardReference.current?.querySelector<HTMLElement>("button") ??
            false,
          allowOutsideClick: true,
          escapeDeactivates: true,
          returnFocusOnDeactivate: true,
          onDeactivate: onClose,
        }}
      >
        <Card
          ref={cardReference}
          className="w-full max-w-2xl max-h-[80vh] overflow-y-auto bg-white dark:bg-slate-800"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="flex items-center justify-between p-6 border-b border-slate-200 dark:border-slate-700">
            <div className="flex items-center gap-3">
              <Keyboard className="w-5 h-5 text-slate-600 dark:text-slate-400" />
              <h2
                id="keyboard-shortcuts-title"
                className="text-xl font-bold text-slate-900 dark:text-slate-100"
              >
                Keyboard Shortcuts
              </h2>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={onClose}
              aria-label="Close keyboard shortcuts help"
            >
              <X className="w-4 h-4" />
            </Button>
          </div>

          <div className="p-6 space-y-6">
            {shortcuts.map((category) => (
              <div key={category.category}>
                <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3 uppercase tracking-wide">
                  {category.category}
                </h3>
                <div className="space-y-2">
                  {category.items.map((item, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between py-2 px-3 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700/50"
                    >
                      <span className="text-sm text-slate-600 dark:text-slate-400">
                        {item.description}
                      </span>
                      <kbd className="px-2 py-1 text-xs font-mono bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 rounded border border-slate-300 dark:border-slate-600">
                        {item.keys || item.key}
                      </kbd>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <div className="p-6 border-t border-slate-200 dark:border-slate-700">
            <Button onClick={onClose} className="w-full">
              Close
            </Button>
          </div>
        </Card>
      </FocusTrap>
    </div>
  );
}
