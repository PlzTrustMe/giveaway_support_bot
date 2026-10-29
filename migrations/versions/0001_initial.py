"""Create the support bot schema in PostgreSQL."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("tg_id", sa.BigInteger, primary_key=True, autoincrement=False),
        sa.Column("username", sa.Text),
        sa.Column("lang", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "tickets",
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
    )
    op.create_index(
        "ix_tickets_user_status_id", "tickets", ["user_tg_id", "status", "id"]
    )
    op.create_index("ix_tickets_status_id", "tickets", ["status", "id"])
    op.create_index(
        "ix_tickets_admin_thread", "tickets", ["admin_group_chat_id", "admin_thread_id"]
    )
    op.create_table(
        "ticket_messages",
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
            "attachments_json",
            JSONB,
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_ticket_messages_ticket_id_id", "ticket_messages", ["ticket_id", "id"]
    )
    op.create_table(
        "settings",
        sa.Column("key", sa.Text, primary_key=True),
        sa.Column("lang", sa.Text, primary_key=True),
        sa.Column("value", sa.Text, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("settings")
    op.drop_table("ticket_messages")
    op.drop_table("tickets")
    op.drop_table("users")
