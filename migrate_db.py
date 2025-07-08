"""
Database migration script to add the AppSettings table.
Run this script to update the database schema.
"""

from app import app
from models import db, AppSettings

def migrate_database():
    """Create the AppSettings table if it doesn't exist."""
    with app.app_context():
        try:
            # Create all tables (this will only create missing tables)
            db.create_all()
            
            # Check if voice_provider setting exists, if not create it with default value
            existing_setting = AppSettings.query.filter_by(key='voice_provider').first()
            if not existing_setting:
                default_setting = AppSettings(
                    key='voice_provider',
                    value='google',
                    description='Voice synthesis provider (google or elevenlabs)'
                )
                db.session.add(default_setting)
                db.session.commit()
                print("✅ Created default voice_provider setting (google)")
            else:
                print(f"✅ Voice provider setting already exists: {existing_setting.value}")
            
            print("✅ Database migration completed successfully!")
            
        except Exception as e:
            print(f"❌ Database migration failed: {e}")
            db.session.rollback()

if __name__ == "__main__":
    migrate_database()
