from datetime import datetime, timezone
from typing import List, Optional
import uuid
from sqlalchemy import String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from ..db import Base


def utc_now():
    return datetime.now(timezone.utc)


class VideoAudit(Base):
    __tablename__ = "video_audits"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_url: Mapped[str] = mapped_column(String(512), nullable=False)
    video_id: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    transcript: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ocr_text: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    
    # final_status can be: pending, processing, pass, fail, needs_review
    final_status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    final_report: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    errors: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    complaice_result: Mapped[List["ComplianceIssue"]] = relationship(back_populates="video_audit", cascade="all, delete-orphan", lazy="selectin")


class ComplianceIssue(Base):
    __tablename__ = "compliance_issues"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    video_audit_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("video_audits.id", ondelete="CASCADE"), nullable=False)
    category: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(50), nullable=False)
    timestamp: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Relationships
    video_audit: Mapped["VideoAudit"] = relationship(back_populates="compliance_results")