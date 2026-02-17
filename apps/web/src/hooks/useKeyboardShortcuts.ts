/**
 * Keyboard shortcuts hook for power users.
 *
 * Provides:
 * - Global and scoped keyboard shortcuts
 * - Help overlay state
 * - Customizable bindings
 */

import { useCallback, useEffect, useMemo, useState, useRef } from 'react';

export type ShortcutScope = 'global' | 'dashboard' | 'jobs' | 'editor' | 'modal';

export interface KeyboardShortcut {
  id: string;
  name: string;
  description: string;
  defaultBinding: string;
  currentBinding: string;
  scope: ShortcutScope;
  category: string;
  handler?: () => void;
}

export interface ShortcutConfig {
  key: string;
  ctrl?: boolean;
  shift?: boolean;
  alt?: boolean;
  meta?: boolean;
  handler: () => void;
  scope?: ShortcutScope;
  description?: string;
}

// Default shortcuts configuration
const DEFAULT_SHORTCUTS: KeyboardShortcut[] = [
  // Navigation
  {
    id: 'nav.dashboard',
    name: 'Go to Dashboard',
    description: 'Navigate to the main dashboard',
    defaultBinding: 'g d',
    currentBinding: 'g d',
    scope: 'global',
    category: 'navigation',
  },
  {
    id: 'nav.jobs',
    name: 'Go to Jobs',
    description: 'Navigate to jobs list',
    defaultBinding: 'g j',
    currentBinding: 'g j',
    scope: 'global',
    category: 'navigation',
  },
  {
    id: 'nav.settings',
    name: 'Go to Settings',
    description: 'Navigate to settings page',
    defaultBinding: 'g s',
    currentBinding: 'g s',
    scope: 'global',
    category: 'navigation',
  },
  {
    id: 'nav.profile',
    name: 'Go to Profile',
    description: 'Navigate to user profile',
    defaultBinding: 'g p',
    currentBinding: 'g p',
    scope: 'global',
    category: 'navigation',
  },

  // Job actions
  {
    id: 'jobs.search',
    name: 'Search Jobs',
    description: 'Focus the job search input',
    defaultBinding: '/',
    currentBinding: '/',
    scope: 'dashboard',
    category: 'jobs',
  },
  {
    id: 'jobs.next',
    name: 'Next Job',
    description: 'Navigate to next job in list',
    defaultBinding: 'j',
    currentBinding: 'j',
    scope: 'jobs',
    category: 'jobs',
  },
  {
    id: 'jobs.prev',
    name: 'Previous Job',
    description: 'Navigate to previous job in list',
    defaultBinding: 'k',
    currentBinding: 'k',
    scope: 'jobs',
    category: 'jobs',
  },
  {
    id: 'jobs.apply',
    name: 'Quick Apply',
    description: 'Apply to current job',
    defaultBinding: 'a',
    currentBinding: 'a',
    scope: 'jobs',
    category: 'jobs',
  },
  {
    id: 'jobs.save',
    name: 'Save Job',
    description: 'Save job for later',
    defaultBinding: 's',
    currentBinding: 's',
    scope: 'jobs',
    category: 'jobs',
  },
  {
    id: 'jobs.skip',
    name: 'Skip Job',
    description: 'Skip current job',
    defaultBinding: 'x',
    currentBinding: 'x',
    scope: 'jobs',
    category: 'jobs',
  },

  // Editor actions
  {
    id: 'editor.save',
    name: 'Save',
    description: 'Save current document',
    defaultBinding: 'Ctrl+s',
    currentBinding: 'Ctrl+s',
    scope: 'editor',
    category: 'editor',
  },
  {
    id: 'editor.undo',
    name: 'Undo',
    description: 'Undo last action',
    defaultBinding: 'Ctrl+z',
    currentBinding: 'Ctrl+z',
    scope: 'editor',
    category: 'editor',
  },
  {
    id: 'editor.redo',
    name: 'Redo',
    description: 'Redo last undone action',
    defaultBinding: 'Ctrl+Shift+z',
    currentBinding: 'Ctrl+Shift+z',
    scope: 'editor',
    category: 'editor',
  },

  // General
  {
    id: 'general.help',
    name: 'Show Shortcuts',
    description: 'Show keyboard shortcuts help',
    defaultBinding: '?',
    currentBinding: '?',
    scope: 'global',
    category: 'general',
  },
  {
    id: 'general.escape',
    name: 'Close/Cancel',
    description: 'Close modal or cancel action',
    defaultBinding: 'Escape',
    currentBinding: 'Escape',
    scope: 'global',
    category: 'general',
  },
  {
    id: 'general.search',
    name: 'Global Search',
    description: 'Open global search',
    defaultBinding: 'Ctrl+k',
    currentBinding: 'Ctrl+k',
    scope: 'global',
    category: 'general',
  },
];

// Parse a key binding string like "Ctrl+Shift+s" or "g d"
function parseBinding(binding: string): {
  key: string;
  ctrl: boolean;
  shift: boolean;
  alt: boolean;
  meta: boolean;
  sequence?: string[];
} {
  const parts = binding.split('+').map((p) => p.trim().toLowerCase());
  const sequence = binding.includes(' ') ? binding.split(' ') : undefined;

  if (sequence) {
    return {
      key: sequence[sequence.length - 1].toLowerCase(),
      ctrl: false,
      shift: false,
      alt: false,
      meta: false,
      sequence: sequence.map((s) => s.toLowerCase()),
    };
  }

  const modifiers = {
    ctrl: parts.includes('ctrl'),
    shift: parts.includes('shift'),
    alt: parts.includes('alt'),
    meta: parts.includes('meta') || parts.includes('cmd'),
  };

  const key = parts.find(
    (p) => !['ctrl', 'shift', 'alt', 'meta', 'cmd'].includes(p)
  ) || '';

  return { key, ...modifiers };
}

// Check if an event matches a binding
function matchesBinding(
  event: KeyboardEvent,
  binding: string,
  sequenceState: { keys: string[]; timeout: ReturnType<typeof setTimeout> | null }
): boolean {
  const parsed = parseBinding(binding);

  // Handle key sequences (like "g d")
  if (parsed.sequence) {
    const key = event.key.toLowerCase();

    if (sequenceState.timeout) {
      clearTimeout(sequenceState.timeout);
    }

    const newKeys = [...sequenceState.keys, key];
    const sequenceStr = newKeys.join(' ');

    // Check if sequence matches
    if (binding.toLowerCase() === sequenceStr) {
      sequenceState.keys = [];
      return true;
    }

    // Check if partial match
    if (binding.toLowerCase().startsWith(sequenceStr)) {
      sequenceState.keys = newKeys;
      sequenceState.timeout = setTimeout(() => {
        sequenceState.keys = [];
      }, 1000);
      return false;
    }

    // No match, reset
    sequenceState.keys = [];
    return false;
  }

  // Handle single key with modifiers
  const keyMatch = event.key.toLowerCase() === parsed.key;
  const ctrlMatch = parsed.ctrl === (event.ctrlKey || event.metaKey);
  const shiftMatch = parsed.shift === event.shiftKey;
  const altMatch = parsed.alt === event.altKey;

  return keyMatch && ctrlMatch && shiftMatch && altMatch;
}

/**
 * Hook for managing keyboard shortcuts.
 */
export function useKeyboardShortcuts(
  shortcuts: ShortcutConfig[],
  options: {
    scope?: ShortcutScope;
    enabled?: boolean;
  } = {}
) {
  const { scope = 'global', enabled = true } = options;
  const sequenceState = useRef({ keys: [] as string[], timeout: null as ReturnType<typeof setTimeout> | null });
  const [helpOpen, setHelpOpen] = useState(false);

  // M-9: Store latest shortcuts in a ref so the effect handler always sees
  // the freshest handlers without re-registering the event listener.
  const shortcutsRef = useRef(shortcuts);
  shortcutsRef.current = shortcuts;

  // L-11: Pre-compute binding strings once per shortcut change instead of
  // rebuilding them on every keypress event.
  const bindings = useMemo(
    () =>
      shortcuts.map((s) => {
        const parts: string[] = [];
        if (s.ctrl) parts.push('Ctrl');
        if (s.shift) parts.push('Shift');
        if (s.alt) parts.push('Alt');
        if (s.meta) parts.push('Meta');
        parts.push(s.key);
        return { binding: parts.join('+'), scope: s.scope || 'global' };
      }),
    [shortcuts]
  );
  const bindingsRef = useRef(bindings);
  bindingsRef.current = bindings;

  useEffect(() => {
    if (!enabled) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      // Don't trigger shortcuts when typing in inputs
      const target = event.target as HTMLElement;
      const isInput =
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.isContentEditable;

      // Allow Escape and modifier shortcuts in inputs
      const isEscape = event.key === 'Escape';
      const hasModifier = event.ctrlKey || event.metaKey || event.altKey;

      if (isInput && !isEscape && !hasModifier) {
        return;
      }

      // Check each shortcut using latest refs
      const currentShortcuts = shortcutsRef.current;
      const currentBindings = bindingsRef.current;
      for (let i = 0; i < currentShortcuts.length; i++) {
        const shortcut = currentShortcuts[i];
        const { binding, scope: shortcutScope } = currentBindings[i];

        // Check scope match
        if (shortcutScope !== 'global' && shortcutScope !== scope) {
          continue;
        }

        if (matchesBinding(event, binding, sequenceState.current)) {
          event.preventDefault();
          shortcut.handler();
          return;
        }
      }

      // Show help on "?"
      if (event.key === '?' && !isInput) {
        event.preventDefault();
        setHelpOpen((prev) => !prev);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [scope, enabled]); // M-9: removed `shortcuts` dep — we read from ref instead

  const openHelp = useCallback(() => setHelpOpen(true), []);
  const closeHelp = useCallback(() => setHelpOpen(false), []);

  return { helpOpen, openHelp, closeHelp };
}

/**
 * Hook for showing keyboard shortcuts help.
 */
export function useShortcutsHelp() {
  const [isOpen, setIsOpen] = useState(false);

  const openHelp = useCallback(() => setIsOpen(true), []);
  const closeHelp = useCallback(() => setIsOpen(false), []);
  const toggleHelp = useCallback(() => setIsOpen((prev) => !prev), []);

  const shortcutsByCategory = DEFAULT_SHORTCUTS.reduce(
    (acc, shortcut) => {
      if (!acc[shortcut.category]) {
        acc[shortcut.category] = [];
      }
      acc[shortcut.category].push(shortcut);
      return acc;
    },
    {} as Record<string, KeyboardShortcut[]>
  );

  return {
    isOpen,
    openHelp,
    closeHelp,
    toggleHelp,
    shortcuts: DEFAULT_SHORTCUTS,
    shortcutsByCategory,
  };
}

/**
 * Hook for a single keyboard shortcut.
 * M-9: Uses a ref for the handler to avoid re-registering on every render.
 */
export function useKeyboardShortcut(
  key: string,
  handler: () => void,
  options: {
    ctrl?: boolean;
    shift?: boolean;
    alt?: boolean;
    meta?: boolean;
    enabled?: boolean;
  } = {}
) {
  const { ctrl, shift, alt, meta, enabled = true } = options;

  // M-9: Store handler in ref so we always call the latest without
  // re-registering the keydown listener on every render.
  const handlerRef = useRef(handler);
  handlerRef.current = handler;

  useEffect(() => {
    if (!enabled) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      // Don't trigger shortcuts when typing in inputs
      const target = event.target as HTMLElement;
      const isInput =
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.isContentEditable;

      if (isInput && !event.ctrlKey && !event.metaKey) {
        return;
      }

      const keyMatch = event.key.toLowerCase() === key.toLowerCase();
      const ctrlMatch = ctrl === event.ctrlKey;
      const shiftMatch = shift === event.shiftKey;
      const altMatch = alt === event.altKey;
      const metaMatch = meta === event.metaKey;

      if (keyMatch && ctrlMatch && shiftMatch && altMatch && metaMatch) {
        event.preventDefault();
        handlerRef.current();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [key, ctrl, shift, alt, meta, enabled]); // M-9: removed `handler` from deps
}

export default useKeyboardShortcuts;
