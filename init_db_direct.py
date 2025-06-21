"""
Initialize the PostgreSQL database with schema and tables directly.
"""
import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def init_database():
    print("Initializing PostgreSQL database...")
    
    # Get database credentials
    db_host = os.getenv("POSTGRES_HOST", "localhost")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB", "finops")
    db_user = os.getenv("POSTGRES_USER", "postgres")
    db_password = os.getenv("POSTGRES_PASSWORD", "pgadmin777")
    
    try:
        # Connect to the database
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            dbname=db_name,
            user=db_user,
            password=db_password
        )
        
        # Set autocommit
        conn.autocommit = True
        
        # Create a cursor
        cursor = conn.cursor()
        
        # Read and execute the init.sql file
        with open('database/init.sql', 'r') as sql_file:
            sql_script = sql_file.read()
            
        print("Executing database initialization script...")
        cursor.execute(sql_script)
        
        print("✅ Database initialized successfully!")
        
        # Close connection
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error initializing database: {str(e)}")
        return False

if __name__ == "__main__":
    init_database()
