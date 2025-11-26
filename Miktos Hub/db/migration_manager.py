"""
Database Migration Manager

Provides programmatic access to Alembic migrations for
automatic database upgrades on server startup.
"""

import logging
from pathlib import Path
from typing import Optional, List, Tuple

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine

logger = logging.getLogger(__name__)


class MigrationManager:
    """
    Manages database migrations using Alembic.

    Provides methods to check migration status, run upgrades,
    and handle migration failures gracefully.

    Example:
        ```python
        manager = MigrationManager()

        # Check if migrations are needed
        if manager.has_pending_migrations():
            print("Running migrations...")
            manager.upgrade()
        ```
    """

    def __init__(
        self,
        database_url: Optional[str] = None,
        alembic_ini_path: Optional[str] = None
    ):
        """
        Initialize migration manager.

        Args:
            database_url: SQLite database URL (uses config if None)
            alembic_ini_path: Path to alembic.ini (auto-detected if None)
        """
        # Get project root
        self._project_root = Path(__file__).parent.parent

        # Set alembic.ini path
        if alembic_ini_path is None:
            alembic_ini_path = str(self._project_root / "alembic.ini")

        self._alembic_cfg = Config(alembic_ini_path)

        # Set database URL if provided
        if database_url:
            self._alembic_cfg.set_main_option(
                "sqlalchemy.url",
                database_url
            )

        # Get database URL for direct queries
        if database_url is None:
            from config import get_config
            app_config = get_config()
            db_path = Path(app_config.paths.data_dir) / "miktos_hub.db"
            database_url = f"sqlite:///{db_path}"

        self._database_url = database_url
        logger.info(f"Migration manager initialized for: {database_url}")

    def get_current_revision(self) -> Optional[str]:
        """
        Get current database revision.

        Returns:
            Current revision ID or None if not versioned
        """
        try:
            engine = create_engine(self._database_url)

            with engine.connect() as conn:
                context = MigrationContext.configure(conn)
                current = context.get_current_revision()

            engine.dispose()
            return current

        except Exception as e:
            logger.warning(
                f"Could not get current revision: {e}",
                exc_info=True
            )
            return None

    def get_head_revision(self) -> str:
        """
        Get the latest available migration revision.

        Returns:
            Head revision ID
        """
        script = ScriptDirectory.from_config(self._alembic_cfg)
        head = script.get_current_head()

        if head is None:
            raise RuntimeError("No migrations found in versions directory")

        return head

    def has_pending_migrations(self) -> bool:
        """
        Check if there are pending migrations.

        Returns:
            True if migrations need to be run
        """
        try:
            current = self.get_current_revision()
            head = self.get_head_revision()

            # No current revision means fresh DB - needs migration
            if current is None:
                return True

            # Different revisions mean pending migrations
            return current != head

        except Exception as e:
            logger.error(
                f"Error checking pending migrations: {e}",
                exc_info=True
            )
            return False

    def get_pending_migrations(self) -> List[Tuple[str, str]]:
        """
        Get list of pending migration revisions.

        Returns:
            List of (revision_id, description) tuples
        """
        pending = []

        try:
            script = ScriptDirectory.from_config(self._alembic_cfg)
            current = self.get_current_revision()

            # Get all revisions from current to head
            for rev in script.iterate_revisions(
                upper="head",
                lower=current or "base"
            ):
                # Skip current revision
                if current and rev.revision == current:
                    continue

                pending.append((rev.revision, rev.doc or ""))

        except Exception as e:
            logger.error(
                f"Error getting pending migrations: {e}",
                exc_info=True
            )

        return pending

    def upgrade(
        self,
        revision: str = "head",
        sql: bool = False
    ) -> bool:
        """
        Upgrade database to a later version.

        Args:
            revision: Target revision (default: "head" for latest)
            sql: Only output SQL instead of running (default: False)

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Running database migrations to {revision}...")

            if sql:
                command.upgrade(self._alembic_cfg, revision, sql=True)
            else:
                command.upgrade(self._alembic_cfg, revision)

            logger.info("✓ Database migrations completed successfully")
            return True

        except Exception as e:
            logger.error(
                f"Migration failed: {e}",
                exc_info=True
            )
            return False

    def downgrade(
        self,
        revision: str,
        sql: bool = False
    ) -> bool:
        """
        Downgrade database to a previous version.

        Args:
            revision: Target revision (e.g., "-1" for previous, "base" for
            initial)
            sql: Only output SQL instead of running (default: False)

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.warning(f"Downgrading database to {revision}...")

            if sql:
                command.downgrade(self._alembic_cfg, revision, sql=True)
            else:
                command.downgrade(self._alembic_cfg, revision)

            logger.info("✓ Database downgrade completed")
            return True

        except Exception as e:
            logger.error(
                f"Downgrade failed: {e}",
                exc_info=True
            )
            return False

    def stamp(self, revision: str = "head") -> bool:
        """
        Mark database as being at a specific revision without running
        migrations.

        Useful for initializing migration tracking on existing databases.

        Args:
            revision: Target revision (default: "head")

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Stamping database as revision: {revision}")
            command.stamp(self._alembic_cfg, revision)
            logger.info("✓ Database stamped successfully")
            return True

        except Exception as e:
            logger.error(
                f"Stamp failed: {e}",
                exc_info=True
            )
            return False

    def current(self) -> Optional[str]:
        """
        Get and display current revision.

        Returns:
            Current revision ID or None
        """
        try:
            current = self.get_current_revision()

            if current:
                logger.info(f"Current database revision: {current}")
            else:
                logger.info("Database is not versioned")

            return current

        except Exception as e:
            logger.error(
                f"Error getting current revision: {e}",
                exc_info=True
            )
            return None

    def history(self, verbose: bool = False) -> List[dict]:
        """
        Get migration history.

        Args:
            verbose: Include detailed information

        Returns:
            List of migration info dicts
        """
        history = []

        try:
            script = ScriptDirectory.from_config(self._alembic_cfg)

            for rev in script.walk_revisions():
                info = {
                    "revision": rev.revision,
                    "down_revision": rev.down_revision,
                    "description": rev.doc or "",
                }

                if verbose:
                    # Get module name as string
                    module_name = (
                        rev.module.__name__ if rev.module else ""
                    )
                    info["module"] = module_name  # type: ignore[assignment]

                history.append(info)

        except Exception as e:
            logger.error(
                f"Error getting history: {e}",
                exc_info=True
            )

        return history

    def auto_upgrade_on_startup(self) -> bool:
        """
        Automatically upgrade database to latest version on startup.

        This is the recommended method to call during server initialization.

        Returns:
            True if no migrations needed or upgrade successful
        """
        try:
            # Check if migrations are needed
            if not self.has_pending_migrations():
                logger.info("✓ Database is up to date (no migrations needed)")
                return True

            # Log pending migrations
            pending = self.get_pending_migrations()
            logger.info(
                f"Found {len(pending)} pending migration(s):"
            )
            for rev_id, description in pending:
                logger.info(f"  - {rev_id}: {description}")

            # Run upgrade
            return self.upgrade()

        except Exception as e:
            logger.error(
                f"Auto-upgrade failed: {e}",
                exc_info=True
            )
            return False


def get_migration_manager(
    database_url: Optional[str] = None
) -> MigrationManager:
    """
    Get singleton migration manager instance.

    Args:
        database_url: Database URL (uses config if None)

    Returns:
        MigrationManager instance
    """
    return MigrationManager(database_url=database_url)
