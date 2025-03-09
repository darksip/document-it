#!/usr/bin/env python3
"""
Database Administration Tool for Document-it.

This script provides command-line utilities for managing the Document-it database,
including resetting the database, checking its status, and performing maintenance tasks.
"""

import argparse
import logging
import os
import sys
from typing import Optional, List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("document-it.db-admin")

# Import document-it modules
from document_it.database.manager import DatabaseManager
from document_it.database.models import Base
from sqlalchemy import text

class DatabaseAdmin:
    """
    Database administration tool for Document-it.
    
    This class provides methods for managing the Document-it database,
    including resetting the database, checking its status, and performing
    maintenance tasks.
    """
    
    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize the database admin tool.
        
        Args:
            database_url: Database URL (defaults to DATABASE_URL environment variable)
        """
        self.db_manager = DatabaseManager(database_url)
        logger.info(f"Database admin initialized with {self.db_manager._get_sanitized_db_url()}")
    
    def reset_database(self, confirm: bool = False) -> bool:
        """
        Reset the database by dropping and recreating all tables.
        
        Args:
            confirm: Whether to skip confirmation prompt
            
        Returns:
            True if successful, False otherwise
        """
        if not confirm:
            response = input("WARNING: This will delete all data in the database. Are you sure? (y/N): ")
            if response.lower() != 'y':
                logger.info("Database reset cancelled")
                return False
        
        try:
            # Create a session
            session = self.db_manager.get_session()
            
            try:
                # Drop all tables
                logger.info("Dropping all tables...")
                Base.metadata.drop_all(self.db_manager.engine)
                
                # Create all tables
                logger.info("Creating all tables...")
                Base.metadata.create_all(self.db_manager.engine)
                
                # Verify pgvector extension
                if not self.db_manager.check_pgvector_extension():
                    logger.warning("pgvector extension not installed, vector search will not work")
                else:
                    logger.info("pgvector extension is installed and working")
                
                logger.info("Database reset completed successfully")
                return True
            
            except Exception as e:
                logger.error(f"Error resetting database: {str(e)}")
                return False
            
            finally:
                # Close session
                self.db_manager.close_session(session)
        
        except Exception as e:
            logger.error(f"Error connecting to database: {str(e)}")
            return False
    
    def check_database_status(self) -> Dict[str, Any]:
        """
        Check the status of the database.
        
        Returns:
            Dictionary with database status information
        """
        status = {
            "connection": False,
            "pgvector": False,
            "tables": [],
            "row_counts": {},
            "schema_version": "unknown"
        }
        
        try:
            # Check connection
            if self.db_manager.check_connection():
                status["connection"] = True
                logger.info("Database connection successful")
            else:
                logger.error("Database connection failed")
                return status
            
            # Check pgvector extension
            if self.db_manager.check_pgvector_extension():
                status["pgvector"] = True
                logger.info("pgvector extension is installed")
            else:
                logger.warning("pgvector extension not installed")
            
            # Create a session
            session = self.db_manager.get_session()
            
            try:
                # Get list of tables
                result = session.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'document_it'
                """)).fetchall()
                
                tables = [row[0] for row in result]
                status["tables"] = tables
                
                # Get row counts for each table
                for table in tables:
                    count_result = session.execute(text(f"""
                        SELECT COUNT(*) FROM document_it.{table}
                    """)).scalar()
                    status["row_counts"][table] = count_result
                
                # Try to get schema version from alembic_version table
                try:
                    version_result = session.execute(text("""
                        SELECT version_num FROM alembic_version
                    """)).scalar()
                    if version_result:
                        status["schema_version"] = version_result
                except Exception:
                    # Alembic might not be set up
                    pass
                
                logger.info(f"Database has {len(tables)} tables")
                for table, count in status["row_counts"].items():
                    logger.info(f"Table {table}: {count} rows")
                
                return status
            
            finally:
                # Close session
                self.db_manager.close_session(session)
        
        except Exception as e:
            logger.error(f"Error checking database status: {str(e)}")
            return status
    
    def vacuum_database(self) -> bool:
        """
        Perform VACUUM operation on the database to reclaim storage.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create a session
            session = self.db_manager.get_session()
            
            try:
                # VACUUM requires its own transaction
                session.execute(text("VACUUM FULL ANALYZE"))
                logger.info("Database vacuum completed successfully")
                return True
            
            except Exception as e:
                logger.error(f"Error vacuuming database: {str(e)}")
                return False
            
            finally:
                # Close session
                self.db_manager.close_session(session)
        
        except Exception as e:
            logger.error(f"Error connecting to database: {str(e)}")
            return False
    
    def initialize_schema(self) -> bool:
        """
        Initialize the database schema without dropping existing tables.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create all tables if they don't exist
            logger.info("Creating tables if they don't exist...")
            Base.metadata.create_all(self.db_manager.engine)
            
            # Verify pgvector extension
            if not self.db_manager.check_pgvector_extension():
                logger.warning("pgvector extension not installed, vector search will not work")
            else:
                logger.info("pgvector extension is installed and working")
            
            logger.info("Schema initialization completed successfully")
            return True
        
        except Exception as e:
            logger.error(f"Error initializing schema: {str(e)}")
            return False
    
    def truncate_tables(self, tables: Optional[List[str]] = None, confirm: bool = False) -> bool:
        """
        Truncate specified tables or all tables.
        
        Args:
            tables: List of tables to truncate (None for all tables)
            confirm: Whether to skip confirmation prompt
            
        Returns:
            True if successful, False otherwise
        """
        if not confirm:
            if tables:
                table_list = ", ".join(tables)
                response = input(f"WARNING: This will delete all data in tables: {table_list}. Are you sure? (y/N): ")
            else:
                response = input("WARNING: This will delete all data in ALL tables. Are you sure? (y/N): ")
            
            if response.lower() != 'y':
                logger.info("Truncate operation cancelled")
                return False
        
        try:
            # Create a session
            session = self.db_manager.get_session()
            
            try:
                # Get list of tables if not provided
                if not tables:
                    result = session.execute(text("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = 'document_it'
                    """)).fetchall()
                    
                    tables = [row[0] for row in result]
                
                # Truncate each table
                for table in tables:
                    session.execute(text(f"TRUNCATE TABLE document_it.{table} CASCADE"))
                
                # Commit the transaction
                session.commit()
                
                logger.info(f"Truncated {len(tables)} tables")
                return True
            
            except Exception as e:
                logger.error(f"Error truncating tables: {str(e)}")
                session.rollback()
                return False
            
            finally:
                # Close session
                self.db_manager.close_session(session)
        
        except Exception as e:
            logger.error(f"Error connecting to database: {str(e)}")
            return False

def main():
    """Main function to run the database admin tool."""
    parser = argparse.ArgumentParser(description="Document-it Database Administration Tool")
    
    # Add subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Reset command
    reset_parser = subparsers.add_parser("reset", help="Reset the database by dropping and recreating all tables")
    reset_parser.add_argument("--force", action="store_true", help="Skip confirmation prompt")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Check the status of the database")
    
    # Vacuum command
    vacuum_parser = subparsers.add_parser("vacuum", help="Perform VACUUM operation on the database")
    
    # Initialize command
    init_parser = subparsers.add_parser("init", help="Initialize the database schema without dropping existing tables")
    
    # Truncate command
    truncate_parser = subparsers.add_parser("truncate", help="Truncate specified tables or all tables")
    truncate_parser.add_argument("--tables", nargs="+", help="List of tables to truncate (omit for all tables)")
    truncate_parser.add_argument("--force", action="store_true", help="Skip confirmation prompt")
    
    # Database URL option for all commands
    parser.add_argument("--database-url", help="Database URL (defaults to DATABASE_URL environment variable)")
    
    args = parser.parse_args()
    
    # Create database admin
    db_admin = DatabaseAdmin(args.database_url)
    
    # Execute command
    if args.command == "reset":
        success = db_admin.reset_database(confirm=args.force)
        return 0 if success else 1
    
    elif args.command == "status":
        status = db_admin.check_database_status()
        return 0 if status["connection"] else 1
    
    elif args.command == "vacuum":
        success = db_admin.vacuum_database()
        return 0 if success else 1
    
    elif args.command == "init":
        success = db_admin.initialize_schema()
        return 0 if success else 1
    
    elif args.command == "truncate":
        success = db_admin.truncate_tables(tables=args.tables, confirm=args.force)
        return 0 if success else 1
    
    else:
        parser.print_help()
        return 1

if __name__ == "__main__":
    sys.exit(main())