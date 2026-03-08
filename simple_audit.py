#!/usr/bin/env python3
"""
Simple Phase Audit: Quick verification of all phases 1-16.

This script provides a simplified audit of all development phases to identify
missing components and verify system completeness. It serves as a quick check before
running the comprehensive audit.

Usage:
    python simple_audit.py

Outputs:
    - Console report of audit findings
    - Missing components list
    - Overall audit status

Author: JobHuntin Development Team
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from datetime import datetime

# Add project root to Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('simple_audit.log')
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class AuditCheck:
    """"Data class for individual audit checks."""
    category: str
    name: str
    path: str
    description: str
    exists: bool
    status: str
    details: Optional[str] = None

@dataclass
class PhaseAuditResult:
    """"Data class for phase audit results."""
    phase_name: str
    total_checks: int
    passed_checks: int
    failed_checks: int
    missing_items: List[str]
    status: str
    timestamp: datetime

class SimplePhaseAuditor:
    """"Simple auditor for all phases 1-16.
    
    This class provides a quick verification of all development phases to identify
    missing components and ensure system completeness. It's designed for rapid
    assessment before running the comprehensive audit.
    
    Attributes:
        missing_items: List of identified missing components
        issues_found: List of identified issues
        phase_results: Dictionary storing results for each phase
    """
    
    def __init__(self) -> None:
        """Initialize the simple auditor."""
        self.missing_items: List[str] = []
        self.issues_found: List[str] = []
        self.phase_results: Dict[str, PhaseAuditResult] = {}
        logger.info("Initialized SimplePhaseAuditor")

def check_file_exists(file_path):
    """Check if file exists."""
    return os.path.exists(file_path)

def check_table_exists(table_name):
    """Check if table exists in migration files."""
    migrations_dir = Path("migrations")
    if not migrations_dir.exists():
        return False
    
    for migration_file in migrations_dir.glob("*.sql"):
        try:
            with open(migration_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # More flexible table detection
                if (f"CREATE TABLE.*{table_name}" in content or 
                    f"CREATE TABLE IF NOT EXISTS.*{table_name}" in content or
                    f"{table_name}" in content):
                    return True
        except Exception:
            continue
    
    return False

def audit_all_phases():
    """Audit all phases for missing components."""
    print("=" * 80)
    print("COMPREHENSIVE PHASE AUDIT 1-16")
    print("=" * 80)
    
    all_issues = []
    
    # Phase 1-5: Foundation
    print("\nPHASE 1-5: FOUNDATION")
    print("-" * 40)
    
    foundation_checks = [
        ("Core Tables", [
            ("tenants", check_table_exists("tenants")),
            ("users", check_table_exists("users")),
            ("jobs", check_table_exists("jobs")),
            ("applications", check_table_exists("applications")),
            ("events", check_table_exists("events")),
        ]),
        ("Core APIs", [
            ("apps/api/auth.py", check_file_exists("apps/api/auth.py")),
            ("apps/api/user.py", check_file_exists("apps/api/user.py")),
            ("apps/api/dashboard.py", check_file_exists("apps/api/dashboard.py")),
            ("apps/api/admin.py", check_file_exists("apps/api/admin.py")),
        ]),
        ("Auth System", [
            ("packages/backend/domain/tenant.py", check_file_exists("packages/backend/domain/tenant.py")),
            ("packages/backend/domain/repositories.py", check_file_exists("packages/backend/domain/repositories.py")),
        ]),
        ("Frontend Core", [
            ("apps/web/src/App.tsx", check_file_exists("apps/web/src/App.tsx")),
            ("apps/web/src/main.tsx", check_file_exists("apps/web/src/main.tsx")),
            ("apps/web/src/index.css", check_file_exists("apps/web/src/index.css")),
        ]),
        ("Shared Libraries", [
            ("shared/config.py", check_file_exists("shared/config.py")),
            ("shared/logging_config.py", check_file_exists("shared/logging_config.py")),
            ("shared/metrics.py", check_file_exists("shared/metrics.py")),
            ("shared/redis_client.py", check_file_exists("shared/redis_client.py")),
        ])
    ]
    
    for category, items in foundation_checks:
        print(f"\n{category}:")
        for name, exists in items:
            status = "OK" if exists else "MISSING"
            print(f"  {name}: {status}")
            if not exists:
                all_issues.append(f"Foundation - {category}: {name}")
    
    # Phase 6: Backend Reliability
    print("\nPHASE 6: BACKEND RELIABILITY")
    print("-" * 40)
    
    reliability_checks = [
        ("Error Handling", [
            ("packages/backend/domain/repositories.py", check_file_exists("packages/backend/domain/repositories.py")),
            ("apps/api/main.py", check_file_exists("apps/api/main.py")),
        ]),
        ("Monitoring", [
            ("shared/telemetry.py", check_file_exists("shared/telemetry.py")),
            ("shared/metrics.py", check_file_exists("shared/metrics.py")),
            ("shared/logging_config.py", check_file_exists("shared/logging_config.py")),
        ]),
        ("Performance", [
            ("shared/redis_client.py", check_file_exists("shared/redis_client.py")),
        ]),
        ("Security", [
            ("packages/backend/domain/tenant.py", check_file_exists("packages/backend/domain/tenant.py")),
            ("apps/api/admin_security.py", check_file_exists("apps/api/admin_security.py")),
        ])
    ]
    
    for category, items in reliability_checks:
        print(f"\n{category}:")
        for name, exists in items:
            status = "OK" if exists else "MISSING"
            print(f"  {name}: {status}")
            if not exists:
                all_issues.append(f"Backend Reliability - {category}: {name}")
    
    # Phase 7: Design System
    print("\nPHASE 7: DESIGN SYSTEM")
    print("-" * 40)
    
    design_checks = [
        ("UI Components", [
            ("apps/web/src/components/ui/ButtonStyles.tsx", check_file_exists("apps/web/src/components/ui/ButtonStyles.tsx")),
            ("apps/web/src/components/ui/CardStyles.tsx", check_file_exists("apps/web/src/components/ui/CardStyles.tsx")),
            ("apps/web/src/components/ui/SkeletonLoader.tsx", check_file_exists("apps/web/src/components/ui/SkeletonLoader.tsx")),
        ]),
        ("Styling", [
            ("apps/web/src/index.css", check_file_exists("apps/web/src/index.css")),
            ("apps/web/src/styles/globals.css", check_file_exists("apps/web/src/styles/globals.css")),
        ]),
        ("Marketing", [
            ("apps/web/src/components/marketing/MarketingNavbar.tsx", check_file_exists("apps/web/src/components/marketing/MarketingNavbar.tsx")),
            ("apps/web/src/components/marketing/SwitchFrom.tsx", check_file_exists("apps/web/src/components/marketing/SwitchFrom.tsx")),
            ("apps/web/src/components/marketing/SuccessStories.tsx", check_file_exists("apps/web/src/components/marketing/SuccessStories.tsx")),
        ])
    ]
    
    for category, items in design_checks:
        print(f"\n{category}:")
        for name, exists in items:
            status = "OK" if exists else "MISSING"
            print(f"  {name}: {status}")
            if not exists:
                all_issues.append(f"Design System - {category}: {name}")
    
    # Phase 8: Typography & Layout
    print("\nPHASE 8: TYPOGRAPHY & LAYOUT")
    print("-" * 40)
    
    typography_checks = [
        ("Typography", [
            ("apps/web/src/styles/typography.css", check_file_exists("apps/web/src/styles/typography.css")),
            ("apps/web/src/index.css", check_file_exists("apps/web/src/index.css")),
        ]),
        ("Layout", [
            ("apps/web/src/layouts/AppLayout.tsx", check_file_exists("apps/web/src/layouts/AppLayout.tsx")),
            ("apps/web/src/components/marketing/SwitchFrom.tsx", check_file_exists("apps/web/src/components/marketing/SwitchFrom.tsx")),
        ])
    ]
    
    for category, items in typography_checks:
        print(f"\n{category}:")
        for name, exists in items:
            status = "OK" if exists else "MISSING"
            print(f"  {name}: {status}")
            if not exists:
                all_issues.append(f"Typography & Layout - {category}: {name}")
    
    # Phase 9: Mobile Optimization
    print("\nPHASE 9: MOBILE OPTIMIZATION")
    print("-" * 40)
    
    mobile_checks = [
        ("Mobile Components", [
            ("apps/web/src/components/marketing/MarketingNavbar.tsx", check_file_exists("apps/web/src/components/marketing/MarketingNavbar.tsx")),
            ("apps/web/src/components/navigation/MobileMenu.tsx", check_file_exists("apps/web/src/components/navigation/MobileMenu.tsx")),
        ]),
        ("Responsive CSS", [
            ("apps/web/src/index.css", check_file_exists("apps/web/src/index.css")),
            ("apps/web/src/styles/typography.css", check_file_exists("apps/web/src/styles/typography.css")),
        ])
    ]
    
    for category, items in mobile_checks:
        print(f"\n{category}:")
        for name, exists in items:
            status = "OK" if exists else "MISSING"
            print(f"  {name}: {status}")
            if not exists:
                all_issues.append(f"Mobile Optimization - {category}: {name}")
    
    # Phase 10: Accessibility
    print("\nPHASE 10: ACCESSIBILITY")
    print("-" * 40)
    
    a11y_checks = [
        ("A11y Components", [
            ("apps/web/src/components/FocusTrap.tsx", check_file_exists("apps/web/src/components/FocusTrap.tsx")),
            ("apps/web/src/components/ui/ButtonStyles.tsx", check_file_exists("apps/web/src/components/ui/ButtonStyles.tsx")),
        ]),
        ("Keyboard Navigation", [
            ("apps/web/src/components/navigation/Navigation.tsx", check_file_exists("apps/web/src/components/navigation/Navigation.tsx")),
        ])
    ]
    
    for category, items in a11y_checks:
        print(f"\n{category}:")
        for name, exists in items:
            status = "OK" if exists else "MISSING"
            print(f"  {name}: {status}")
            if not exists:
                all_issues.append(f"Accessibility - {category}: {name}")
    
    # Phase 11: AI System
    print("\nPHASE 11: AI SYSTEM")
    print("-" * 40)
    
    ai_checks = [
        ("AI Domain", [
            ("packages/backend/domain/document_processor.py", check_file_exists("packages/backend/domain/document_processor.py")),
            ("packages/backend/domain/skills_taxonomy.py", check_file_exists("packages/backend/domain/skills_taxonomy.py")),
            ("packages/backend/domain/resume.py", check_file_exists("packages/backend/domain/resume.py")),
            ("packages/backend/domain/ab_testing.py", check_file_exists("packages/backend/domain/ab_testing.py")),
            ("packages/backend/domain/llm_career_path.py", check_file_exists("packages/backend/domain/llm_career_path.py")),
            ("packages/backend/domain/voice_interviews.py", check_file_exists("packages/backend/domain/voice_interviews.py")),
            ("packages/backend/domain/ai_onboarding.py", check_file_exists("packages/backend/domain/ai_onboarding.py")),
        ]),
        ("AI APIs", [
            ("apps/api/ai_endpoints.py", check_file_exists("apps/api/ai_endpoints.py")),
            ("apps/api/skills.py", check_file_exists("apps/api/skills.py")),
            ("apps/api/ats_recommendations.py", check_file_exists("apps/api/ats_recommendations.py")),
            ("apps/api/voice_interviews.py", check_file_exists("apps/api/voice_interviews.py")),
            ("apps/api/llm_career_path.py", check_file_exists("apps/api/llm_career_path.py")),
            ("apps/api/ai_onboarding.py", check_file_exists("apps/api/ai_onboarding.py")),
            ("apps/api/ab_testing.py", check_file_exists("apps/api/ab_testing.py")),
        ]),
        ("AI Tables", [
            ("skills_taxonomy", check_table_exists("skills_taxonomy")),
            ("ab_testing_experiments", check_table_exists("ab_testing_experiments")),
            ("interview_sessions", check_table_exists("interview_sessions")),
            ("voice_interview_sessions", check_table_exists("voice_interview_sessions")),
        ])
    ]
    
    for category, items in ai_checks:
        print(f"\n{category}:")
        for name, exists in items:
            status = "OK" if exists else "MISSING"
            print(f"  {name}: {status}")
            if not exists:
                all_issues.append(f"AI System - {category}: {name}")
    
    # Phase 12: Agent Improvements
    print("\nPHASE 12: AGENT IMPROVEMENTS")
    print("-" * 40)
    
    agent_checks = [
        ("Agent Domain", [
            ("packages/backend/domain/agent_improvements.py", check_file_exists("packages/backend/domain/agent_improvements.py")),
            ("packages/backend/domain/oauth_handler.py", check_file_exists("packages/backend/domain/oauth_handler.py")),
            ("packages/backend/domain/concurrent_tracker.py", check_file_exists("packages/backend/domain/concurrent_tracker.py")),
            ("packages/backend/domain/dlq_manager.py", check_file_exists("packages/backend/domain/dlq_manager.py")),
        ]),
        ("Agent APIs", [
            ("apps/api/agent_improvements_endpoints.py", check_file_exists("apps/api/agent_improvements_endpoints.py")),
            ("apps/api/oauth_endpoints.py", check_file_exists("apps/api/oauth_endpoints.py")),
            ("apps/api/concurrent_usage_endpoints.py", check_file_exists("apps/api/concurrent_usage_endpoints.py")),
            ("apps/api/dlq_endpoints.py", check_file_exists("apps/api/dlq_endpoints.py")),
            ("apps/api/screenshot_endpoints.py", check_file_exists("apps/api/screenshot_endpoints.py")),
        ]),
        ("Agent Frontend", [
            ("apps/web/src/components/agent-improvements/OAuthHandler.tsx", check_file_exists("apps/web/src/components/agent-improvements/OAuthHandler.tsx")),
            ("apps/web/src/components/agent-improvements/ConcurrentUsageMonitor.tsx", check_file_exists("apps/web/src/components/agent-improvements/ConcurrentUsageMonitor.tsx")),
            ("apps/web/src/components/agent-improvements/DLQDashboard.tsx", check_file_exists("apps/web/src/components/agent-improvements/DLQDashboard.tsx")),
            ("apps/web/src/components/agent-improvements/ScreenshotCapture.tsx", check_file_exists("apps/web/src/components/agent-improvements/ScreenshotCapture.tsx")),
            ("apps/web/src/components/agent-improvements/DocumentProcessor.tsx", check_file_exists("apps/web/src/components/agent-improvements/DocumentProcessor.tsx")),
            ("apps/web/src/components/agent-improvements/PerformanceMetrics.tsx", check_file_exists("apps/web/src/components/agent-improvements/PerformanceMetrics.tsx")),
        ]),
        ("Agent Tables", [
            ("button_detections", check_table_exists("button_detections")),
            ("form_field_detections", check_table_exists("form_field_detections")),
            ("oauth_credentials", check_table_exists("oauth_credentials")),
            ("concurrent_usage_sessions", check_table_exists("concurrent_usage_sessions")),
            ("dead_letter_queue", check_table_exists("dead_letter_queue")),
            ("screenshot_captures", check_table_exists("screenshot_captures")),
            ("document_type_tracking", check_table_exists("document_type_tracking")),
            ("agent_performance_metrics", check_table_exists("agent_performance_metrics")),
        ])
    ]
    
    for category, items in agent_checks:
        print(f"\n{category}:")
        for name, exists in items:
            status = "OK" if exists else "MISSING"
            print(f"  {name}: {status}")
            if not exists:
                all_issues.append(f"Agent Improvements - {category}: {name}")
    
    # Phase 13: Communication System
    print("\nPHASE 13: COMMUNICATION SYSTEM")
    print("-" * 40)
    
    comm_checks = [
        ("Comm Domain", [
            ("packages/backend/domain/email_communications.py", check_file_exists("packages/backend/domain/email_communications.py")),
            ("packages/backend/domain/enhanced_notifications.py", check_file_exists("packages/backend/domain/enhanced_notifications.py")),
        ]),
        ("Comm APIs", [
            ("apps/api/communication_endpoints.py", check_file_exists("apps/api/communication_endpoints.py")),
        ]),
        ("Comm Tables", [
            ("email_communications_log", check_table_exists("email_communications_log")),
            ("email_preferences", check_table_exists("email_preferences")),
            ("user_preferences", check_table_exists("user_preferences")),
            ("notification_semantic_tags", check_table_exists("notification_semantic_tags")),
            ("user_interests", check_table_exists("user_interests")),
            ("notification_delivery_tracking", check_table_exists("notification_delivery_tracking")),
        ])
    ]
    
    for category, items in comm_checks:
        print(f"\n{category}:")
        for name, exists in items:
            status = "OK" if exists else "MISSING"
            print(f"  {name}: {status}")
            if not exists:
                all_issues.append(f"Communication System - {category}: {name}")
    
    # Phase 14: User Experience
    print("\nPHASE 14: USER EXPERIENCE")
    print("-" * 40)
    
    ux_checks = [
        ("UX Domain", [
            ("packages/backend/domain/application_pipeline.py", check_file_exists("packages/backend/domain/application_pipeline.py")),
            ("packages/backend/domain/application_export.py", check_file_exists("packages/backend/domain/application_export.py")),
            ("packages/backend/domain/follow_up_reminders.py", check_file_exists("packages/backend/domain/follow_up_reminders.py")),
            ("packages/backend/domain/answer_memory.py", check_file_exists("packages/backend/domain/answer_memory.py")),
            ("packages/backend/domain/multi_resume.py", check_file_exists("packages/backend/domain/multi_resume.py")),
            ("packages/backend/domain/application_notes.py", check_file_exists("packages/backend/domain/application_notes.py")),
        ]),
        ("UX APIs", [
            ("apps/api/user_experience_endpoints.py", check_file_exists("apps/api/user_experience_endpoints.py")),
        ]),
        ("UX Frontend", [
            ("apps/web/src/components/user-experience/PipelineView.tsx", check_file_exists("apps/web/src/components/user-experience/PipelineView.tsx")),
            ("apps/web/src/components/user-experience/ApplicationExport.tsx", check_file_exists("apps/web/src/components/user-experience/ApplicationExport.tsx")),
        ]),
        ("UX Tables", [
            ("resume_versions", check_table_exists("resume_versions")),
            ("follow_up_reminders", check_table_exists("follow_up_reminders")),
            ("interview_questions", check_table_exists("interview_questions")),
            ("answer_attempts", check_table_exists("answer_attempts")),
            ("answer_memory", check_table_exists("answer_memory")),
            ("application_notes", check_table_exists("application_notes")),
        ])
    ]
    
    for category, items in ux_checks:
        print(f"\n{category}:")
        for name, exists in items:
            status = "OK" if exists else "MISSING"
            print(f"  {name}: {status}")
            if not exists:
                all_issues.append(f"User Experience - {category}: {name}")
    
    # Phase 15: Database & Performance
    print("\nPHASE 15: DATABASE & PERFORMANCE")
    print("-" * 40)
    
    perf_checks = [
        ("Performance Migrations", [
            ("migrations/008_performance_indexes.sql", check_file_exists("migrations/008_performance_indexes.sql")),
            ("migrations/009_missing_indexes.sql", check_file_exists("migrations/009_missing_indexes.sql")),
        ]),
        ("Monitoring", [
            ("apps/api/monitoring_endpoints.py", check_file_exists("apps/api/monitoring_endpoints.py")),
            ("apps/web/src/components/PerformanceMonitor.tsx", check_file_exists("apps/web/src/components/PerformanceMonitor.tsx")),
        ]),
        ("Caching", [
            ("shared/redis_client.py", check_file_exists("shared/redis_client.py")),
            ("shared/metrics.py", check_file_exists("shared/metrics.py")),
        ])
    ]
    
    for category, items in perf_checks:
        print(f"\n{category}:")
        for name, exists in items:
            status = "OK" if exists else "MISSING"
            print(f"  {name}: {status}")
            if not exists:
                all_issues.append(f"Database & Performance - {category}: {name}")
    
    # Phase 16: Configuration & Security
    print("\nPHASE 16: CONFIGURATION & SECURITY")
    print("-" * 40)
    
    config_checks = [
        ("Configuration", [
            ("shared/config.py", check_file_exists("shared/config.py")),
        ]),
        ("Security", [
            ("apps/api/admin_security.py", check_file_exists("apps/api/admin_security.py")),
            ("apps/api/ccpa.py", check_file_exists("apps/api/ccpa.py")),
            ("apps/api/gdpr.py", check_file_exists("apps/api/gdpr.py")),
            ("apps/api/mfa.py", check_file_exists("apps/api/mfa.py")),
        ]),
        ("Middleware", [
            ("shared/middleware.py", check_file_exists("shared/middleware.py")),
        ])
    ]
    
    for category, items in config_checks:
        print(f"\n{category}:")
        for name, exists in items:
            status = "OK" if exists else "MISSING"
            print(f"  {name}: {status}")
            if not exists:
                all_issues.append(f"Configuration & Security - {category}: {name}")
    
    # Integration Checks
    print("\nINTEGRATION CHECKS")
    print("-" * 40)
    
    integration_checks = [
        ("Main.py Integration", [
            ("apps/api/main.py", check_file_exists("apps/api/main.py")),
        ]),
        ("Database Connection", [
            ("apps/api/dependencies.py", check_file_exists("apps/api/dependencies.py")),
        ]),
        ("Worker Integration", [
            ("apps/worker/agent.py", check_file_exists("apps/worker/agent.py")),
        ])
    ]
    
    for category, items in integration_checks:
        print(f"\n{category}:")
        for name, exists in items:
            status = "OK" if exists else "MISSING"
            print(f"  {name}: {status}")
            if not exists:
                all_issues.append(f"Integration - {category}: {name}")
    
    # Production Readiness
    print("\nPRODUCTION READINESS")
    print("-" * 40)
    
    prod_checks = [
        ("Deployment", [
            ("Dockerfile", check_file_exists("Dockerfile")),
            ("docker-compose.yml", check_file_exists("docker-compose.yml")),
            ("render.yaml", check_file_exists("render.yaml")),
            (".env.example", check_file_exists(".env.example")),
        ]),
        ("CI/CD", [
            (".github/workflows/ci.yml", check_file_exists(".github/workflows/ci.yml")),
            (".github/workflows/deploy-render-seo.yml", check_file_exists(".github/workflows/deploy-render-seo.yml")),
        ]),
        ("Documentation", [
            ("README.md", check_file_exists("README.md")),
            ("CONTRIBUTING.md", check_file_exists("CONTRIBUTING.md")),
            ("SECURITY.md", check_file_exists("SECURITY.md")),
        ])
    ]
    
    for category, items in prod_checks:
        print(f"\n{category}:")
        for name, exists in items:
            status = "OK" if exists else "MISSING"
            print(f"  {name}: {status}")
            if not exists:
                all_issues.append(f"Production Readiness - {category}: {name}")
    
    # Summary
    print("\n" + "=" * 80)
    print("AUDIT SUMMARY")
    print("=" * 80)
    print(f"Total Issues Found: {len(all_issues)}")
    
    if all_issues:
        print("\nMISSING COMPONENTS:")
        for i, issue in enumerate(all_issues, 1):
            print(f"{i:3d}. {issue}")
        
        print(f"\nSTATUS: FAIL - {len(all_issues)} components missing")
        return False
    else:
        print("\nSTATUS: PASS - All components present")
        return True

if __name__ == "__main__":
    success = audit_all_phases()
    sys.exit(0 if success else 1)
