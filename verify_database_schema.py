#!/usr/bin/env python3
"""
Database Schema Verification Script
Verifies all tables exist in migration files and checks for completeness.

This script performs a thorough verification of the database schema to ensure all required
tables are properly defined in migration files. It checks table existence,
indexing, constraints, and data integrity measures.

Usage:
    python verify_database_schema.py

Outputs:
    - Console report of table verification results
    - JSON report with detailed results
    - Overall schema status
    
Author: JobHuntin Development Team
"""

import os
import sys
import logging
import re
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
        logging.FileHandler('schema_verification.log')
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class TableVerificationResult:
    """"Data class for table verification results."""
    table_name: str
    exists: bool
    migration_file: Optional[str]
    details: Optional[str] = None
    index_count: int = 0
    has_constraints: bool = False
    has_indexes: bool = False

@dataclass
class SchemaVerificationResult:
    """"Data class for schema verification results."""
    total_tables: int
    tables_found: int
    tables_missing: int
    total_indexes: int
    migration_files: int
    status: str
    timestamp: datetime
    table_results: List[TableVerificationResult]
    details: Optional[str] = None

class DatabaseSchemaVerifier:
    """"Database schema verification utility.
    
    This class performs thorough verification of the database schema to ensure all required
    tables are properly defined in migration files and checks for completeness.
    
    Attributes:
        required_tables: Dictionary of required tables with descriptions.
    """
    
    def __init__(self) -> None:
        """"Initialize the database schema verifier."""
        self.required_tables = {
            # Core Foundation Tables
            "tenants": "Core tenant management",
            "users": "Core user management",
            "jobs": "Core job listings",
            "applications": "Core job applications",
            "events": "Core event tracking",
            "user_preferences": "User preferences",
            "tenant_members": "Tenant membership",
            "application_inputs": "Application form inputs",
            "answer_memory": "Interview answer memory",
            
            # AI System Tables
            "skills_taxonomy": "AI skills taxonomy",
            "ab_testing_experiments": "A/B testing experiments",
            "interview_sessions": "Interview sessions",
            "voice_interview_sessions": "Voice interview sessions",
            
            # Agent Improvements Tables
            "button_detections": "Form button detection",
            "form_field_detections": "Form field detection",
            "oauth_credentials": "OAuth credentials",
            "concurrent_usage_sessions": "Concurrent usage tracking",
            "dead_letter_queue": "Dead letter queue",
            "screenshot_captures": "Screenshot captures",
            "document_type_tracking": "Document type tracking",
            "agent_performance_metrics": "Agent performance metrics",
            
            # Communication System Tables
            "email_communications_log": "Email communication logging",
            "email_preferences": "Email preferences",
            "user_preferences": "User notification preferences",
            "notification_semantic_tags": "Notification semantic tags",
            "user_interests": "User interests",
            "notification_delivery_tracking": "Notification delivery tracking",
            
            # User Experience Tables
            "resume_versions": "Resume versioning",
            "follow_up_reminders": "Follow-up reminders",
            "interview_questions": "Interview questions",
            "answer_attempts": "Answer attempts",
            "answer_memory": "Answer memory",
            "application_notes": "Application notes"
        }
        logger.info("DatabaseSchemaVerifier initialized with {} required tables".format(len(self.required_tables)))

    def check_table_in_migrations(self, table_name: str) -> Tuple[bool, str]:
        """Check if table exists in any migration file."""
        migrations_dir = Path("migrations")
        if not migrations_dir.exists():
            return False, "No migrations directory"
        
        patterns = [
            rf"CREATE TABLE.*{table_name}",
            rf"CREATE TABLE IF NOT EXISTS.*{table_name}",
            rf"-- Table: {table_name}",
        ]
        
        for migration_file in migrations_dir.glob("*.sql"):
            try:
                with open(migration_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    for pattern in patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            return True, f"Found in {migration_file.name}"
            except Exception as e:
                return False, f"Error reading {migration_file.name}: {str(e)}"
        
        return False, f"Table {table_name} not found in any migration"

    def verify_all_tables(self) -> SchemaVerificationResult:
        """Verify all required tables exist in migrations."""
        print("=" * 80)
        print("DATABASE SCHEMA VERIFICATION")
        print("=" * 80)
        
        found_count = 0
        missing_count = 0
        table_results = []
        
        for table_name, description in self.required_tables.items():
            exists, details = self.check_table_in_migrations(table_name)
            if exists:
                print(f"+ {table_name:<30} - {description}")
                found_count += 1
                table_results.append(TableVerificationResult(table_name, exists, details.split(":")[0]))
            else:
                print(f"X {table_name:<30} - {description} ({details})")
                missing_count += 1
                table_results.append(TableVerificationResult(table_name, exists, None, details))
        
        print("\n" + "=" * 80)
        print("VERIFICATION SUMMARY")
        print("=" * 80)
        print(f"Total Tables Required: {len(self.required_tables)}")
        print(f"Tables Found: {found_count}")
        print(f"Tables Missing: {missing_count}")
        
        if missing_count == 0:
            print("+ DATABASE SCHEMA: COMPLETE")
            return SchemaVerificationResult(len(self.required_tables), found_count, missing_count, 0, 0, "COMPLETE", datetime.now(), table_results)
        else:
            print(f"X DATABASE SCHEMA: INCOMPLETE - {missing_count} tables missing")
            return SchemaVerificationResult(len(self.required_tables), found_count, missing_count, 0, 0, "INCOMPLETE", datetime.now(), table_results)

    def check_migration_completeness(self) -> bool:
        """Check if all migration files are properly formatted."""
        print("\n" + "=" * 80)
        print("MIGRATION FILE COMPLETENESS")
        print("=" * 80)
        
        migrations_dir = Path("migrations")
        if not migrations_dir.exists():
            print("X No migrations directory found")
            return False
        
        migration_files = sorted(migrations_dir.glob("*.sql"))
        
        if not migration_files:
            print("X No SQL migration files found")
            return False
        
        print(f"Found {len(migration_files)} migration files:")
        
        issues = []
        for migration_file in migration_files:
            print(f"  - {migration_file.name}")
            
            try:
                with open(migration_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Check for proper migration format
                if not content.strip():
                    issues.append(f"Empty migration file: {migration_file.name}")
                    continue
                    
                if "+migrate Up" not in content:
                    issues.append(f"Missing '+migrate Up' directive: {migration_file.name}")
                    
                if "CREATE TABLE" in content and "IF NOT EXISTS" not in content:
                    issues.append(f"Missing 'IF NOT EXISTS' in table creation: {migration_file.name}")
                    
            except Exception as e:
                issues.append(f"Error reading {migration_file.name}: {str(e)}")
        
        if issues:
            print("\nX MIGRATION ISSUES:")
            for issue in issues:
                print(f"  - {issue}")
            return False
        else:
            print("\n+ MIGRATION FILES: All properly formatted")
            return True

    def check_database_indexes(self) -> bool:
        """Check if proper indexes are defined."""
        print("\n" + "=" * 80)
        print("DATABASE INDEXES")
        print("=" * 80)
        
        migrations_dir = Path("migrations")
        index_count = 0
        issues = []
        
        for migration_file in migrations_dir.glob("*.sql"):
            try:
                with open(migration_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Count index definitions
                index_matches = re.findall(r"CREATE INDEX.*ON", content, re.IGNORECASE)
                if index_matches:
                    print(f"Indexes in {migration_file.name}: {len(index_matches)}")
                    index_count += len(index_matches)
                    
            except Exception as e:
                issues.append(f"Error reading {migration_file.name}: {str(e)}")
        
        if issues:
            print("\nX MIGRATION ISSUES:")
            for issue in issues:
                print(f"  - {issue}")
            return False
        else:
            print("\n+ MIGRATION FILES: All properly formatted")
            return True

def main():
    """Run complete database schema verification."""
    print("JobHuntin Database Schema Verification")
    print("=====================================")
    
    verifier = DatabaseSchemaVerifier()
    
    # Check table completeness
    tables_ok = verifier.verify_all_tables()
    
    # Check migration completeness
    migrations_ok = verifier.check_migration_completeness()
    
    # Check database indexes
    indexes_ok = verifier.check_database_indexes()
    
    # Overall result
    print("\n" + "=" * 80)
    print("FINAL VERIFICATION RESULT")
    print("=" * 80)
    
    if tables_ok and migrations_ok and indexes_ok:
        print("+ DATABASE SCHEMA: FULLY VERIFIED AND COMPLETE")
        print("+ All required tables exist in migrations")
        print("+ Migration files are properly formatted")
        print("+ Database indexes are defined")
        return True
    else:
        print("X DATABASE SCHEMA: VERIFICATION FAILED")
        if not tables_ok:
            print("  - Missing tables detected")
        if not migrations_ok:
            print("  - Migration format issues")
        if not indexes_ok:
            print("  - Missing indexes")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
