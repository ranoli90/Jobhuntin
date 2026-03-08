"""Database security auditing and compliance system.

Provides:
- Security event monitoring
- Access pattern analysis
- Privilege escalation detection
- Data access auditing
- Compliance reporting

Usage:
    from shared.db_security_auditor import SecurityAuditor

    auditor = SecurityAuditor(db_pool)
    await auditor.audit_database_security()
"""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
from enum import Enum

import asyncpg

from shared.logging_config import get_logger
from shared.alerting import AlertSeverity, get_alert_manager

logger = get_logger("sorce.db_security")


class SecurityEventType(Enum):
    """Security event types."""

    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    DATA_EXPORT = "data_export"
    SCHEMA_CHANGE = "schema_change"
    ADMIN_ACTION = "admin_action"
    SUSPICIOUS_QUERY = "suspicious_query"
    MASS_DELETE = "mass_delete"
    BACKUP_ACCESS = "backup_access"
    CONFIG_CHANGE = "config_change"


class SecuritySeverity(Enum):
    """Security event severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityEvent:
    """Security event record."""

    event_type: SecurityEventType
    severity: SecuritySeverity
    user: str
    database: str
    action: str
    object: Optional[str] = None
    ip_address: Optional[str] = None
    query: Optional[str] = None
    rows_affected: Optional[int] = None
    timestamp: float = field(default_factory=time.time)
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SecurityAlert:
    """Security alert record."""

    alert_id: str
    event_type: SecurityEventType
    severity: SecuritySeverity
    title: str
    description: str
    user: str
    ip_address: Optional[str] = None
    events: List[SecurityEvent] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    resolved: bool = False
    resolved_at: Optional[float] = None
    resolved_by: Optional[str] = None


@dataclass
class AccessPattern:
    """User access pattern analysis."""

    user: str
    total_queries: int
    unique_tables: Set[str]
    query_types: Dict[str, int]
    avg_rows_per_query: float
    max_rows_per_query: int
    suspicious_patterns: List[str]
    time_distribution: Dict[str, int]  # hour -> count
    last_activity: float
    risk_score: float


@dataclass
class ComplianceReport:
    """Compliance report data."""

    report_id: str
    generated_at: float
    period_start: float
    period_end: float
    total_events: int
    critical_events: int
    high_events: int
    medium_events: int
    low_events: int
    users_with_access: Set[str]
    privileged_actions: int
    data_exports: int
    failed_logins: int
    compliance_score: float
    recommendations: List[str]


class SecurityAuditor:
    """Advanced database security auditing system."""

    def __init__(self, db_pool: asyncpg.Pool, alert_manager: Optional[Any] = None):
        self.db_pool = db_pool
        self.alert_manager = alert_manager or get_alert_manager()

        # Security configuration
        self.security_config = {
            "enable_query_auditing": True,
            "enable_login_auditing": True,
            "enable_access_monitoring": True,
            "suspicious_query_threshold": 1000,  # rows affected
            "mass_delete_threshold": 100,  # rows deleted
            "failed_login_threshold": 5,  # consecutive failures
            "privileged_users": {"postgres", "admin", "root"},
            "sensitive_tables": {
                "users",
                "profiles",
                "applications",
                "billing_customers",
            },
            "restricted_hours": {"start": 22, "end": 6},  # 10 PM to 6 AM
        }

        # Event storage
        self.security_events: deque[SecurityEvent] = deque(maxlen=10000)
        self.security_alerts: deque[SecurityAlert] = deque(maxlen=1000)
        self.access_patterns: Dict[str, AccessPattern] = {}

        # Monitoring state
        self.failed_login_attempts: Dict[str, int] = defaultdict(int)
        self.active_sessions: Dict[str, Dict[str, Any]] = {}

        # Background tasks
        self._auditing_task: Optional[asyncio.Task] = None
        self._analysis_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()

    async def audit_database_security(self) -> Dict[str, Any]:
        """Perform comprehensive database security audit."""
        audit_results = {
            "timestamp": time.time(),
            "total_events": len(self.security_events),
            "active_alerts": len([a for a in self.security_alerts if not a.resolved]),
            "access_patterns": len(self.access_patterns),
            "failed_logins": dict(self.failed_login_attempts),
            "active_sessions": len(self.active_sessions),
        }

        # Analyze recent events
        recent_events = [
            e
            for e in self.security_events
            if time.time() - e.timestamp < 24 * 60 * 60  # Last 24 hours
        ]

        audit_results.update(
            {
                "recent_events_24h": len(recent_events),
                "critical_events_24h": len(
                    [
                        e
                        for e in recent_events
                        if e.severity == SecuritySeverity.CRITICAL
                    ]
                ),
                "high_events_24h": len(
                    [e for e in recent_events if e.severity == SecuritySeverity.HIGH]
                ),
            }
        )

        # Check for security issues
        issues = await self._identify_security_issues()
        audit_results["security_issues"] = issues

        # Generate recommendations
        recommendations = self._generate_security_recommendations(issues)
        audit_results["recommendations"] = recommendations

        return audit_results

    async def log_security_event(
        self,
        event_type: SecurityEventType,
        user: str,
        action: str,
        severity: SecuritySeverity = SecuritySeverity.MEDIUM,
        database: Optional[str] = None,
        object: Optional[str] = None,
        ip_address: Optional[str] = None,
        query: Optional[str] = None,
        rows_affected: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log a security event."""
        event = SecurityEvent(
            event_type=event_type,
            severity=severity,
            user=user,
            database=database or "default",
            action=action,
            object=object,
            ip_address=ip_address,
            query=query,
            rows_affected=rows_affected,
            context=context or {},
        )

        # Store event
        self.security_events.append(event)

        # Update access patterns
        await self._update_access_pattern(event)

        # Check for immediate alerts
        await self._check_immediate_alerts(event)

        logger.info(f"Security event logged: {event_type.value} - {user} - {action}")

    async def _update_access_pattern(self, event: SecurityEvent) -> None:
        """Update user access pattern analysis."""
        if event.user not in self.access_patterns:
            self.access_patterns[event.user] = AccessPattern(
                user=event.user,
                total_queries=0,
                unique_tables=set(),
                query_types=defaultdict(int),
                avg_rows_per_query=0,
                max_rows_per_query=0,
                suspicious_patterns=[],
                time_distribution=defaultdict(int),
                last_activity=event.timestamp,
                risk_score=0.0,
            )

        pattern = self.access_patterns[event.user]
        pattern.total_queries += 1
        pattern.last_activity = event.timestamp

        # Extract table names from query
        if event.query:
            tables = self._extract_tables_from_query(event.query)
            pattern.unique_tables.update(tables)

        # Update query type
        query_type = self._classify_query(event.action)
        pattern.query_types[query_type] += 1

        # Update row statistics
        if event.rows_affected:
            pattern.avg_rows_per_query = (
                pattern.avg_rows_per_query * (pattern.total_queries - 1)
                + event.rows_affected
            ) / pattern.total_queries
            pattern.max_rows_per_query = max(
                pattern.max_rows_per_query, event.rows_affected
            )

        # Update time distribution
        hour = int(time.strftime("%H", time.localtime(event.timestamp)))
        pattern.time_distribution[str(hour)] += 1

        # Calculate risk score
        pattern.risk_score = self._calculate_risk_score(pattern)

    def _extract_tables_from_query(self, query: str) -> Set[str]:
        """Extract table names from SQL query."""
        import re

        tables = set()

        # Simple regex patterns for table extraction
        patterns = [
            r"FROM\s+(\w+)",
            r"JOIN\s+(\w+)",
            r"UPDATE\s+(\w+)",
            r"INSERT INTO\s+(\w+)",
            r"DELETE FROM\s+(\w+)",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            tables.update(matches)

        return tables

    def _classify_query(self, action: str) -> str:
        """Classify query type."""
        action_lower = action.lower()

        if any(keyword in action_lower for keyword in ["select", "show"]):
            return "read"
        elif any(keyword in action_lower for keyword in ["insert", "create"]):
            return "create"
        elif any(keyword in action_lower for keyword in ["update", "alter"]):
            return "update"
        elif any(keyword in action_lower for keyword in ["delete", "drop"]):
            return "delete"
        elif "grant" in action_lower or "revoke" in action_lower:
            return "privilege"
        else:
            return "other"

    def _calculate_risk_score(self, pattern: AccessPattern) -> float:
        """Calculate risk score for user access pattern."""
        score = 0.0

        # High volume queries
        if pattern.total_queries > 1000:
            score += 0.2

        # Access to many tables
        if len(pattern.unique_tables) > 50:
            score += 0.2

        # High row counts
        if (
            pattern.max_rows_per_query
            > self.security_config["suspicious_query_threshold"]
        ):
            score += 0.3

        # After hours activity
        restricted_hours = self.security_config["restricted_hours"]
        after_hours_count = sum(
            count
            for hour, count in pattern.time_distribution.items()
            if restricted_hours["start"] <= int(hour)
            or int(hour) < restricted_hours["end"]
        )
        if after_hours_count > pattern.total_queries * 0.3:  # More than 30% after hours
            score += 0.2

        # Delete operations
        delete_count = pattern.query_types.get("delete", 0)
        if delete_count > pattern.total_queries * 0.1:  # More than 10% deletes
            score += 0.1

        return min(score, 1.0)

    async def _check_immediate_alerts(self, event: SecurityEvent) -> None:
        """Check for immediate security alerts."""
        # Check for failed login threshold
        if event.event_type == SecurityEventType.LOGIN_FAILURE:
            self.failed_login_attempts[event.user] += 1

            if (
                self.failed_login_attempts[event.user]
                >= self.security_config["failed_login_threshold"]
            ):
                await self._create_security_alert(
                    event_type=SecurityEventType.LOGIN_FAILURE,
                    severity=SecuritySeverity.HIGH,
                    title=f"Multiple failed login attempts for {event.user}",
                    description=f"User {event.user} has {self.failed_login_attempts[event.user]} failed login attempts",
                    user=event.user,
                    ip_address=event.ip_address,
                    events=[event],
                )

        # Check for mass delete
        elif (
            event.event_type == SecurityEventType.MASS_DELETE
            and event.rows_affected
            and event.rows_affected > self.security_config["mass_delete_threshold"]
        ):
            await self._create_security_alert(
                event_type=SecurityEventType.MASS_DELETE,
                severity=SecuritySeverity.CRITICAL,
                title=f"Mass delete operation by {event.user}",
                description=f"User {event.user} deleted {event.rows_affected} rows from {event.object}",
                user=event.user,
                events=[event],
            )

        # Check for suspicious query
        elif (
            event.event_type == SecurityEventType.SUSPICIOUS_QUERY
            and event.rows_affected
            and event.rows_affected > self.security_config["suspicious_query_threshold"]
        ):
            await self._create_security_alert(
                event_type=SecurityEventType.SUSPICIOUS_QUERY,
                severity=SecuritySeverity.HIGH,
                title=f"Suspicious query by {event.user}",
                description=f"Query affected {event.rows_affected} rows: {event.query[:100]}...",
                user=event.user,
                events=[event],
            )

        # Check for privilege escalation
        elif event.event_type == SecurityEventType.PRIVILEGE_ESCALATION:
            await self._create_security_alert(
                event_type=SecurityEventType.PRIVILEGE_ESCALATION,
                severity=SecuritySeverity.CRITICAL,
                title=f"Privilege escalation attempt by {event.user}",
                description=f"User {event.user} attempted privilege escalation: {event.action}",
                user=event.user,
                events=[event],
            )

        # Check for unauthorized access
        elif event.event_type == SecurityEventType.UNAUTHORIZED_ACCESS:
            await self._create_security_alert(
                event_type=SecurityEventType.UNAUTHORIZED_ACCESS,
                severity=SecuritySeverity.HIGH,
                title=f"Unauthorized access attempt by {event.user}",
                description=f"User {event.user} attempted unauthorized access to {event.object}",
                user=event.user,
                events=[event],
            )

    async def _create_security_alert(
        self,
        event_type: SecurityEventType,
        severity: SecuritySeverity,
        title: str,
        description: str,
        user: str,
        ip_address: Optional[str] = None,
        events: Optional[List[SecurityEvent]] = None,
    ) -> None:
        """Create a security alert."""
        import uuid

        alert = SecurityAlert(
            alert_id=str(uuid.uuid4())[:8],
            event_type=event_type,
            severity=severity,
            title=title,
            description=description,
            user=user,
            ip_address=ip_address,
            events=events or [],
            recommendations=self._generate_alert_recommendations(event_type, severity),
        )

        self.security_alerts.append(alert)

        # Trigger external alert
        await self.alert_manager.trigger_alert(
            name=f"security_{event_type.value}",
            severity=self._map_severity_to_alert(severity),
            message=title,
            context={
                "description": description,
                "user": user,
                "ip_address": ip_address,
                "alert_id": alert.alert_id,
            },
        )

    def _map_severity_to_alert(self, severity: SecuritySeverity) -> AlertSeverity:
        """Map security severity to alert severity."""
        mapping = {
            SecuritySeverity.LOW: AlertSeverity.INFO,
            SecuritySeverity.MEDIUM: AlertSeverity.WARNING,
            SecuritySeverity.HIGH: AlertSeverity.ERROR,
            SecuritySeverity.CRITICAL: AlertSeverity.CRITICAL,
        }
        return mapping.get(severity, AlertSeverity.WARNING)

    def _generate_alert_recommendations(
        self, event_type: SecurityEventType, severity: SecuritySeverity
    ) -> List[str]:
        """Generate recommendations for security alert."""
        recommendations = []

        if event_type == SecurityEventType.LOGIN_FAILURE:
            recommendations.extend(
                [
                    "Review user account for potential compromise",
                    "Consider implementing account lockout policy",
                    "Check for brute force attack patterns",
                ]
            )
        elif event_type == SecurityEventType.PRIVILEGE_ESCALATION:
            recommendations.extend(
                [
                    "Immediately review user privileges",
                    "Investigate potential security breach",
                    "Consider temporary account suspension",
                ]
            )
        elif event_type == SecurityEventType.UNAUTHORIZED_ACCESS:
            recommendations.extend(
                [
                    "Review access control policies",
                    "Investigate user intent and authorization",
                    "Update security configurations if needed",
                ]
            )
        elif event_type == SecurityEventType.MASS_DELETE:
            recommendations.extend(
                [
                    "Immediately investigate data deletion",
                    "Check for data backup availability",
                    "Review user authorization for bulk operations",
                ]
            )
        elif event_type == SecurityEventType.SUSPICIOUS_QUERY:
            recommendations.extend(
                [
                    "Review query patterns and user intent",
                    "Monitor for additional suspicious activity",
                    "Consider query rate limiting",
                ]
            )

        if severity == SecuritySeverity.CRITICAL:
            recommendations.append("Immediate security team notification required")

        return recommendations

    async def _identify_security_issues(self) -> List[Dict[str, Any]]:
        """Identify current security issues."""
        issues = []

        # Check for high-risk users
        high_risk_users = [
            user
            for user, pattern in self.access_patterns.items()
            if pattern.risk_score > 0.7
        ]

        if high_risk_users:
            issues.append(
                {
                    "type": "high_risk_users",
                    "severity": "high",
                    "description": f"Found {len(high_risk_users)} high-risk users",
                    "details": high_risk_users[:10],  # Limit to top 10
                }
            )

        # Check for after hours activity
        after_hours_users = []
        restricted_hours = self.security_config["restricted_hours"]

        for user, pattern in self.access_patterns.items():
            after_hours_count = sum(
                count
                for hour, count in pattern.time_distribution.items()
                if restricted_hours["start"] <= int(hour)
                or int(hour) < restricted_hours["end"]
            )
            if (
                after_hours_count > pattern.total_queries * 0.5
            ):  # More than 50% after hours
                after_hours_users.append(user)

        if after_hours_users:
            issues.append(
                {
                    "type": "after_hours_activity",
                    "severity": "medium",
                    "description": f"Found {len(after_hours_users)} users with significant after-hours activity",
                    "details": after_hours_users[:10],
                }
            )

        # Check for data export patterns
        data_export_users = []
        for event in self.security_events:
            if event.event_type == SecurityEventType.DATA_EXPORT:
                data_export_users.append(event.user)

        if data_export_users:
            issues.append(
                {
                    "type": "data_export_activity",
                    "severity": "medium",
                    "description": f"Found {len(set(data_export_users))} users performing data exports",
                    "details": list(set(data_export_users))[:10],
                }
            )

        # Check for active alerts
        active_alerts = [a for a in self.security_alerts if not a.resolved]
        if active_alerts:
            issues.append(
                {
                    "type": "active_security_alerts",
                    "severity": "high",
                    "description": f"Found {len(active_alerts)} unresolved security alerts",
                    "details": [a.alert_id for a in active_alerts[:10]],
                }
            )

        return issues

    def _generate_security_recommendations(
        self, issues: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate security recommendations based on issues."""
        recommendations = []

        issue_types = {issue["type"] for issue in issues}

        if "high_risk_users" in issue_types:
            recommendations.extend(
                [
                    "Implement user behavior analytics",
                    "Review and update access control policies",
                    "Consider additional monitoring for high-risk users",
                ]
            )

        if "after_hours_activity" in issue_types:
            recommendations.extend(
                [
                    "Review after-hours access policies",
                    "Implement time-based access controls",
                    "Add alerts for unusual access times",
                ]
            )

        if "data_export_activity" in issue_types:
            recommendations.extend(
                [
                    "Review data export policies",
                    "Implement data loss prevention measures",
                    "Add approval workflows for large data exports",
                ]
            )

        if "active_security_alerts" in issue_types:
            recommendations.extend(
                [
                    "Address all active security alerts",
                    "Implement automated alert resolution workflows",
                    "Review security incident response procedures",
                ]
            )

        # General recommendations
        recommendations.extend(
            [
                "Regular security audits and assessments",
                "Employee security awareness training",
                "Implement principle of least privilege",
                "Regular access review and cleanup",
            ]
        )

        return recommendations

    async def generate_compliance_report(
        self, period_start: Optional[float] = None, period_end: Optional[float] = None
    ) -> ComplianceReport:
        """Generate compliance report."""
        import uuid

        if period_start is None:
            period_start = time.time() - (30 * 24 * 60 * 60)  # Last 30 days
        if period_end is None:
            period_end = time.time()

        # Filter events by period
        period_events = [
            e for e in self.security_events if period_start <= e.timestamp <= period_end
        ]

        # Count events by severity
        critical_events = len(
            [e for e in period_events if e.severity == SecuritySeverity.CRITICAL]
        )
        high_events = len(
            [e for e in period_events if e.severity == SecuritySeverity.HIGH]
        )
        medium_events = len(
            [e for e in period_events if e.severity == SecuritySeverity.MEDIUM]
        )
        low_events = len(
            [e for e in period_events if e.severity == SecuritySeverity.LOW]
        )

        # Extract users with access
        users_with_access = set(e.user for e in period_events)

        # Count specific event types
        privileged_actions = len(
            [e for e in period_events if e.event_type == SecurityEventType.ADMIN_ACTION]
        )
        data_exports = len(
            [e for e in period_events if e.event_type == SecurityEventType.DATA_EXPORT]
        )
        failed_logins = len(
            [
                e
                for e in period_events
                if e.event_type == SecurityEventType.LOGIN_FAILURE
            ]
        )

        # Calculate compliance score
        total_events = len(period_events)
        if total_events > 0:
            # Weight events by severity (lower score is better)
            weighted_score = (
                critical_events * 4
                + high_events * 3
                + medium_events * 2
                + low_events * 1
            ) / total_events
            compliance_score = max(0, 100 - (weighted_score * 10))
        else:
            compliance_score = 100

        # Generate recommendations
        recommendations = []
        if critical_events > 0:
            recommendations.append("Address critical security events immediately")
        if failed_logins > 100:
            recommendations.append(
                "Review authentication policies and implement stronger controls"
            )
        if data_exports > 50:
            recommendations.append(
                "Review data export policies and implement additional controls"
            )

        return ComplianceReport(
            report_id=str(uuid.uuid4())[:8],
            generated_at=time.time(),
            period_start=period_start,
            period_end=period_end,
            total_events=total_events,
            critical_events=critical_events,
            high_events=high_events,
            medium_events=medium_events,
            low_events=low_events,
            users_with_access=users_with_access,
            privileged_actions=privileged_actions,
            data_exports=data_exports,
            failed_logins=failed_logins,
            compliance_score=compliance_score,
            recommendations=recommendations,
        )

    def get_security_summary(self) -> Dict[str, Any]:
        """Get comprehensive security summary."""
        if not self.security_events:
            return {"status": "no_data"}

        # Recent events (last 24 hours)
        recent_events = [
            e for e in self.security_events if time.time() - e.timestamp < 24 * 60 * 60
        ]

        # Event distribution by type
        event_types = defaultdict(int)
        for event in self.security_events:
            event_types[event.event_type.value] += 1

        # Event distribution by severity
        severity_counts = defaultdict(int)
        for event in self.security_events:
            severity_counts[event.severity.value] += 1

        # Top risk users
        risk_users = sorted(
            [
                (user, pattern.risk_score)
                for user, pattern in self.access_patterns.items()
            ],
            key=lambda x: x[1],
            reverse=True,
        )[:10]

        # Active alerts
        active_alerts = [a for a in self.security_alerts if not a.resolved]

        return {
            "total_events": len(self.security_events),
            "recent_events_24h": len(recent_events),
            "active_alerts": len(active_alerts),
            "monitored_users": len(self.access_patterns),
            "failed_login_attempts": dict(self.failed_login_attempts),
            "event_types": dict(event_types),
            "severity_distribution": dict(severity_counts),
            "top_risk_users": risk_users,
            "critical_alerts": len(
                [a for a in active_alerts if a.severity == SecuritySeverity.CRITICAL]
            ),
            "high_risk_alerts": len(
                [a for a in active_alerts if a.severity == SecuritySeverity.HIGH]
            ),
        }

    async def start_monitoring(self, interval_seconds: int = 60) -> asyncio.Task:
        """Start continuous security monitoring."""

        async def monitor():
            while True:
                try:
                    # Analyze access patterns
                    await self._analyze_access_patterns()

                    # Check for anomalies
                    await self._check_for_anomalies()

                    # Clean up old data
                    await self._cleanup_old_data()

                    await asyncio.sleep(interval_seconds)
                except Exception as e:
                    logger.error(f"Security monitoring error: {e}")
                    await asyncio.sleep(interval_seconds)

        self._auditing_task = asyncio.create_task(monitor)
        return self._auditing_task

    async def _analyze_access_patterns(self) -> None:
        """Analyze user access patterns for anomalies."""
        for user, pattern in self.access_patterns.items():
            # Check for sudden increase in activity
            if pattern.total_queries > 1000 and pattern.total_queries % 1000 < 10:
                await self.log_security_event(
                    event_type=SecurityEventType.SUSPICIOUS_QUERY,
                    user=user,
                    action="high_volume_queries",
                    severity=SecuritySeverity.MEDIUM,
                    context={"query_count": pattern.total_queries},
                )

    async def _check_for_anomalies(self) -> None:
        """Check for security anomalies."""
        # Check for unusual access times
        current_hour = int(time.strftime("%H"))
        if (
            self.security_config["restricted_hours"]["start"] <= current_hour
            or current_hour < self.security_config["restricted_hours"]["end"]
        ):
            # During restricted hours, check for unusual activity
            for event in self.security_events:
                if (
                    time.time() - event.timestamp < 300  # Last 5 minutes
                    and event.user not in self.security_config["privileged_users"]
                ):
                    await self.log_security_event(
                        event_type=SecurityEventType.SUSPICIOUS_QUERY,
                        user=event.user,
                        action="after_hours_access",
                        severity=SecuritySeverity.LOW,
                        ip_address=event.ip_address,
                    )

    async def _cleanup_old_data(self) -> None:
        """Clean up old security data."""
        cutoff_time = time.time() - (90 * 24 * 60 * 60)  # Keep 90 days

        # Clean up old events
        self.security_events = deque(
            (e for e in self.security_events if e.timestamp >= cutoff_time),
            maxlen=10000,
        )

        # Clean up old access patterns for inactive users
        inactive_users = [
            user
            for user, pattern in self.access_patterns.items()
            if time.time() - pattern.last_activity
            > (30 * 24 * 60 * 60)  # 30 days inactive
        ]

        for user in inactive_users:
            del self.access_patterns[user]

    async def stop_monitoring(self) -> None:
        """Stop continuous monitoring."""
        if self._auditing_task:
            self._auditing_task.cancel()
            self._auditing_task = None

        if self._analysis_task:
            self._analysis_task.cancel()
            self._analysis_task = None


# Global security auditor instance
_security_auditor: SecurityAuditor | None = None


def get_security_auditor() -> SecurityAuditor:
    """Get global security auditor instance."""
    global _security_auditor
    if _security_auditor is None:
        raise RuntimeError(
            "Security auditor not initialized. Call init_security_auditor() first."
        )
    return _security_auditor


async def init_security_auditor(
    db_pool: asyncpg.Pool, alert_manager: Optional[Any] = None
) -> SecurityAuditor:
    """Initialize global security auditor."""
    global _security_auditor
    _security_auditor = SecurityAuditor(db_pool, alert_manager)
    return _security_auditor
