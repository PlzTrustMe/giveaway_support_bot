"""Routing metadata for Alembic. No messages or user profiles are stored."""

import sqlalchemy as sa

metadata = sa.MetaData()

support_threads = sa.Table(
    "support_threads",
    metadata,
    sa.Column("user_id", sa.BigInteger, primary_key=True, autoincrement=False),
    sa.Column("group_chat_id", sa.BigInteger, primary_key=True, autoincrement=False),
    sa.Column("thread_id", sa.BigInteger, nullable=False),
    sa.Column("card_message_id", sa.BigInteger),
    sa.Column("is_banned", sa.Boolean, nullable=False, server_default=sa.false()),
    sa.UniqueConstraint(
        "group_chat_id", "thread_id", name="uq_support_threads_group_thread"
    ),
)
