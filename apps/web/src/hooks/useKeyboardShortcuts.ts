/**
 * M8: Keyboard Navigation - Comprehensive keyboard shortcuts hook
 *
 * Provides keyboard shortcuts for common actions across the application.
 * WCAG 2.1 AA requirement for keyboard accessibility.
 */

import { useEffect, useCallback } from "react";

export interface KeyboardShortcut {
  key: string;
  ctrl?: boolean;
  shift?: boolean;
  alt?: boolean;
  meta?: boolean;
  action: () => void;
  description: string;
  preventDefault?: boolean;
}

export function useKeyboardShortcuts(
  shortcuts: KeyboardShortcut[],
  enabled: boolean = true,
) {
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (!enabled) return;

      const el = document.activeElement;
      if (
        el &&
        (el.tagName === "INPUT" ||
          el.tagName === "TEXTAREA" ||
          el.getAttribute("contenteditable") === "true")
      ) {
        return;
      }

      for (const shortcut of shortcuts) {
        const keyMatch =
          event.key === shortcut.key ||
          event.key.toLowerCase() === shortcut.key.toLowerCase();
        const ctrlMatch = shortcut.ctrl
          ? event.ctrlKey || event.metaKey
          : !event.ctrlKey && !event.metaKey;
        const shiftMatch = shortcut.shift ? event.shiftKey : !event.shiftKey;
        const altMatch = shortcut.alt ? event.altKey : !event.altKey;

        if (keyMatch && ctrlMatch && shiftMatch && altMatch) {
          if (shortcut.preventDefault !== false) {
            event.preventDefault();
          }
          shortcut.action();
          break;
        }
      }
    },
    [shortcuts, enabled],
  );

  useEffect(() => {
    if (!enabled) return;

    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [handleKeyDown, enabled]);
}

// Common keyboard shortcuts for the application
export const COMMON_SHORTCUTS = {
  // Navigation
  GO_TO_DASHBOARD: { key: "d", ctrl: true, description: "Go to Dashboard" },
  GO_TO_JOBS: { key: "j", ctrl: true, description: "Go to Jobs" },
  GO_TO_APPLICATIONS: {
    key: "a",
    ctrl: true,
    description: "Go to Applications",
  },
  GO_TO_SETTINGS: { key: ",", ctrl: true, description: "Go to Settings" },

  // Actions
  NEW_APPLICATION: { key: "n", ctrl: true, description: "New Application" },
  SEARCH: { key: "k", ctrl: true, description: "Search" },
  HELP: { key: "?", shift: true, description: "Show Help" },

  // UI
  TOGGLE_DARK_MODE: {
    key: "d",
    ctrl: true,
    shift: true,
    description: "Toggle Dark Mode",
  },
  CLOSE_MODAL: { key: "Escape", description: "Close Modal/Dialog" },
};
