"""
Test database connectivity and operations.
"""
import os
from dotenv import load_dotenv
import psycopg2
from psycopg2 import sql

# Load environment variables
load_dotenv()

def test_database_connection():
    print("Testing PostgreSQL database connection...")
    
    # Get database credentials
    db_host = os.getenv("POSTGRES_HOST", "localhost")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB", "finops")
    db_user = os.getenv("POSTGRES_USER", "postgres")
    db_password = os.getenv("POSTGRES_PASSWORD", "pgadmin777")
    
    # Check if credentials are available
    if not all([db_host, db_port, db_name, db_user, db_password]):
        print("❌ Database credentials not found in environment variables.")
        return False
    
    try:
        # Connect to the database
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            dbname=db_name,
            user=db_user,
            password=db_password
        )
        
        # Create a cursor
        cursor = conn.cursor()
        
        # Test query - check if tables exist
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        
        print("✅ Database connection successful!")
        print("\nDatabase tables:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Check if cost_data table exists and has records
        if any('cost_data' in table[0] for table in tables):
            cursor.execute("SELECT COUNT(*) FROM cost_data;")
            count = cursor.fetchone()[0]
            print(f"\nCost data records: {count}")
            
            if count > 0:
                cursor.execute("SELECT * FROM cost_data LIMIT 5;")
                records = cursor.fetchall()
                print("\nSample cost data records:")
                for record in records:
                    print(f"  - {record}")
        
        # Close connection
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error connecting to database: {str(e)}")
        return False

if __name__ == "__main__":
    test_database_connection()
