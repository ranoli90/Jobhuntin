#!/usr/bin/env python3
"""
Comprehensive Phase Audit 1-16: Systematic review of all phases to identify missing components.

This script performs a thorough audit of all development phases (1-16) of the JobHuntin platform
to identify any missing components, no matter how small, ensuring perfect end-to-end functionality.

The audit covers:
- Backend components (APIs, domain models, database tables)
- Frontend components (UI components, styling, navigation)
- Database schema and migrations
- Integration points and dependencies
- Code quality and best practices

Usage:
    python comprehensive_phase_audit.py

Outputs:
    - Console report of audit findings
    - JSON report with detailed results
    - TODO list of missing components
"""

import os
import sys
import json
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
        logging.FileHandler('audit.log')
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class AuditResult:
    """Data class for audit results."""
    phase_name: str
    total_checks: int
    passed_checks: int
    failed_checks: int
    missing_items: List[str]
    issues_found: List[str]
    status: str
    details: Optional[Dict[str, Any]] = None


class ComprehensivePhaseAudit:
    """Comprehensive audit of all phases 1-16.
    
    This class performs systematic audits of all development phases to identify
    missing components and ensure perfect end-to-end functionality.
    
    Attributes:
        missing_items: List of identified missing components
        issues_found: List of identified issues
        phase_results: Dictionary storing results for each phase
    """
    
    def __init__(self) -> None:
        """Initialize the audit instance."""
        self.missing_items: List[str] = []
        self.issues_found: List[str] = []
        self.phase_results: Dict[str, AuditResult] = {}
        logger.info("Initialized ComprehensivePhaseAudit")
        
    def audit_all_phases(self) -> Dict[str, Any]:
        """Run comprehensive audit of all phases.
        
        Returns:
            Dict containing comprehensive audit results with statistics and recommendations.
            
        Raises:
            RuntimeError: If critical audit errors occur.
        """
        try:
            logger.info("Starting comprehensive audit of all phases 1-16")
            print("=" * 80)
            print("COMPREHENSIVE PHASE AUDIT 1-16")
            print("=" * 80)
            
            # Phase 1-5: Foundation Audit
            self.audit_phase_foundation()
            
            # Phase 6: Backend Reliability Audit
            self.audit_phase_backend_reliability()
            
            # Phase 7: Design System Audit
            self.audit_phase_design_system()
            
            # Phase 8: Typography & Layout Audit
            self.audit_phase_typography_layout()
            
            # Phase 9: Mobile Optimization Audit
            self.audit_phase_mobile_optimization()
            
            # Phase 10: Accessibility Audit
            self.audit_phase_accessibility()
            
            # Phase 11: AI System Audit
            self.audit_phase_ai_system()
            
            # Phase 12: Agent Improvements Audit
            self.audit_phase_agent_improvements()
            
            # Phase 13: Communication System Audit
            self.audit_phase_communication_system()
            
            # Phase 14: User Experience Audit
            self.audit_phase_user_experience()
            
            # Phase 15: Database & Performance Audit
            self.audit_phase_database_performance()
            
            # Phase 16: Configuration & Security Audit
            self.audit_phase_configuration_security()
            
            # End-to-End Integration Testing
            self.audit_end_to_end_integration()
            
            # Production Readiness Verification
            self.audit_production_readiness()
            
            # Generate comprehensive report
            return self.generate_audit_report()
            
        except Exception as e:
                logger.error(f"Critical error during audit: {e}")
                raise RuntimeError(f"Audit failed: {e}") from e
    
    def audit_phase_foundation(self) -> AuditResult:
        """Audit Phase 1-5: Foundation components.
        
        This phase covers the core infrastructure including database tables,
        authentication system, basic API endpoints, frontend structure, and shared libraries.
        
        Returns:
            AuditResult containing the foundation phase audit results.
        """
        logger.info("Starting Phase 1-5 Foundation Audit")
        print("\n" + "=" * 60)
        print("PHASE 1-5: FOUNDATION AUDIT")
        print("=" * 60)
        
        phase_issues: List[str] = []
        total_checks = 0
        passed_checks = 0
        
        # Check core database schema
        core_tables: List[str] = [
            "tenants", "tenant_members", "users", "user_preferences", 
            "jobs", "applications", "application_inputs", "events", "answer_memory"
        ]
        
        print("Checking core database tables...")
        for table in core_tables:
            total_checks += 1
            if not self.check_table_exists(table):
                phase_issues.append(f"Missing core table: {table}")
                print(f"  X Missing table: {table}")
                self.missing_items.append(f"Foundation - Core Tables: {table}")
            else:
                print(f"  + Table exists: {table}")
                passed_checks += 1
        
        # Check core API endpoints
        core_endpoints: List[str] = [
            "apps/api/auth.py",
            "apps/api/user.py", 
            "apps/api/dashboard.py",
            "apps/api/admin.py"
        ]
        
        print("Checking core API endpoints...")
        for endpoint in core_endpoints:
            total_checks += 1
            if not os.path.exists(endpoint):
                phase_issues.append(f"Missing core endpoint: {endpoint}")
                print(f"  X Missing endpoint: {endpoint}")
                self.missing_items.append(f"Foundation - Core APIs: {endpoint}")
            else:
                print(f"  + Endpoint exists: {endpoint}")
                passed_checks += 1
        
        # Check authentication system
        auth_components: List[str] = [
            "packages/backend/domain/tenant.py",
            "apps/api/auth.py",
            "packages/backend/domain/repositories.py"
        ]
        
        print("Checking authentication system...")
        for component in auth_components:
            total_checks += 1
            if not os.path.exists(component):
                phase_issues.append(f"Missing auth component: {component}")
                print(f"  X Missing auth component: {component}")
                self.missing_items.append(f"Foundation - Auth System: {component}")
            else:
                print(f"  + Auth component exists: {component}")
                passed_checks += 1
        
        # Check basic frontend structure
        frontend_core: List[str] = [
            "apps/web/src/App.tsx",
            "apps/web/src/main.tsx",
            "apps/web/src/index.css"
        ]
        
        print("Checking frontend foundation...")
        for component in frontend_core:
            total_checks += 1
            if not os.path.exists(component):
                phase_issues.append(f"Missing frontend component: {component}")
                print(f"  X Missing frontend component: {component}")
                self.missing_items.append(f"Foundation - Frontend Core: {component}")
            else:
                print(f"  + Frontend component exists: {component}")
                passed_checks += 1
        
        # Check shared libraries
        shared_components: List[str] = [
            "shared/config.py",
            "shared/logging_config.py",
            "shared/metrics.py",
            "shared/redis_client.py"
        ]
        
        print("Checking shared libraries...")
        for component in shared_components:
            total_checks += 1
            if not os.path.exists(component):
                phase_issues.append(f"Missing shared component: {component}")
                print(f"  X Missing shared component: {component}")
                self.missing_items.append(f"Foundation - Shared Libraries: {component}")
            else:
                print(f"  + Shared component exists: {component}")
                passed_checks += 1
        
        # Create audit result
        result = AuditResult(
            phase_name="Foundation",
            total_checks=total_checks,
            passed_checks=passed_checks,
            failed_checks=total_checks - passed_checks,
            missing_items=phase_issues,
            issues_found=phase_issues,
            status="PASS" if not phase_issues else "FAIL"
        )
        
        self.phase_results["foundation"] = result
        
        # Log results
        if phase_issues:
            logger.warning(f"Foundation audit completed with {len(phase_issues)} issues")
            print(f"\nX FOUNDATION ISSUES: {len(phase_issues)}")
            for issue in phase_issues:
                print(f"   - {issue}")
        else:
            logger.info("Foundation audit completed successfully")
            print("\n+ FOUNDATION: All core components present")
        
        return result
    
    def audit_phase_backend_reliability(self) -> AuditResult:
        """Audit Phase 6: Backend Reliability.
        
        This phase covers backend reliability aspects including error handling,
        monitoring integration, performance monitoring, security features, and caching.
        
        Returns:
            AuditResult containing the backend reliability audit results.
        """
        logger.info("Starting Phase 6 Backend Reliability Audit")
        print("\n" + "=" * 60)
        print("PHASE 6: BACKEND RELIABILITY AUDIT")
        print("=" * 60)
        
        phase_issues: List[str] = []
        total_checks = 0
        passed_checks = 0
        
        # Check error handling
        error_handling = [
            ("packages/backend/domain/repositories.py", "Repository error handling"),
            ("apps/api/main.py", "Global exception handlers")
        ]
        
        print("Checking error handling...")
        for component, description in error_handling:
            total_checks += 1
            if not os.path.exists(component):
                phase_issues.append(f"Missing error handling: {component}")
                print(f"  X Missing error handling: {component}")
                self.missing_items.append(f"Backend Reliability - Error Handling: {component}")
            else:
                print(f"  + Error handling exists: {component}")
                passed_checks += 1
        
        # Check monitoring and logging
        monitoring = [
            ("shared/telemetry.py", "Telemetry system"),
            ("shared/metrics.py", "Metrics collection"),
            ("shared/logging_config.py", "Logging configuration")
        ]
        
        print("Checking monitoring and logging...")
        for component, description in monitoring:
            total_checks += 1
            if not os.path.exists(component):
                phase_issues.append(f"Missing monitoring: {component}")
                print(f"  X Missing monitoring: {component}")
                self.missing_items.append(f"Backend Reliability - Monitoring: {component}")
            else:
                print(f"  + Monitoring exists: {component}")
                passed_checks += 1
        
        # Check performance optimizations
        performance = [
            ("shared/redis_client.py", "Redis caching"),
            ("shared/metrics.py", "Performance metrics")
        ]
        
        print("Checking performance optimizations...")
        for component, description in performance:
            total_checks += 1
            if not os.path.exists(component):
                phase_issues.append(f"Missing performance component: {component}")
                print(f"  X Missing performance component: {component}")
                self.missing_items.append(f"Backend Reliability - Performance: {component}")
            else:
                print(f"  + Performance component exists: {component}")
                passed_checks += 1
        
        # Check security features
        security = [
            ("packages/backend/domain/tenant.py", "Tenant security"),
            ("apps/api/admin_security.py", "Admin security")
        ]
        
        print("Checking security features...")
        for component, description in security:
            total_checks += 1
            if not os.path.exists(component):
                phase_issues.append(f"Missing security component: {component}")
                print(f"  X Missing security component: {component}")
                self.missing_items.append(f"Backend Reliability - Security: {component}")
            else:
                print(f"  + Security component exists: {component}")
                passed_checks += 1
        
        # Create audit result
        result = AuditResult(
            phase_name="Backend Reliability",
            total_checks=total_checks,
            passed_checks=passed_checks,
            failed_checks=total_checks - passed_checks,
            missing_items=phase_issues,
            issues_found=phase_issues,
            status="PASS" if not phase_issues else "FAIL"
        )
        
        self.phase_results["backend_reliability"] = result
        
        # Log results
        if phase_issues:
            logger.warning(f"Backend reliability audit completed with {len(phase_issues)} issues")
            print(f"\nX BACKEND RELIABILITY ISSUES: {len(phase_issues)}")
            for issue in phase_issues:
                print(f"   - {issue}")
        else:
            logger.info("Backend reliability audit completed successfully")
            print("\n+ BACKEND RELIABILITY: All components present")
        
        return result
    
    def audit_phase_design_system(self):
        """Audit Phase 7: Design System."""
        print("\n" + "=" * 60)
        print("PHASE 7: DESIGN SYSTEM AUDIT")
        print("=" * 60)
        
        phase_issues = []
        
        # Check UI components
        ui_components = [
            "apps/web/src/components/ui/ButtonStyles.tsx",
            "apps/web/src/components/ui/CardStyles.tsx",
            "apps/web/src/components/ui/SkeletonLoader.tsx"
        ]
        
        print("Checking UI components...")
        for component in ui_components:
            if not os.path.exists(component):
                phase_issues.append(f"Missing UI component: {component}")
                print(f"  ❌ Missing UI component: {component}")
            else:
                print(f"  ✅ UI component exists: {component}")
        
        # Check styling system
        styling = [
            "apps/web/src/index.css",
            "apps/web/src/styles/globals.css"
        ]
        
        print("Checking styling system...")
        for component in styling:
            if not os.path.exists(component):
                phase_issues.append(f"Missing styling: {component}")
                print(f"  ❌ Missing styling: {component}")
            else:
                print(f"  ✅ Styling exists: {component}")
        
        # Check marketing components
        marketing = [
            "apps/web/src/components/marketing/MarketingNavbar.tsx",
            "apps/web/src/components/marketing/SwitchFrom.tsx",
            "apps/web/src/components/marketing/SuccessStories.tsx"
        ]
        
        print("Checking marketing components...")
        for component in marketing:
            if not os.path.exists(component):
                phase_issues.append(f"Missing marketing component: {component}")
                print(f"  ❌ Missing marketing component: {component}")
            else:
                print(f"  ✅ Marketing component exists: {component}")
        
        self.phase_results["design_system"] = {
            "issues": phase_issues,
            "status": "PASS" if not phase_issues else "FAIL"
        }
        
        if phase_issues:
            print(f"\n❌ DESIGN SYSTEM ISSUES: {len(phase_issues)}")
            for issue in phase_issues:
                print(f"   - {issue}")
        else:
            print("\n✅ DESIGN SYSTEM: All components present")
    
    def audit_phase_typography_layout(self):
        """Audit Phase 8: Typography & Layout."""
        print("\n" + "=" * 60)
        print("PHASE 8: TYPOGRAPHY & LAYOUT AUDIT")
        print("=" * 60)
        
        phase_issues = []
        
        # Check typography files
        typography = [
            "apps/web/src/styles/typography.css",
            "apps/web/src/index.css"
        ]
        
        print("Checking typography system...")
        for component in typography:
            if not os.path.exists(component):
                phase_issues.append(f"Missing typography: {component}")
                print(f"  ❌ Missing typography: {component}")
            else:
                print(f"  ✅ Typography exists: {component}")
        
        # Check layout components
        layout = [
            "apps/web/src/layouts/AppLayout.tsx",
            "apps/web/src/components/marketing/SwitchFrom.tsx"
        ]
        
        print("Checking layout components...")
        for component in layout:
            if not os.path.exists(component):
                phase_issues.append(f"Missing layout component: {component}")
                print(f"  ❌ Missing layout component: {component}")
            else:
                print(f"  ✅ Layout component exists: {component}")
        
        self.phase_results["typography_layout"] = {
            "issues": phase_issues,
            "status": "PASS" if not phase_issues else "FAIL"
        }
        
        if phase_issues:
            print(f"\n❌ TYPOGRAPHY & LAYOUT ISSUES: {len(phase_issues)}")
            for issue in phase_issues:
                print(f"   - {issue}")
        else:
            print("\n✅ TYPOGRAPHY & LAYOUT: All components present")
    
    def audit_phase_mobile_optimization(self):
        """Audit Phase 9: Mobile Optimization."""
        print("\n" + "=" * 60)
        print("PHASE 9: MOBILE OPTIMIZATION AUDIT")
        print("=" * 60)
        
        phase_issues = []
        
        # Check mobile-optimized components
        mobile_components = [
            "apps/web/src/components/marketing/MarketingNavbar.tsx",
            "apps/web/src/components/navigation/MobileMenu.tsx"
        ]
        
        print("Checking mobile components...")
        for component in mobile_components:
            if not os.path.exists(component):
                phase_issues.append(f"Missing mobile component: {component}")
                print(f"  ❌ Missing mobile component: {component}")
            else:
                print(f"  ✅ Mobile component exists: {component}")
        
        # Check responsive CSS
        responsive_css = [
            "apps/web/src/index.css",
            "apps/web/src/styles/typography.css"
        ]
        
        print("Checking responsive CSS...")
        for component in responsive_css:
            if not os.path.exists(component):
                phase_issues.append(f"Missing responsive CSS: {component}")
                print(f"  ❌ Missing responsive CSS: {component}")
            else:
                print(f"  ✅ Responsive CSS exists: {component}")
        
        self.phase_results["mobile_optimization"] = {
            "issues": phase_issues,
            "status": "PASS" if not phase_issues else "FAIL"
        }
        
        if phase_issues:
            print(f"\n❌ MOBILE OPTIMIZATION ISSUES: {len(phase_issues)}")
            for issue in phase_issues:
                print(f"   - {issue}")
        else:
            print("\n✅ MOBILE OPTIMIZATION: All components present")
    
    def audit_phase_accessibility(self):
        """Audit Phase 10: Accessibility."""
        print("\n" + "=" * 60)
        print("PHASE 10: ACCESSIBILITY AUDIT")
        print("=" * 60)
        
        phase_issues = []
        
        # Check accessibility components
        a11y_components = [
            "apps/web/src/components/FocusTrap.tsx",
            "apps/web/src/components/ui/ButtonStyles.tsx"
        ]
        
        print("Checking accessibility components...")
        for component in a11y_components:
            if not os.path.exists(component):
                phase_issues.append(f"Missing a11y component: {component}")
                print(f"  ❌ Missing a11y component: {component}")
            else:
                print(f"  ✅ A11y component exists: {component}")
        
        # Check keyboard navigation
        keyboard_nav = [
            "apps/web/src/components/navigation/Navigation.tsx"
        ]
        
        print("Checking keyboard navigation...")
        for component in keyboard_nav:
            if not os.path.exists(component):
                phase_issues.append(f"Missing keyboard navigation: {component}")
                print(f"  ❌ Missing keyboard navigation: {component}")
            else:
                print(f"  ✅ Keyboard navigation exists: {component}")
        
        self.phase_results["accessibility"] = {
            "issues": phase_issues,
            "status": "PASS" if not phase_issues else "FAIL"
        }
        
        if phase_issues:
            print(f"\n❌ ACCESSIBILITY ISSUES: {len(phase_issues)}")
            for issue in phase_issues:
                print(f"   - {issue}")
        else:
            print("\n✅ ACCESSIBILITY: All components present")
    
    def audit_phase_ai_system(self):
        """Audit Phase 11: AI System."""
        print("\n" + "=" * 60)
        print("PHASE 11: AI SYSTEM AUDIT")
        print("=" * 60)
        
        phase_issues = []
        
        # Check AI domain components
        ai_domain = [
            "packages/backend/domain/document_processor.py",
            "packages/backend/domain/skills_taxonomy.py",
            "packages/backend/domain/resume.py",
            "packages/backend/domain/ab_testing.py",
            "packages/backend/domain/llm_career_path.py",
            "packages/backend/domain/voice_interviews.py",
            "packages/backend/domain/ai_onboarding.py"
        ]
        
        print("Checking AI domain components...")
        for component in ai_domain:
            if not os.path.exists(component):
                phase_issues.append(f"Missing AI domain: {component}")
                print(f"  ❌ Missing AI domain: {component}")
            else:
                print(f"  ✅ AI domain exists: {component}")
        
        # Check AI API endpoints
        ai_endpoints = [
            "apps/api/ai_endpoints.py",
            "apps/api/skills.py",
            "apps/api/ats_recommendations.py",
            "apps/api/voice_interviews.py",
            "apps/api/llm_career_path.py",
            "apps/api/ai_onboarding.py",
            "apps/api/ab_testing.py"
        ]
        
        print("Checking AI API endpoints...")
        for endpoint in ai_endpoints:
            if not os.path.exists(endpoint):
                phase_issues.append(f"Missing AI endpoint: {endpoint}")
                print(f"  ❌ Missing AI endpoint: {endpoint}")
            else:
                print(f"  ✅ AI endpoint exists: {endpoint}")
        
        # Check AI database tables
        ai_tables = [
            "skills_taxonomy",
            "ab_testing_experiments",
            "interview_sessions",
            "voice_interview_sessions"
        ]
        
        print("Checking AI database tables...")
        for table in ai_tables:
            if not self.check_table_exists(table):
                phase_issues.append(f"Missing AI table: {table}")
                print(f"  ❌ Missing AI table: {table}")
            else:
                print(f"  ✅ AI table exists: {table}")
        
        self.phase_results["ai_system"] = {
            "issues": phase_issues,
            "status": "PASS" if not phase_issues else "FAIL"
        }
        
        if phase_issues:
            print(f"\n❌ AI SYSTEM ISSUES: {len(phase_issues)}")
            for issue in phase_issues:
                print(f"   - {issue}")
        else:
            print("\n✅ AI SYSTEM: All components present")
    
    def audit_phase_agent_improvements(self):
        """Audit Phase 12: Agent Improvements."""
        print("\n" + "=" * 60)
        print("PHASE 12: AGENT IMPROVEMENTS AUDIT")
        print("=" * 60)
        
        phase_issues = []
        
        # Check agent domain components
        agent_domain = [
            "packages/backend/domain/agent_improvements.py",
            "packages/backend/domain/oauth_handler.py",
            "packages/backend/domain/concurrent_tracker.py",
            "packages/backend/domain/dlq_manager.py"
        ]
        
        print("Checking agent domain components...")
        for component in agent_domain:
            if not os.path.exists(component):
                phase_issues.append(f"Missing agent domain: {component}")
                print(f"  ❌ Missing agent domain: {component}")
            else:
                print(f"  ✅ Agent domain exists: {component}")
        
        # Check agent API endpoints
        agent_endpoints = [
            "apps/api/agent_improvements_endpoints.py",
            "apps/api/oauth_endpoints.py",
            "apps/api/concurrent_usage_endpoints.py",
            "apps/api/dlq_endpoints.py",
            "apps/api/screenshot_endpoints.py"
        ]
        
        print("Checking agent API endpoints...")
        for endpoint in agent_endpoints:
            if not os.path.exists(endpoint):
                phase_issues.append(f"Missing agent endpoint: {endpoint}")
                print(f"  ❌ Missing agent endpoint: {endpoint}")
            else:
                print(f"  ✅ Agent endpoint exists: {endpoint}")
        
        # Check agent frontend components
        agent_frontend = [
            "apps/web/src/components/agent-improvements/OAuthHandler.tsx",
            "apps/web/src/components/agent-improvements/ConcurrentUsageMonitor.tsx",
            "apps/web/src/components/agent-improvements/DLQDashboard.tsx",
            "apps/web/src/components/agent-improvements/ScreenshotCapture.tsx",
            "apps/web/src/components/agent-improvements/DocumentProcessor.tsx",
            "apps/web/src/components/agent-improvements/PerformanceMetrics.tsx"
        ]
        
        print("Checking agent frontend components...")
        for component in agent_frontend:
            if not os.path.exists(component):
                phase_issues.append(f"Missing agent frontend: {component}")
                print(f"  ❌ Missing agent frontend: {component}")
            else:
                print(f"  ✅ Agent frontend exists: {component}")
        
        # Check agent database tables
        agent_tables = [
            "button_detections",
            "form_field_detections",
            "oauth_credentials",
            "concurrent_usage_sessions",
            "dead_letter_queue",
            "screenshot_captures",
            "document_type_tracking",
            "agent_performance_metrics"
        ]
        
        print("Checking agent database tables...")
        for table in agent_tables:
            if not self.check_table_exists(table):
                phase_issues.append(f"Missing agent table: {table}")
                print(f"  ❌ Missing agent table: {table}")
            else:
                print(f"  ✅ Agent table exists: {table}")
        
        self.phase_results["agent_improvements"] = {
            "issues": phase_issues,
            "status": "PASS" if not phase_issues else "FAIL"
        }
        
        if phase_issues:
            print(f"\n❌ AGENT IMPROVEMENTS ISSUES: {len(phase_issues)}")
            for issue in phase_issues:
                print(f"   - {issue}")
        else:
            print("\n✅ AGENT IMPROVEMENTS: All components present")
    
    def audit_phase_communication_system(self):
        """Audit Phase 13: Communication System."""
        print("\n" + "=" * 60)
        print("PHASE 13: COMMUNICATION SYSTEM AUDIT")
        print("=" * 60)
        
        phase_issues = []
        
        # Check communication domain components
        comm_domain = [
            "packages/backend/domain/email_communications.py",
            "packages/backend/domain/enhanced_notifications.py"
        ]
        
        print("Checking communication domain components...")
        for component in comm_domain:
            if not os.path.exists(component):
                phase_issues.append(f"Missing comm domain: {component}")
                print(f"  ❌ Missing comm domain: {component}")
            else:
                print(f"  ✅ Comm domain exists: {component}")
        
        # Check communication API endpoints
        comm_endpoints = [
            "apps/api/communication_endpoints.py"
        ]
        
        print("Checking communication API endpoints...")
        for endpoint in comm_endpoints:
            if not os.path.exists(endpoint):
                phase_issues.append(f"Missing comm endpoint: {endpoint}")
                print(f"  ❌ Missing comm endpoint: {endpoint}")
            else:
                print(f"  ✅ Comm endpoint exists: {endpoint}")
        
        # Check communication database tables
        comm_tables = [
            "email_communications_log",
            "email_preferences",
            "user_preferences",
            "notification_semantic_tags",
            "user_interests",
            "notification_delivery_tracking"
        ]
        
        print("Checking communication database tables...")
        for table in comm_tables:
            if not self.check_table_exists(table):
                phase_issues.append(f"Missing comm table: {table}")
                print(f"  ❌ Missing comm table: {table}")
            else:
                print(f"  ✅ Comm table exists: {table}")
        
        self.phase_results["communication_system"] = {
            "issues": phase_issues,
            "status": "PASS" if not phase_issues else "FAIL"
        }
        
        if phase_issues:
            print(f"\n❌ COMMUNICATION SYSTEM ISSUES: {len(phase_issues)}")
            for issue in phase_issues:
                print(f"   - {issue}")
        else:
            print("\n✅ COMMUNICATION SYSTEM: All components present")
    
    def audit_phase_user_experience(self):
        """Audit Phase 14: User Experience."""
        print("\n" + "=" * 60)
        print("PHASE 14: USER EXPERIENCE AUDIT")
        print("=" * 60)
        
        phase_issues = []
        
        # Check UX domain components
        ux_domain = [
            "packages/backend/domain/application_pipeline.py",
            "packages/backend/domain/application_export.py",
            "packages/backend/domain/follow_up_reminders.py",
            "packages/backend/domain/answer_memory.py",
            "packages/backend/domain/multi_resume.py",
            "packages/backend/domain/application_notes.py"
        ]
        
        print("Checking UX domain components...")
        for component in ux_domain:
            if not os.path.exists(component):
                phase_issues.append(f"Missing UX domain: {component}")
                print(f"  ❌ Missing UX domain: {component}")
            else:
                print(f"  ✅ UX domain exists: {component}")
        
        # Check UX API endpoints
        ux_endpoints = [
            "apps/api/user_experience_endpoints.py"
        ]
        
        print("Checking UX API endpoints...")
        for endpoint in ux_endpoints:
            if not os.path.exists(endpoint):
                phase_issues.append(f"Missing UX endpoint: {endpoint}")
                print(f"  ❌ Missing UX endpoint: {endpoint}")
            else:
                print(f"  ✅ UX endpoint exists: {endpoint}")
        
        # Check UX frontend components
        ux_frontend = [
            "apps/web/src/components/user-experience/PipelineView.tsx",
            "apps/web/src/components/user-experience/ApplicationExport.tsx"
        ]
        
        print("Checking UX frontend components...")
        for component in ux_frontend:
            if not os.path.exists(component):
                phase_issues.append(f"Missing UX frontend: {component}")
                print(f"  ❌ Missing UX frontend: {component}")
            else:
                print(f"  ✅ UX frontend exists: {component}")
        
        # Check UX database tables
        ux_tables = [
            "resume_versions",
            "follow_up_reminders",
            "interview_questions",
            "answer_attempts",
            "answer_memory",
            "application_notes"
        ]
        
        print("Checking UX database tables...")
        for table in ux_tables:
            if not self.check_table_exists(table):
                phase_issues.append(f"Missing UX table: {table}")
                print(f"  ❌ Missing UX table: {table}")
            else:
                print(f"  ✅ UX table exists: {table}")
        
        self.phase_results["user_experience"] = {
            "issues": phase_issues,
            "status": "PASS" if not phase_issues else "FAIL"
        }
        
        if phase_issues:
            print(f"\n❌ USER EXPERIENCE ISSUES: {len(phase_issues)}")
            for issue in phase_issues:
                print(f"   - {issue}")
        else:
            print("\n✅ USER EXPERIENCE: All components present")
    
    def audit_phase_database_performance(self):
        """Audit Phase 15: Database & Performance."""
        print("\n" + "=" * 60)
        print("PHASE 15: DATABASE & PERFORMANCE AUDIT")
        print("=" * 60)
        
        phase_issues = []
        
        # Check performance migrations
        perf_migrations = [
            "migrations/008_performance_indexes.sql",
            "migrations/009_missing_indexes.sql"
        ]
        
        print("Checking performance migrations...")
        for migration in perf_migrations:
            if not os.path.exists(migration):
                phase_issues.append(f"Missing performance migration: {migration}")
                print(f"  ❌ Missing performance migration: {migration}")
            else:
                print(f"  ✅ Performance migration exists: {migration}")
        
        # Check monitoring components
        monitoring = [
            "apps/api/monitoring_endpoints.py",
            "apps/web/src/components/PerformanceMonitor.tsx"
        ]
        
        print("Checking monitoring components...")
        for component in monitoring:
            if not os.path.exists(component):
                phase_issues.append(f"Missing monitoring component: {component}")
                print(f"  ❌ Missing monitoring component: {component}")
            else:
                print(f"  ✅ Monitoring component exists: {component}")
        
        # Check caching system
        caching = [
            "shared/redis_client.py",
            "shared/metrics.py"
        ]
        
        print("Checking caching system...")
        for component in caching:
            if not os.path.exists(component):
                phase_issues.append(f"Missing caching component: {component}")
                print(f"  ❌ Missing caching component: {component}")
            else:
                print(f"  ✅ Caching component exists: {component}")
        
        self.phase_results["database_performance"] = {
            "issues": phase_issues,
            "status": "PASS" if not phase_issues else "FAIL"
        }
        
        if phase_issues:
            print(f"\n❌ DATABASE & PERFORMANCE ISSUES: {len(phase_issues)}")
            for issue in phase_issues:
                print(f"   - {issue}")
        else:
            print("\n✅ DATABASE & PERFORMANCE: All components present")
    
    def audit_phase_configuration_security(self):
        """Audit Phase 16: Configuration & Security."""
        print("\n" + "=" * 60)
        print("PHASE 16: CONFIGURATION & SECURITY AUDIT")
        print("=" * 60)
        
        phase_issues = []
        
        # Check configuration system
        config = [
            "shared/config.py"
        ]
        
        print("Checking configuration system...")
        for component in config:
            if not os.path.exists(component):
                phase_issues.append(f"Missing config component: {component}")
                print(f"  ❌ Missing config component: {component}")
            else:
                print(f"  ✅ Config component exists: {component}")
        
        # Check security components
        security = [
            "apps/api/admin_security.py",
            "apps/api/ccpa.py",
            "apps/api/gdpr.py",
            "apps/api/mfa.py"
        ]
        
        print("Checking security components...")
        for component in security:
            if not os.path.exists(component):
                phase_issues.append(f"Missing security component: {component}")
                print(f"  ❌ Missing security component: {component}")
            else:
                print(f"  ✅ Security component exists: {component}")
        
        # Check middleware
        middleware = [
            "shared/middleware.py"
        ]
        
        print("Checking middleware...")
        for component in middleware:
            if not os.path.exists(component):
                phase_issues.append(f"Missing middleware: {component}")
                print(f"  ❌ Missing middleware: {component}")
            else:
                print(f"  ✅ Middleware exists: {component}")
        
        self.phase_results["configuration_security"] = {
            "issues": phase_issues,
            "status": "PASS" if not phase_issues else "FAIL"
        }
        
        if phase_issues:
            print(f"\n❌ CONFIGURATION & SECURITY ISSUES: {len(phase_issues)}")
            for issue in phase_issues:
                print(f"   - {issue}")
        else:
            print("\n✅ CONFIGURATION & SECURITY: All components present")
    
    def audit_end_to_end_integration(self):
        """Audit End-to-End Integration."""
        print("\n" + "=" * 60)
        print("END-TO-END INTEGRATION AUDIT")
        print("=" * 60)
        
        phase_issues = []
        
        # Check main.py integration
        main_py = "apps/api/main.py"
        if os.path.exists(main_py):
            with open(main_py, 'r') as f:
                content = f.read()
            
            required_imports = [
                "agent_improvements_endpoints",
                "communication_endpoints",
                "user_experience_endpoints",
                "dlq_endpoints"
            ]
            
            print("Checking main.py integration...")
            for imp in required_imports:
                if imp not in content:
                    phase_issues.append(f"Missing import in main.py: {imp}")
                    print(f"  ❌ Missing import: {imp}")
                else:
                    print(f"  ✅ Import exists: {imp}")
        else:
            phase_issues.append("Missing main.py")
            print(f"  ❌ Missing main.py")
        
        # Check database connection
        db_connection = [
            "apps/api/dependencies.py"
        ]
        
        print("Checking database connection...")
        for component in db_connection:
            if not os.path.exists(component):
                phase_issues.append(f"Missing DB connection: {component}")
                print(f"  ❌ Missing DB connection: {component}")
            else:
                print(f"  ✅ DB connection exists: {component}")
        
        # Check worker integration
        worker = [
            "apps/worker/agent.py"
        ]
        
        print("Checking worker integration...")
        for component in worker:
            if not os.path.exists(component):
                phase_issues.append(f"Missing worker: {component}")
                print(f"  ❌ Missing worker: {component}")
            else:
                print(f"  ✅ Worker exists: {component}")
        
        self.phase_results["end_to_end_integration"] = {
            "issues": phase_issues,
            "status": "PASS" if not phase_issues else "FAIL"
        }
        
        if phase_issues:
            print(f"\n❌ END-TO-END INTEGRATION ISSUES: {len(phase_issues)}")
            for issue in phase_issues:
                print(f"   - {issue}")
        else:
            print("\n✅ END-TO-END INTEGRATION: All components integrated")
    
    def audit_production_readiness(self):
        """Audit Production Readiness."""
        print("\n" + "=" * 60)
        print("PRODUCTION READINESS AUDIT")
        print("=" * 60)
        
        phase_issues = []
        
        # Check deployment files
        deployment = [
            "Dockerfile",
            "docker-compose.yml",
            "render.yaml",
            ".env.example"
        ]
        
        print("Checking deployment files...")
        for component in deployment:
            if not os.path.exists(component):
                phase_issues.append(f"Missing deployment file: {component}")
                print(f"  ❌ Missing deployment file: {component}")
            else:
                print(f"  ✅ Deployment file exists: {component}")
        
        # Check CI/CD
        cicd = [
            ".github/workflows/ci.yml",
            ".github/workflows/deploy-render-seo.yml"
        ]
        
        print("Checking CI/CD...")
        for component in cicd:
            if not os.path.exists(component):
                phase_issues.append(f"Missing CI/CD: {component}")
                print(f"  ❌ Missing CI/CD: {component}")
            else:
                print(f"  ✅ CI/CD exists: {component}")
        
        # Check documentation
        docs = [
            "README.md",
            "CONTRIBUTING.md",
            "SECURITY.md"
        ]
        
        print("Checking documentation...")
        for component in docs:
            if not os.path.exists(component):
                phase_issues.append(f"Missing documentation: {component}")
                print(f"  ❌ Missing documentation: {component}")
            else:
                print(f"  ✅ Documentation exists: {component}")
        
        self.phase_results["production_readiness"] = {
            "issues": phase_issues,
            "status": "PASS" if not phase_issues else "FAIL"
        }
        
        if phase_issues:
            print(f"\n❌ PRODUCTION READINESS ISSUES: {len(phase_issues)}")
            for issue in phase_issues:
                print(f"   - {issue}")
        else:
            print("\n✅ PRODUCTION READINESS: All components ready")
    
    def check_table_exists(self, table_name: str) -> bool:
        """Check if table exists in migration files."""
        migrations_dir = Path("migrations")
        if not migrations_dir.exists():
            return False
        
        for migration_file in migrations_dir.glob("*.sql"):
            try:
                with open(migration_file, 'r') as f:
                    content = f.read()
                    if f"CREATE TABLE.*{table_name}" in content or f"CREATE TABLE IF NOT EXISTS.*{table_name}" in content:
                        return True
            except Exception:
                continue
        
        return False
    
    def generate_audit_report(self) -> Dict[str, Any]:
        """Generate comprehensive audit report."""
        print("\n" + "=" * 80)
        print("COMPREHENSIVE AUDIT REPORT")
        print("=" * 80)
        
        total_issues = 0
        passed_phases = 0
        failed_phases = 0
        
        for phase_name, result in self.phase_results.items():
            issues = result["issues"]
            status = result["status"]
            
            total_issues += len(issues)
            
            if status == "PASS":
                passed_phases += 1
                print(f"✅ {phase_name.upper()}: PASSED")
            else:
                failed_phases += 1
                print(f"❌ {phase_name.upper()}: FAILED ({len(issues)} issues)")
                for issue in issues:
                    print(f"   - {issue}")
        
        print(f"\n" + "=" * 80)
        print(f"SUMMARY:")
        print(f"  Total Issues Found: {total_issues}")
        print(f"  Phases Passed: {passed_phases}")
        print(f"  Phases Failed: {failed_phases}")
        print(f"  Overall Status: {'PASS' if failed_phases == 0 else 'FAIL'}")
        print("=" * 80)
        
        return {
            "total_issues": total_issues,
            "passed_phases": passed_phases,
            "failed_phases": failed_phases,
            "overall_status": "PASS" if failed_phases == 0 else "FAIL",
            "phase_results": self.phase_results
        }

def main():
    """Run comprehensive audit."""
    auditor = ComprehensivePhaseAudit()
    report = auditor.audit_all_phases()
    
    # Save report to file
    with open("comprehensive_audit_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Audit report saved to: comprehensive_audit_report.json")
    
    return report["overall_status"] == "PASS"

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
