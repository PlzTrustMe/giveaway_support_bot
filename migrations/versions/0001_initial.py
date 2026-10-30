"""Create Telegram user/topic routing without storing message content."""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "support_threads",
        sa.Column("user_id", sa.BigInteger, primary_key=True, autoincrement=False),
        sa.Column(
            "group_chat_id", sa.BigInteger, primary_key=True, autoincrement=False
        ),
        sa.Column("thread_id", sa.BigInteger, nullable=False),
        sa.Column("card_message_id", sa.BigInteger),
        sa.Column("is_banned", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.UniqueConstraint(
            "group_chat_id", "thread_id", name="uq_support_threads_group_thread"
        ),
    )
    create_user_languages()


def create_user_languages() -> None:
    op.create_table(
        "user_languages",
        sa.Column("user_id", sa.BigInteger, primary_key=True, autoincrement=False),
        sa.Column("language_code", sa.Text, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("user_languages")
    op.drop_table("support_threads")
