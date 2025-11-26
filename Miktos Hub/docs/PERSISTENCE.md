# Persistence & Database Management

Miktos Hub includes a robust persistence layer that ensures your camera registrations, sessions, and scenes survive server restarts.

## Overview

The persistence system consists of:

- **SQLite Database**: Lightweight, file-based database stored in your data directory
- **SQLAlchemy ORM**: Type-safe object-relational mapping
- **Alembic Migrations**: Database version control and schema evolution
- **Repository Pattern**: Clean separation between domain models and database models
- **Automatic Recovery**: Sessions, cameras, and scenes automatically restored on startup

## Database Location

By default, the database is stored at:

```text
~/.miktos/data/miktos_hub.db
```

You can configure this location in `config/settings.py` by changing the `data_dir` path.

## What Gets Persisted

### 1. Camera Registrations

When you register a camera (either manually or via auto-discovery), it's saved to the database:

```python
# Camera gets registered
camera = CameraDevice(
    id="sony-a7iv-001",
    label="Main Camera",
    transport=TransportType.SRT,
    url="srt://192.168.1.100:8888"
)
device_registry.register(camera)
# ✓ Automatically saved to database
```

**What's stored:**

- Camera ID, name, and label
- Connection details (URL, transport type)
- Capabilities and metadata
- Registration status and last seen timestamp

**Recovery:**

On server startup, all registered cameras are automatically restored from the database before any other services initialize.

### 2. Sessions

Sessions represent complete streaming shows from preparation through completion:

```python
# Create a session
session = session_manager.create_session(
    name="City Council Meeting - Nov 25",
    camera_ids=["camera-1", "camera-2"]
)
# ✓ Automatically saved to database
```

**What's stored:**

- Session ID, name, and description
- Current state (preparing, ready, live, completed, etc.)
- Associated camera IDs
- Timestamps (created, started, ended)
- Session metadata and configuration

**Recovery:**

Active sessions (not in COMPLETED or FAILED state) are automatically recovered on startup, allowing you to resume interrupted sessions.

### 3. Scenes

OBS scenes created for your cameras are persisted and linked to sessions:

```python
# Create a scene
scene = await obs.create_scene_for_camera(
    camera_id="sony-a7iv-001",
    scene_name="Main Camera Fullscreen",
    session_id="session-123"
)
# ✓ Automatically saved to database
```

**What's stored:**

- Scene ID and name
- Layout type (fullscreen, split, grid, etc.)
- Source configurations (cameras, positions, sizes)
- Association with parent session
- OBS-specific metadata

**Recovery:**

Scenes are restored when their parent sessions are recovered, maintaining your complete scene setup.

## Database Schema

### Tables

#### sessions

- `id` (PK): UUID
- `name`: Session name
- `description`: Optional description
- `state`: Current lifecycle state
- `created_at`, `updated_at`, `started_at`, `ended_at`: Timestamps
- `extra_data`: JSON field for additional metadata

#### cameras

- `id` (PK): Camera identifier
- `name`: Camera label/name
- `stream_url`: Connection URL
- `discovery_method`: How camera was discovered (mdns, manual, etc.)
- `host`, `port`: Network location
- `capabilities`: JSON field for camera capabilities
- `is_active`: Registration status
- `last_seen`: Last heartbeat timestamp
- `created_at`, `updated_at`: Timestamps

#### scenes

- `id` (PK): Scene identifier
- `session_id` (FK): Parent session
- `name`: Scene name
- `sources`: JSON array of source configurations
- `extra_data`: JSON field for layout and OBS metadata
- `created_at`, `updated_at`: Timestamps

#### session_cameras (join table)

- `id` (PK): Auto-increment
- `session_id` (FK): Session reference
- `camera_id` (FK): Camera reference
- `created_at`: When camera was added to session

## Migration System

Miktos Hub uses [Alembic](https://alembic.sqlalchemy.org/) for database version control, allowing schema changes without data loss.

### Automatic Migrations

Migrations run automatically on server startup:

```text
INFO: Checking for database migrations...
INFO: Found 2 pending migration(s):
  - abc123: Add camera capabilities column
  - def456: Add scene layout types
INFO: Running database migrations to head...
INFO: ✓ Database migrations completed successfully
```

If migrations fail, the server will not start, preventing data corruption.

### Manual Migration Commands

You can also run migrations manually using the Alembic CLI:

#### Check current version

```bash
alembic current
```

#### View migration history

```bash
alembic history --verbose
```

#### Upgrade to latest

```bash
alembic upgrade head
```

#### Downgrade one version

```bash
alembic downgrade -1
```

#### Generate new migration

```bash
alembic revision --autogenerate -m "Add new feature"
```

### Creating Migrations

When you modify database models in `db/models.py`:

1. **Generate migration**:

   ```bash
   alembic revision --autogenerate -m "Describe your changes"
   ```

2. **Review generated migration** in `db/migrations/versions/`

3. **Test migration**:

   ```bash
   alembic upgrade head
   ```

4. **Test downgrade** (to verify rollback works):

   ```bash
   alembic downgrade -1
   alembic upgrade head
   ```

5. **Commit migration file** to version control

## Programmatic API

### Migration Manager

```python
from db.migration_manager import get_migration_manager

manager = get_migration_manager()

# Check if migrations are pending
if manager.has_pending_migrations():
    print("Migrations needed!")
    pending = manager.get_pending_migrations()
    for rev_id, description in pending:
        print(f"  - {rev_id}: {description}")

# Run migrations
success = manager.upgrade()

# Get current version
current = manager.get_current_revision()
print(f"Database at revision: {current}")
```

### Direct Database Access

```python
from db import get_database
from db.repositories import CameraRepository, SessionRepository

db = get_database()

# Use repositories for type-safe operations
with db.session() as session:
    camera_repo = CameraRepository(session)
    
    # List all cameras
    cameras = camera_repo.list_all()
    
    # Get specific camera
    camera = camera_repo.get("camera-id")
    
    # Mark camera inactive
    camera_repo.mark_inactive("camera-id")
```

## Recovery Behavior

### Startup Sequence

1. **Check for migrations** → Run if needed
2. **Initialize database** → Create tables if new
3. **Restore cameras** → Load registered cameras
4. **Restore sessions** → Recover active sessions
5. **Restore scenes** → Recreate OBS scenes
6. **Start services** → Normal operation begins

### What Gets Recovered

✅ **Always Recovered:**

- All registered cameras
- Active sessions (not COMPLETED or FAILED)
- Scenes belonging to active sessions

❌ **Not Recovered:**

- Completed sessions
- Failed sessions
- Temporary/transient state
- WebSocket connections
- Active streams (must be restarted)

### Recovery Logs

Watch the startup logs to see recovery in action:

```text
INFO: Recovering cameras from database...
INFO: ✓ Restored 3 camera(s)
INFO: Recovering sessions from database...
INFO: ✓ Recovered 1 session(s)
```

## Backup & Restore

### Backup Database

The database is a single SQLite file, making backups simple:

```bash
# Stop the server first!
cp ~/.miktos/data/miktos_hub.db ~/backups/miktos_hub_$(date +%Y%m%d).db
```

### Automated Backups

Add to crontab for daily backups:

```cron
0 2 * * * cp ~/.miktos/data/miktos_hub.db ~/backups/miktos_hub_$(date +\%Y\%m\%d).db
```

### Restore from Backup

```bash
# Stop the server
# Replace current database
cp ~/backups/miktos_hub_20251125.db ~/.miktos/data/miktos_hub.db
# Start the server
```

## Database Management

### View Database Contents

Use any SQLite browser:

```bash
# Command line
sqlite3 ~/.miktos/data/miktos_hub.db
> .tables
> SELECT * FROM cameras;
> .quit

# Or use GUI tools:
# - DB Browser for SQLite (https://sqlitebrowser.org/)
# - TablePlus
# - DBeaver
```

### Reset Database

To start fresh (⚠️ **deletes all data**):

```bash
# Stop the server
rm ~/.miktos/data/miktos_hub.db
# Start the server (will create new empty database)
```

### Vacuum Database

Optimize database file size:

```bash
sqlite3 ~/.miktos/data/miktos_hub.db "VACUUM;"
```

## Troubleshooting

### Migration Failures

**Problem:** Migration fails on startup

```text
ERROR: Migration failed: ...
```

**Solutions:**

1. Check migration file in `db/migrations/versions/`
2. Review error message for SQL issues
3. Fix migration file or rollback:

   ```bash
   alembic downgrade -1
   ```

4. Re-run migration:

   ```bash
   alembic upgrade head
   ```

### Database Locked

**Problem:** `database is locked` error

**Causes:**

- Multiple Miktos Hub instances running
- Backup in progress
- File system issues

**Solutions:**

1. Ensure only one server instance is running
2. Wait for backups to complete
3. Check file permissions on database file

### Corrupted Database

**Problem:** Database file is corrupted

**Recovery:**

1. Stop the server
2. Try SQLite recovery:

   ```bash
   sqlite3 miktos_hub.db ".recover" | sqlite3 miktos_hub_recovered.db
   ```

3. If recovery fails, restore from backup
4. If no backup exists, delete database (loses all data)

### Lost Data

**Problem:** Sessions/cameras not recovering

**Diagnostics:**

1. Check startup logs for recovery messages
2. Verify database exists and is readable
3. Check database content:

   ```bash
   sqlite3 ~/.miktos/data/miktos_hub.db "SELECT COUNT(*) FROM cameras;"
   ```

4. Review migration status:

   ```bash
   alembic current
   ```

## Best Practices

### Development

- **Always review** auto-generated migrations before committing
- **Test migrations** both upgrade and downgrade
- **Never edit** applied migrations; create new ones instead
- **Use transactions** in custom migration scripts

### Production

- **Backup before migrations**: Especially for major version upgrades
- **Monitor startup logs**: Watch for migration and recovery issues
- **Regular backups**: Automate daily database backups
- **Test recovery**: Periodically test backup restoration

### Performance

- **SQLite is single-writer**: Avoid high-concurrency write scenarios
- **Use WAL mode** for better concurrency (enabled by default)
- **Vacuum periodically**: Reclaim space from deleted data
- **Consider PostgreSQL**: For high-concurrency production deployments

## Advanced Topics

### Custom Queries

```python
from db import get_database
from db.models import CameraModel, SessionModel
from sqlalchemy import and_, or_

db = get_database()

with db.session() as session:
    # Complex query
    active_cams = session.query(CameraModel).filter(
        and_(
            CameraModel.is_active == True,
            CameraModel.capabilities.contains('{"transport": "SRT"}')
        )
    ).all()
```

### Migration Hooks

Add custom logic to migrations:

```python
# In migration file
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Create new column
    op.add_column('cameras', sa.Column('quality_preset', sa.String(50)))
    
    # Migrate existing data
    connection = op.get_bind()
    connection.execute(
        "UPDATE cameras SET quality_preset = 'standard' WHERE quality_preset IS NULL"
    )

def downgrade():
    op.drop_column('cameras', 'quality_preset')
```

### Database URL Configuration

Override database location via environment:

```bash
export MIKTOS_DB_URL="sqlite:////custom/path/miktos.db"
python main.py
```

Or in code:

```python
from db import Database

db = Database(database_url="sqlite:////custom/path/miktos.db")
```

## Related Documentation

- [Database Models](../db/models.py) - SQLAlchemy model definitions
- [Repositories](../db/repositories.py) - Data access layer
- [Migration Manager](../db/migration_manager.py) - Programmatic migration API
- [Server Startup](../hub_api/server.py) - Initialization and recovery logic

## Support

For issues or questions about persistence:

1. Check logs in `~/.miktos/logs/`
2. Review this documentation
3. Check GitHub issues
4. Open a new issue with:
   - Error messages
   - Database file size
   - Migration status output
   - Startup logs
