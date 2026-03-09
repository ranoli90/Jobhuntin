"""
Application notes system for tracking application progress and insights.

Provides:
  - Add and manage notes for individual applications
  - Note categorization and tagging
  - Note search and filtering
  - Note sharing and collaboration
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from shared.logging_config import get_logger

logger = get_logger("sorce.application_notes")

# Note categories
NOTE_CATEGORIES = [
    "general",
    "contact_info",
    "interview_prep",
    "follow_up",
    "feedback",
    "questions",
    "research",
    "salary_info",
    "next_steps",
    "personal_notes",
]


class ApplicationNote(BaseModel):
    """Application note with metadata."""

    id: str
    application_id: str
    user_id: str
    tenant_id: str
    title: str
    content: str
    category: str
    tags: List[str] = []
    is_private: bool = True
    is_pinned: bool = False
    reminder_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    author_id: str  # For shared notes


class NoteTemplate(BaseModel):
    """Note template for common note types."""

    id: str
    name: str
    category: str
    title_template: str
    content_template: str
    suggested_tags: List[str] = []
    is_default: bool = False


class NoteSearchResult(BaseModel):
    """Note search result."""

    note: ApplicationNote
    relevance_score: float
    matched_terms: List[str] = []


class ApplicationNotesManager:
    """Manages application notes and templates."""

    def __init__(self, db_pool):
        self.db_pool = db_pool
        self.templates = self._initialize_templates()

    async def create_note(
        self,
        tenant_id: str,
        user_id: str,
        application_id: str,
        title: str,
        content: str,
        category: str = "general",
        tags: List[str] = None,
        is_private: bool = True,
        is_pinned: bool = False,
        reminder_date: Optional[datetime] = None,
    ) -> ApplicationNote:
        """Create a new application note."""

        note_id = str(uuid.uuid4())

        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO application_notes (
                    id, application_id, user_id, tenant_id, title, content,
                    category, tags, is_private, is_pinned, reminder_date,
                    author_id, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, NOW(), NOW())
                """,
                note_id,
                application_id,
                user_id,
                tenant_id,
                title,
                content,
                category,
                tags or [],
                is_private,
                is_pinned,
                reminder_date,
                user_id,  # Author is the creator
            )

            note = ApplicationNote(
                id=note_id,
                application_id=application_id,
                user_id=user_id,
                tenant_id=tenant_id,
                title=title,
                content=content,
                category=category,
                tags=tags or [],
                is_private=is_private,
                is_pinned=is_pinned,
                reminder_date=reminder_date,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                author_id=user_id,
            )

            logger.info(
                "Created note %s for application %s by user %s",
                note_id,
                application_id,
                user_id,
            )

            return note

    async def get_application_notes(
        self,
        tenant_id: str,
        user_id: str,
        application_id: str,
        category: Optional[str] = None,
        include_private: bool = True,
        limit: int = 50,
    ) -> List[ApplicationNote]:
        """Get notes for a specific application."""

        async with self.db_pool.acquire() as conn:
            query = """
            SELECT * FROM application_notes
            WHERE application_id = $1 AND tenant_id = $2
            """
            params = [application_id, tenant_id]
            param_idx = 3

            if not include_private:
                query += f" AND (is_private = false OR user_id = ${param_idx})"
                params.append(user_id)
                param_idx += 1

            if category:
                query += f" AND category = ${param_idx}"
                params.append(category)
                param_idx += 1

            query += " ORDER BY is_pinned DESC, updated_at DESC LIMIT $" + str(
                param_idx
            )
            params.append(limit)

            rows = await conn.fetch(query, *params)

            notes = []
            for row in rows:
                note = ApplicationNote(
                    id=row["id"],
                    application_id=row["application_id"],
                    user_id=row["user_id"],
                    tenant_id=row["tenant_id"],
                    title=row["title"],
                    content=row["content"],
                    category=row["category"],
                    tags=row.get("tags", []),
                    is_private=row["is_private"],
                    is_pinned=row["is_pinned"],
                    reminder_date=row.get("reminder_date"),
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    author_id=row["author_id"],
                )
                notes.append(note)

            return notes

    async def update_note(
        self,
        tenant_id: str,
        user_id: str,
        note_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        is_private: Optional[bool] = None,
        is_pinned: Optional[bool] = None,
        reminder_date: Optional[datetime] = None,
    ) -> bool:
        """Update an existing note."""

        async with self.db_pool.acquire() as conn:
            # Build update query dynamically
            update_fields = []
            params = [note_id, tenant_id, user_id]
            param_idx = 4

            if title is not None:
                update_fields.append(f"title = ${param_idx}")
                params.append(title)
                param_idx += 1

            if content is not None:
                update_fields.append(f"content = ${param_idx}")
                params.append(content)
                param_idx += 1

            if category is not None:
                update_fields.append(f"category = ${param_idx}")
                params.append(category)
                param_idx += 1

            if tags is not None:
                update_fields.append(f"tags = ${param_idx}")
                params.append(tags)
                param_idx += 1

            if is_private is not None:
                update_fields.append(f"is_private = ${param_idx}")
                params.append(is_private)
                param_idx += 1

            if is_pinned is not None:
                update_fields.append(f"is_pinned = ${param_idx}")
                params.append(is_pinned)
                param_idx += 1

            if reminder_date is not None:
                update_fields.append(f"reminder_date = ${param_idx}")
                params.append(reminder_date)
                param_idx += 1

            if update_fields:
                update_fields.append("updated_at = NOW()")
                query = f"""
                UPDATE application_notes
                SET {", ".join(update_fields)}
                WHERE id = $1 AND tenant_id = $2 AND user_id = $3
                """

                result = await conn.execute(query, *params)
                return result == "UPDATE 1"

            return False

    async def delete_note(
        self,
        tenant_id: str,
        user_id: str,
        note_id: str,
    ) -> bool:
        """Delete a note."""

        async with self.db_pool.acquire() as conn:
            result = await conn.execute(
                """
                DELETE FROM application_notes
                WHERE id = $1 AND tenant_id = $2 AND user_id = $3
                """,
                note_id,
                tenant_id,
                user_id,
            )

            return result == "DELETE 1"

    async def search_notes(
        self,
        tenant_id: str,
        user_id: str,
        search_query: str,
        application_id: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 20,
    ) -> List[NoteSearchResult]:
        """Search notes with relevance scoring."""

        async with self.db_pool.acquire() as conn:
            query = """
            SELECT *,
                   ts_rank_cd(to_tsvector('english', title || ' ' || content), plainto_tsquery($1)) as relevance
            FROM application_notes
            WHERE tenant_id = $2 AND user_id = $3
              AND (to_tsvector('english', title || ' ' || content) @@ plainto_tsquery($1))
            """
            params = [search_query, tenant_id, user_id]
            param_idx = 4

            if application_id:
                query += f" AND application_id = ${param_idx}"
                params.append(application_id)
                param_idx += 1

            if category:
                query += f" AND category = ${param_idx}"
                params.append(category)
                param_idx += 1

            if tags:
                query += f" AND tags && ${param_idx}"
                params.append(tags)
                param_idx += 1

            query += (
                " ORDER BY relevance DESC, is_pinned DESC, updated_at DESC LIMIT $"
                + str(param_idx)
            )
            params.append(limit)

            rows = await conn.fetch(query, *params)

            results = []
            for row in rows:
                note = ApplicationNote(
                    id=row["id"],
                    application_id=row["application_id"],
                    user_id=row["user_id"],
                    tenant_id=row["tenant_id"],
                    title=row["title"],
                    content=row["content"],
                    category=row["category"],
                    tags=row.get("tags", []),
                    is_private=row["is_private"],
                    is_pinned=row["is_pinned"],
                    reminder_date=row.get("reminder_date"),
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    author_id=row["author_id"],
                )

                # Extract matched terms (simplified)
                search_terms = search_query.lower().split()
                matched_terms = []
                for term in search_terms:
                    if term in note.title.lower() or term in note.content.lower():
                        matched_terms.append(term)

                result = NoteSearchResult(
                    note=note,
                    relevance_score=row["relevance"],
                    matched_terms=matched_terms,
                )
                results.append(result)

            return results

    async def get_notes_with_reminders(
        self,
        tenant_id: str,
        user_id: str,
        days_ahead: int = 7,
    ) -> List[ApplicationNote]:
        """Get notes with upcoming reminders."""

        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM application_notes
                WHERE tenant_id = $1 AND user_id = $2
                  AND reminder_date IS NOT NULL
                  AND reminder_date <= NOW() + INTERVAL '${param_idx} days'
                  AND reminder_date >= NOW()
                ORDER BY reminder_date ASC
                """,
                tenant_id,
                user_id,
                days_ahead,
            )

            notes = []
            for row in rows:
                note = ApplicationNote(
                    id=row["id"],
                    application_id=row["application_id"],
                    user_id=row["user_id"],
                    tenant_id=row["tenant_id"],
                    title=row["title"],
                    content=row["content"],
                    category=row["category"],
                    tags=row.get("tags", []),
                    is_private=row["is_private"],
                    is_pinned=row["is_pinned"],
                    reminder_date=row["reminder_date"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    author_id=row["author_id"],
                )
                notes.append(note)

            return notes

    async def get_note_templates(
        self,
        category: Optional[str] = None,
    ) -> List[NoteTemplate]:
        """Get available note templates."""

        templates = list(self.templates.values())

        if category:
            templates = [t for t in templates if t.category == category]

        return templates

    async def create_note_from_template(
        self,
        tenant_id: str,
        user_id: str,
        application_id: str,
        template_id: str,
        variables: Dict[str, str],
    ) -> ApplicationNote:
        """Create a note from a template."""

        template = self.templates.get(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")

        # Substitute variables in template
        title = template.title_template
        content = template.content_template

        for key, value in variables.items():
            title = title.replace(f"{{{key}}}", value)
            content = content.replace(f"{{{key}}}", value)

        return await self.create_note(
            tenant_id=tenant_id,
            user_id=user_id,
            application_id=application_id,
            title=title,
            content=content,
            category=template.category,
            tags=template.suggested_tags,
        )

    async def get_note_statistics(
        self,
        tenant_id: str,
        user_id: str,
        days_back: int = 30,
    ) -> Dict[str, Any]:
        """Get statistics about user's notes."""

        async with self.db_pool.acquire() as conn:
            # Total notes
            total_notes = await conn.fetchval(
                """
                SELECT COUNT(*) FROM application_notes
                WHERE tenant_id = $1 AND user_id = $2
                  AND created_at >= NOW() - INTERVAL '${param_idx} days'
                """,
                tenant_id,
                user_id,
                days_back,
            )

            # Notes by category
            category_stats = await conn.fetch(
                """
                SELECT category, COUNT(*) as count
                FROM application_notes
                WHERE tenant_id = $1 AND user_id = $2
                  AND created_at >= NOW() - INTERVAL '${param_idx} days'
                GROUP BY category
                ORDER BY count DESC
                """,
                tenant_id,
                user_id,
                days_back,
            )

            # Pinned notes
            pinned_notes = await conn.fetchval(
                """
                SELECT COUNT(*) FROM application_notes
                WHERE tenant_id = $1 AND user_id = $2 AND is_pinned = true
                """,
                tenant_id,
                user_id,
            )

            # Notes with reminders
            reminder_notes = await conn.fetchval(
                """
                SELECT COUNT(*) FROM application_notes
                WHERE tenant_id = $1 AND user_id = $2 AND reminder_date IS NOT NULL
                """,
                tenant_id,
                user_id,
            )

            return {
                "total_notes": total_notes,
                "pinned_notes": pinned_notes,
                "reminder_notes": reminder_notes,
                "category_breakdown": {
                    row["category"]: row["count"] for row in category_stats
                },
                "period_days": days_back,
            }

    def _initialize_templates(self) -> Dict[str, NoteTemplate]:
        """Initialize default note templates."""

        templates = {}

        # Interview preparation template
        templates["interview_prep"] = NoteTemplate(
            id="interview_prep",
            name="Interview Preparation",
            category="interview_prep",
            title_template="Interview Prep - {company_name}",
            content_template="""
Interview Details:
- Date: {interview_date}
- Time: {interview_time}
- Location: {interview_location}
- Interviewer(s): {interviewers}

Research Points:
- Company values:
- Recent news:
- Key products/services:

Questions to Ask:
1.
2.
3.

Key Points to Emphasize:
- {key_point_1}
- {key_point_2}
- {key_point_3}

Notes:
""",
            suggested_tags=["interview", "preparation", "questions"],
            is_default=True,
        )

        # Contact information template
        templates["contact_info"] = NoteTemplate(
            id="contact_info",
            name="Contact Information",
            category="contact_info",
            title_template="Contact Info - {contact_name}",
            content_template="""
Name: {contact_name}
Title: {contact_title}
Company: {company_name}
Email: {contact_email}
Phone: {contact_phone}
LinkedIn: {linkedin_profile}

Notes:
- {notes_1}
- {notes_2}

Communication History:
""",
            suggested_tags=["contact", "networking", "information"],
            is_default=True,
        )

        # Follow-up template
        templates["follow_up"] = NoteTemplate(
            id="follow_up",
            name="Follow-up Actions",
            category="follow_up",
            title_template="Follow-up - {follow_up_type}",
            content_template="""
Follow-up Type: {follow_up_type}
Date: {follow_up_date}
Method: {method} (email/phone/in-person)

Action Items:
- [ ] {action_1}
- [ ] {action_2}
- [ ] {action_3}

Next Steps:
{next_steps}

Status: {status}
""",
            suggested_tags=["follow-up", "action", "status"],
            is_default=True,
        )

        # Research template
        templates["research"] = NoteTemplate(
            id="research",
            name="Company Research",
            category="research",
            title_template="Research - {company_name}",
            content_template="""
Company Overview:
- Founded: {founded_year}
- Size: {company_size}
- Industry: {industry}
- Location: {location}

Recent News/Updates:
- {news_1}
- {news_2}

Key People:
- {key_person_1}: {role_1}
- {key_person_2}: {role_2}

Culture/Values:
- {culture_1}
- {culture_2}

Financial/Performance:
- {financial_info}

Competitors:
- {competitor_1}
- {competitor_2}
""",
            suggested_tags=["research", "company", "analysis"],
            is_default=True,
        )

        return templates


# Factory function
def create_application_notes_manager(db_pool) -> ApplicationNotesManager:
    """Create application notes manager instance."""
    return ApplicationNotesManager(db_pool)
