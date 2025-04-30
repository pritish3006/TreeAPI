#!/usr/bin/env python3
"""migration management script for tree api database."""

import os
import sys
import argparse
from alembic import command
from alembic.config import Config
from pathlib import Path

def get_alembic_config():
    """get alembic configuration."""
    # get project root directory
    root_dir = Path(__file__).parent.parent
    
    # create alembic config
    alembic_cfg = Config(os.path.join(root_dir, "alembic.ini"))
    return alembic_cfg

def create_migration(message):
    """create a new migration revision."""
    cfg = get_alembic_config()
    command.revision(cfg, autogenerate=True, message=message)

def upgrade_db(revision="head"):
    """upgrade database to specified revision."""
    cfg = get_alembic_config()
    command.upgrade(cfg, revision)

def downgrade_db(revision="-1"):
    """downgrade database by one revision."""
    cfg = get_alembic_config()
    command.downgrade(cfg, revision)

def show_history():
    """show migration history."""
    cfg = get_alembic_config()
    command.history(cfg)

def show_current():
    """show current revision."""
    cfg = get_alembic_config()
    command.current(cfg)

def main():
    """main function to handle migration commands."""
    parser = argparse.ArgumentParser(description="manage database migrations")
    
    subparsers = parser.add_subparsers(dest="command", help="commands")
    
    # create migration
    create_parser = subparsers.add_parser("create", help="create new migration")
    create_parser.add_argument("message", help="migration message")
    
    # upgrade
    upgrade_parser = subparsers.add_parser("upgrade", help="upgrade database")
    upgrade_parser.add_argument("--revision", default="head", help="target revision (default: head)")
    
    # downgrade
    downgrade_parser = subparsers.add_parser("downgrade", help="downgrade database")
    downgrade_parser.add_argument("--revision", default="-1", help="target revision (default: -1)")
    
    # history
    subparsers.add_parser("history", help="show migration history")
    
    # current
    subparsers.add_parser("current", help="show current revision")
    
    args = parser.parse_args()
    
    try:
        if args.command == "create":
            create_migration(args.message)
        elif args.command == "upgrade":
            upgrade_db(args.revision)
        elif args.command == "downgrade":
            downgrade_db(args.revision)
        elif args.command == "history":
            show_history()
        elif args.command == "current":
            show_current()
        else:
            parser.print_help()
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 