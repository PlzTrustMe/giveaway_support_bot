"""Database metadata for Alembic autogeneration."""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

metadata = sa.MetaData()

users = sa.Table(
    "users",
    metadata,
    sa.Column("tg_id", sa.BigInteger, primary_key=True, autoincrement=False),
    sa.Column("username", sa.Text),
    sa.Column("lang", sa.Text),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
)

tickets = sa.Table(
    "tickets",
    metadata,
    sa.Column("id", sa.BigInteger, sa.Identity(), primary_key=True),
    sa.Column("user_tg_id", sa.BigInteger, nullable=False),
    sa.Column("user_username", sa.Text),
    sa.Column("lang", sa.Text, nullable=False),
    sa.Column("status", sa.Text, nullable=False),
    sa.Column("taken_by_admin_id", sa.BigInteger),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("closed_at", sa.DateTime(timezone=True)),
    sa.Column("last_message_at", sa.DateTime(timezone=True)),
    sa.Column("last_message_preview", sa.Text),
    sa.Column("attachments_count", sa.Integer, nullable=False, server_default="0"),
    sa.Column("admin_group_chat_id", sa.BigInteger),
    sa.Column("admin_thread_id", sa.BigInteger),
    sa.Column("admin_topic_message_id", sa.BigInteger),
    sa.Index("ix_tickets_user_status_id", "user_tg_id", "status", "id"),
    sa.Index("ix_tickets_status_id", "status", "id"),
    sa.Index("ix_tickets_admin_thread", "admin_group_chat_id", "admin_thread_id"),
)

ticket_messages = sa.Table(
    "ticket_messages",
    metadata,
    sa.Column("id", sa.BigInteger, sa.Identity(), primary_key=True),
    sa.Column(
        "ticket_id",
        sa.BigInteger,
        sa.ForeignKey("tickets.id", ondelete="CASCADE"),
        nullable=False,
    ),
    sa.Column("sender_type", sa.Text, nullable=False),
    sa.Column("sender_tg_id", sa.BigInteger, nullable=False),
    sa.Column("text", sa.Text),
    sa.Column(
        "attachments_json", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")
    ),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    sa.Index("ix_ticket_messages_ticket_id_id", "ticket_id", "id"),
)

settings = sa.Table(
    "settings",
    metadata,
    sa.Column("key", sa.Text, primary_key=True),
    sa.Column("lang", sa.Text, primary_key=True),
    sa.Column("value", sa.Text, nullable=False),
    sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
)
