#!/usr/bin/env python3
"""CLI scaffolder for new Agent Blueprints.

Usage:
    python scripts/create_blueprint.py --name "Vendor Onboarding" --slug vendor-onboard
    python scripts/create_blueprint.py --name "College Applications" --slug college-app

Creates:
    backend/blueprints/{slug}/
        __init__.py
        blueprint.py
        models.py
        prompts.py
    supabase/migrations/{next_num}_{slug}.sql
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = ROOT / "templates" / "blueprint_template"
BLUEPRINTS_DIR = ROOT / "backend" / "blueprints"
MIGRATIONS_DIR = ROOT / "supabase" / "migrations"


def slug_to_class_name(slug: str) -> str:
    """Convert 'vendor-onboard' → 'VendorOnboardBlueprint'."""
    parts = slug.replace("_", "-").split("-")
    return "".join(p.capitalize() for p in parts) + "Blueprint"


def slug_to_profile_class(slug: str) -> str:
    """Convert 'vendor-onboard' → 'VendorOnboardProfile'."""
    parts = slug.replace("_", "-").split("-")
    return "".join(p.capitalize() for p in parts) + "Profile"


def slug_to_name(slug: str) -> str:
    """Convert 'vendor-onboard' → 'Vendor Onboard'."""
    return slug.replace("-", " ").replace("_", " ").title()


def next_migration_number() -> str:
    """Find the next migration number (e.g., '008')."""
    existing = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not existing:
        return "001"
    last = existing[-1].stem.split("_")[0]
    return str(int(last) + 1).zfill(3)


def render_template(template_path: Path, context: dict[str, str]) -> str:
    """Read a .tmpl file and substitute {{key}} placeholders."""
    content = template_path.read_text(encoding="utf-8")
    for key, value in context.items():
        content = content.replace("{{" + key + "}}", value)
    return content


def create_blueprint(name: str, slug: str, description: str = "") -> None:
    """Create a new blueprint from the template."""
    # Validate slug
    if not re.match(r"^[a-z][a-z0-9-]*$", slug):
        print(f"ERROR: slug must be lowercase alphanumeric with hyphens: '{slug}'", file=sys.stderr)
        sys.exit(1)

    target_dir = BLUEPRINTS_DIR / slug.replace("-", "_")
    if target_dir.exists():
        print(f"ERROR: Blueprint directory already exists: {target_dir}", file=sys.stderr)
        sys.exit(1)

    class_name = slug_to_class_name(slug)
    profile_class = slug_to_profile_class(slug)
    if not name:
        name = slug_to_name(slug)
    if not description:
        description = f"Auto-generated blueprint for {name}"

    context = {
        "blueprint_name": name,
        "slug": slug.replace("-", "_"),
        "class_name": class_name,
        "profile_class": profile_class,
        "description": description,
    }

    # Create blueprint directory
    target_dir.mkdir(parents=True, exist_ok=True)
    print(f"Created directory: {target_dir}")

    # Render and write each template file
    template_files = {
        "__init__.py.tmpl": "__init__.py",
        "blueprint.py.tmpl": "blueprint.py",
        "models.py.tmpl": "models.py",
        "prompts.py.tmpl": "prompts.py",
    }

    for tmpl_name, output_name in template_files.items():
        tmpl_path = TEMPLATE_DIR / tmpl_name
        if not tmpl_path.exists():
            print(f"WARNING: Template not found: {tmpl_path}", file=sys.stderr)
            continue
        content = render_template(tmpl_path, context)
        output_path = target_dir / output_name
        output_path.write_text(content, encoding="utf-8")
        print(f"  Created: {output_path.relative_to(ROOT)}")

    # Generate schema patch migration
    schema_tmpl = TEMPLATE_DIR / "schema_patch.sql.tmpl"
    if schema_tmpl.exists():
        migration_num = next_migration_number()
        migration_name = f"{migration_num}_{slug.replace('-', '_')}.sql"
        migration_path = MIGRATIONS_DIR / migration_name
        content = render_template(schema_tmpl, context)
        migration_path.write_text(content, encoding="utf-8")
        print(f"  Created: {migration_path.relative_to(ROOT)}")

    # Print next steps
    print(f"\n✓ Blueprint '{name}' created successfully!")
    print("\nNext steps:")
    print(f"  1. Edit backend/blueprints/{slug.replace('-', '_')}/models.py — add vertical-specific fields")
    print(f"  2. Edit backend/blueprints/{slug.replace('-', '_')}/prompts.py — customize LLM prompts")
    print(f"  3. Edit backend/blueprints/{slug.replace('-', '_')}/blueprint.py — implement all methods")
    print("  4. Register in backend/blueprints/registry.py → load_default_blueprints()")
    print(f"  5. Add '{slug}' to ENABLED_BLUEPRINTS in your .env or config")
    print("  6. Run the schema migration if you added custom tables/columns")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scaffold a new Agent Blueprint from the template.",
    )
    parser.add_argument(
        "--name",
        type=str,
        default="",
        help='Human-readable name (e.g., "Vendor Onboarding")',
    )
    parser.add_argument(
        "--slug",
        type=str,
        required=True,
        help='Unique key for the blueprint (e.g., "vendor-onboard")',
    )
    parser.add_argument(
        "--description",
        type=str,
        default="",
        help="Short description of the blueprint",
    )

    args = parser.parse_args()
    create_blueprint(args.name, args.slug, args.description)


if __name__ == "__main__":
    main()
