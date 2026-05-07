"""
Quick test script to verify MongoDB connection and check users collection.
Run from project root: python test_mongo.py
"""
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Setup Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cropsight_backend.settings")

import django
django.setup()

from django.conf import settings
from analyzer.mongo import get_collections, get_db

def test_connection():
    print("=" * 50)
    print("MongoDB Connection Test")
    print("=" * 50)
    
    print(f"\nMongoDB URI: {settings.MONGODB_URI[:50]}...")
    print(f"Database Name: {settings.MONGODB_DB_NAME}")
    
    try:
        db = get_db()
        print(f"\n✓ Connected to database: {db.name}")
        
        collections = get_collections()
        print(f"✓ Collections initialized: {list(collections.keys())}")
        
        # Check users
        users = collections["users"]
        user_count = users.count_documents({})
        print(f"\n✓ Users in database: {user_count}")
        
        # List all users (without passwords)
        if user_count > 0:
            print("\nRegistered users:")
            for user in users.find({}, {"_id": 1, "name": 1, "phone": 1}):
                print(f"  - {user.get('name')} (phone: {user.get('phone')}, id: {user.get('_id')})")
        else:
            print("\n⚠ No users found. Try signing up first.")
        
        # Check analysis results
        results = collections["analysis_results"]
        result_count = results.count_documents({})
        print(f"\n✓ Analysis results in database: {result_count}")
        
        print("\n" + "=" * 50)
        print("✅ MongoDB connection successful!")
        print("=" * 50)
        return True
        
    except Exception as e:
        print(f"\n❌ MongoDB connection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_connection()
