"""add interview session persistence

Revision ID: 20260606_0002
Revises: 20260603_0001
Create Date: 2026-06-06 16:30:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260606_0002"
down_revision = "20260603_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "interview_sessions",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("knowledge_base_id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("reference_answer", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("overall_score", sa.Integer(), nullable=True),
        sa.Column("strengths", sa.JSON(), nullable=True),
        sa.Column("improvements", sa.JSON(), nullable=True),
        sa.Column("suggested_followup", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["knowledge_base_id"], ["knowledge_bases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["question_id"], ["question_bank.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_interview_sessions_user_id"), "interview_sessions", ["user_id"], unique=False)
    op.create_index(op.f("ix_interview_sessions_knowledge_base_id"), "interview_sessions", ["knowledge_base_id"], unique=False)
    op.create_index(op.f("ix_interview_sessions_question_id"), "interview_sessions", ["question_id"], unique=False)

    op.create_table(
        "interview_turns",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.String(length=32), nullable=False),
        sa.Column("role", sa.String(length=30), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("meta_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["interview_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_interview_turns_session_id"), "interview_turns", ["session_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_interview_turns_session_id"), table_name="interview_turns")
    op.drop_table("interview_turns")
    op.drop_index(op.f("ix_interview_sessions_question_id"), table_name="interview_sessions")
    op.drop_index(op.f("ix_interview_sessions_knowledge_base_id"), table_name="interview_sessions")
    op.drop_index(op.f("ix_interview_sessions_user_id"), table_name="interview_sessions")
    op.drop_table("interview_sessions")
