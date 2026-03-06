"""Keyboard shortcuts service for power users.

Provides a centralized registry for keyboard shortcuts with:
- Global and context-sensitive shortcuts
- Conflict detection
- Help overlay
- Customizable key bindings
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

logger = logging.getLogger(__name__)


class ShortcutScope(StrEnum):
    """Scope where shortcut is active."""

    GLOBAL = "global"
    DASHBOARD = "dashboard"
    JOBS = "jobs"
    EDITOR = "editor"
    MODAL = "modal"


@dataclass
class KeyboardShortcut:
    """Represents a keyboard shortcut."""

    id: str
    name: str
    description: str
    default_binding: str
    scope: ShortcutScope = ShortcutScope.GLOBAL
    category: str = "general"
    handler: Callable | None = None
    current_binding: str | None = None

    def __post_init__(self):
        if self.current_binding is None:
            self.current_binding = self.default_binding


class KeyboardShortcutsService:
    """Centralized keyboard shortcuts management.

    Features:
    - Register shortcuts with default bindings
    - Override bindings per user
    - Scope-aware activation
    - Help overlay generation
    """

    def __init__(self):
        self._shortcuts: dict[str, KeyboardShortcut] = {}
        self._bindings: dict[str, str] = {}  # binding -> shortcut_id
        self._user_bindings: dict[str, str] = {}  # User-customized bindings
        self._active_scope: ShortcutScope = ShortcutScope.GLOBAL
        self._enabled: bool = True
        self._register_defaults()

    def _register_defaults(self) -> None:
        """Register default keyboard shortcuts."""
        defaults = [
            # Navigation
            KeyboardShortcut(
                id="nav.dashboard",
                name="Go to Dashboard",
                description="Navigate to the main dashboard",
                default_binding="g d",
                category="navigation",
            ),
            KeyboardShortcut(
                id="nav.jobs",
                name="Go to Jobs",
                description="Navigate to jobs list",
                default_binding="g j",
                category="navigation",
            ),
            KeyboardShortcut(
                id="nav.settings",
                name="Go to Settings",
                description="Navigate to settings page",
                default_binding="g s",
                category="navigation",
            ),
            KeyboardShortcut(
                id="nav.profile",
                name="Go to Profile",
                description="Navigate to user profile",
                default_binding="g p",
                category="navigation",
            ),
            # Job actions
            KeyboardShortcut(
                id="jobs.search",
                name="Search Jobs",
                description="Focus the job search input",
                default_binding="/",
                scope=ShortcutScope.DASHBOARD,
                category="jobs",
            ),
            KeyboardShortcut(
                id="jobs.next",
                name="Next Job",
                description="Navigate to next job in list",
                default_binding="j",
                scope=ShortcutScope.JOBS,
                category="jobs",
            ),
            KeyboardShortcut(
                id="jobs.prev",
                name="Previous Job",
                description="Navigate to previous job in list",
                default_binding="k",
                scope=ShortcutScope.JOBS,
                category="jobs",
            ),
            KeyboardShortcut(
                id="jobs.apply",
                name="Quick Apply",
                description="Apply to current job",
                default_binding="a",
                scope=ShortcutScope.JOBS,
                category="jobs",
            ),
            KeyboardShortcut(
                id="jobs.save",
                name="Save Job",
                description="Save job for later",
                default_binding="s",
                scope=ShortcutScope.JOBS,
                category="jobs",
            ),
            KeyboardShortcut(
                id="jobs.skip",
                name="Skip Job",
                description="Skip current job",
                default_binding="x",
                scope=ShortcutScope.JOBS,
                category="jobs",
            ),
            # Editor actions
            KeyboardShortcut(
                id="editor.save",
                name="Save",
                description="Save current document",
                default_binding="Ctrl+s",
                scope=ShortcutScope.EDITOR,
                category="editor",
            ),
            KeyboardShortcut(
                id="editor.undo",
                name="Undo",
                description="Undo last action",
                default_binding="Ctrl+z",
                scope=ShortcutScope.EDITOR,
                category="editor",
            ),
            KeyboardShortcut(
                id="editor.redo",
                name="Redo",
                description="Redo last undone action",
                default_binding="Ctrl+Shift+z",
                scope=ShortcutScope.EDITOR,
                category="editor",
            ),
            KeyboardShortcut(
                id="editor.format",
                name="Format",
                description="Auto-format document",
                default_binding="Ctrl+Shift+f",
                scope=ShortcutScope.EDITOR,
                category="editor",
            ),
            # General
            KeyboardShortcut(
                id="general.help",
                name="Show Shortcuts",
                description="Show keyboard shortcuts help",
                default_binding="?",
                category="general",
            ),
            KeyboardShortcut(
                id="general.escape",
                name="Close/Cancel",
                description="Close modal or cancel action",
                default_binding="Escape",
                category="general",
            ),
            KeyboardShortcut(
                id="general.search",
                name="Global Search",
                description="Open global search",
                default_binding="Ctrl+k",
                category="general",
            ),
        ]

        for shortcut in defaults:
            self.register(shortcut)

    def register(self, shortcut: KeyboardShortcut) -> None:
        """Register a keyboard shortcut."""
        if shortcut.id in self._shortcuts:
            logger.warning(f"Overwriting existing shortcut: {shortcut.id}")

        self._shortcuts[shortcut.id] = shortcut
        binding = shortcut.current_binding or shortcut.default_binding
        self._bindings[binding] = shortcut.id
        logger.debug(f"Registered shortcut: {shortcut.id} -> {binding}")

    def unregister(self, shortcut_id: str) -> bool:
        """Unregister a keyboard shortcut."""
        if shortcut_id not in self._shortcuts:
            return False

        shortcut = self._shortcuts[shortcut_id]
        binding = shortcut.current_binding or shortcut.default_binding
        del self._shortcuts[shortcut_id]
        if binding in self._bindings and self._bindings[binding] == shortcut_id:
            del self._bindings[binding]

        return True

    def get(self, shortcut_id: str) -> KeyboardShortcut | None:
        """Get a shortcut by ID."""
        return self._shortcuts.get(shortcut_id)

    def get_by_binding(self, binding: str) -> KeyboardShortcut | None:
        """Get a shortcut by its key binding."""
        shortcut_id = self._bindings.get(binding)
        if shortcut_id:
            return self._shortcuts.get(shortcut_id)
        return None

    def set_binding(self, shortcut_id: str, new_binding: str) -> bool:
        """Set a custom binding for a shortcut."""
        if shortcut_id not in self._shortcuts:
            return False

        # Check for conflicts
        if new_binding in self._bindings:
            existing_id = self._bindings[new_binding]
            if existing_id != shortcut_id:
                logger.warning(
                    f"Binding conflict: {new_binding} already used by {existing_id}"
                )
                return False

        shortcut = self._shortcuts[shortcut_id]
        old_binding = shortcut.current_binding or shortcut.default_binding

        # Update bindings
        if old_binding in self._bindings and self._bindings[old_binding] == shortcut_id:
            del self._bindings[old_binding]

        shortcut.current_binding = new_binding
        self._bindings[new_binding] = shortcut_id
        self._user_bindings[shortcut_id] = new_binding

        return True

    def reset_binding(self, shortcut_id: str) -> bool:
        """Reset a shortcut to its default binding."""
        if shortcut_id not in self._shortcuts:
            return False

        shortcut = self._shortcuts[shortcut_id]
        current = shortcut.current_binding or shortcut.default_binding

        if current in self._bindings and self._bindings[current] == shortcut_id:
            del self._bindings[current]

        shortcut.current_binding = shortcut.default_binding
        self._bindings[shortcut.default_binding] = shortcut_id

        if shortcut_id in self._user_bindings:
            del self._user_bindings[shortcut_id]

        return True

    def set_scope(self, scope: ShortcutScope) -> None:
        """Set the active scope for context-sensitive shortcuts."""
        self._active_scope = scope
        logger.debug(f"Active scope changed to: {scope}")

    def get_active_shortcuts(self) -> list[KeyboardShortcut]:
        """Get shortcuts active in current scope."""
        return [
            s
            for s in self._shortcuts.values()
            if s.scope == ShortcutScope.GLOBAL or s.scope == self._active_scope
        ]

    def get_all(self) -> list[KeyboardShortcut]:
        """Get all registered shortcuts."""
        return list(self._shortcuts.values())

    def get_by_category(self, category: str) -> list[KeyboardShortcut]:
        """Get shortcuts by category."""
        return [s for s in self._shortcuts.values() if s.category == category]

    def get_categories(self) -> list[str]:
        """Get all shortcut categories."""
        return list(set(s.category for s in self._shortcuts.values()))

    def get_user_bindings(self) -> dict[str, str]:
        """Get user-customized bindings for persistence."""
        return self._user_bindings.copy()

    def load_user_bindings(self, bindings: dict[str, str]) -> None:
        """Load user-customized bindings from storage."""
        for shortcut_id, binding in bindings.items():
            self.set_binding(shortcut_id, binding)

    def enable(self) -> None:
        """Enable keyboard shortcuts."""
        self._enabled = True

    def disable(self) -> None:
        """Disable keyboard shortcuts."""
        self._enabled = False

    def is_enabled(self) -> bool:
        """Check if shortcuts are enabled."""
        return self._enabled

    def get_help_data(self) -> dict[str, list[dict]]:
        """Get help data for rendering shortcuts overlay."""
        categories: dict[str, list[dict]] = {}

        for shortcut in self.get_active_shortcuts():
            if shortcut.category not in categories:
                categories[shortcut.category] = []

            categories[shortcut.category].append(
                {
                    "id": shortcut.id,
                    "name": shortcut.name,
                    "description": shortcut.description,
                    "binding": shortcut.current_binding or shortcut.default_binding,
                    "scope": shortcut.scope.value,
                }
            )

        return categories


# Global instance
_shortcuts_service: KeyboardShortcutsService | None = None


def get_shortcuts_service() -> KeyboardShortcutsService:
    """Get the global keyboard shortcuts service."""
    global _shortcuts_service
    if _shortcuts_service is None:
        _shortcuts_service = KeyboardShortcutsService()
    return _shortcuts_service
