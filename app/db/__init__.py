"""database package.

exports:
    - get_db: fastapi dependency for database sessions
    - get_db_context: context manager for database sessions
    - verify_database: database verification function
    - check_database_connection: connection check with retry
    - get_table_info: table inspection utility
    - analyze_query: query plan analyzer
    - optimize_database: database optimization utility
    - get_database_stats: database statistics utility
"""

from app.db.session import get_db, get_db_context, verify_database
from app.db.utils import (
    check_database_connection,
    get_table_info,
    analyze_query,
    optimize_database,
    get_database_stats,
)
