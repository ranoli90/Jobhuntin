"""Replace Sparkles icon with appropriate alternatives in public-facing pages."""
import re

# Map of files to fix with their Sparkles replacement icon
files_to_fix = {
    # Public-facing pages
    "apps/web/src/pages/NotFound.tsx": "Compass",
    "apps/web/src/pages/JobNiche.tsx": "Target",
    "apps/web/src/pages/GuidesHome.tsx": "BookOpen",
    "apps/web/src/pages/ComparisonPage.tsx": "BarChart3",
    "apps/web/src/pages/CategoryHub.tsx": "Layers",
    "apps/web/src/pages/AlternativeTo.tsx": "ArrowLeftRight",
    # Onboarding
    "apps/web/src/pages/app/Onboarding.tsx": "Zap",
    "apps/web/src/pages/app/onboarding/steps/WelcomeStep.tsx": "Rocket",
    "apps/web/src/pages/app/onboarding/steps/ResumeStep.tsx": "FileText",
    "apps/web/src/pages/app/onboarding/steps/SkillReviewStep.tsx": "CheckCircle2",
    "apps/web/src/pages/app/onboarding/steps/ConfirmContactStep.tsx": "UserCheck",
    # Internal app components (less critical but still AI-looking)
    "apps/web/src/components/trust/HowItWorksCard.tsx": "Zap",
}

for filepath, replacement_icon in files_to_fix.items():
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        
        # Replace in import statement - handle various import patterns
        # Pattern: Sparkles in import from lucide-react
        # Replace Sparkles with the new icon, but only if the new icon isn't already imported
        if replacement_icon not in content.split('\n')[0:30].__repr__():
            # Simple case: just replace Sparkles with replacement in the import
            content = content.replace(
                f"Sparkles,", f"{replacement_icon},", 1
            )
            if "Sparkles," not in content and "Sparkles " in content:
                content = content.replace(
                    f"Sparkles ", f"{replacement_icon} ", 1
                )
            if "Sparkles}" in content:
                content = content.replace(
                    f"Sparkles}}", f"{replacement_icon}}}", 1
                )
                content = content.replace(
                    f"Sparkles }}", f"{replacement_icon} }}", 1
                )
        else:
            # Icon already imported, just remove Sparkles from import
            content = content.replace("Sparkles, ", "")
            content = content.replace(", Sparkles", "")
            content = content.replace("Sparkles,", "")
        
        # Replace all JSX usage: <Sparkles -> <replacement_icon
        content = content.replace("<Sparkles", f"<{replacement_icon}")
        
        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ Fixed {filepath}: Sparkles → {replacement_icon}")
        else:
            print(f"  Skipped {filepath}: no changes needed")
    except FileNotFoundError:
        print(f"  Skipped {filepath}: file not found")
    except Exception as e:
        print(f"  Error {filepath}: {e}")

print("\nDone!")
