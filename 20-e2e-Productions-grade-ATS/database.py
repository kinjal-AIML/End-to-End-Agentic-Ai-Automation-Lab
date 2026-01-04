from sqlmodel import SQLModel, Session, create_engine
from urllib.parse import quote_plus
import os
from dotenv import load_dotenv
load_dotenv()

# --- DATABASE CONFIGURATION ---
# NOTE: In a strictly production environment, these should come from os.getenv()
# But for your R&D setup, we define them here as requested.

DB_USER = "postgres"
DB_PASSWORD = os.getenv("DB_PASSWORD")  # Contains special chars (@, !)
DB_HOST = os.getenv("DB_HOST")
DB_PORT = "5432"
ATS_DB_NAME = os.getenv("ATS_DB_NAME")

# --- URL ENCODING (CRITICAL) ---
# We must encode the password because it contains '@'. 
# Without this, the system thinks the password ends at 'Tr' and tries to connect to host 'de'.
encoded_password = quote_plus(DB_PASSWORD)

# Construct the PostgreSQL Connection String
DATABASE_URL = f"postgresql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{ATS_DB_NAME}"

# --- ENGINE CREATION ---
# pool_pre_ping=True: Checks if the DB connection is alive before using it (Prevents "Server has gone away" errors)
# echo=True: Logs all SQL queries to the console (Useful for R&D debugging)
engine = create_engine(DATABASE_URL, echo=True, pool_pre_ping=True)

def create_db_and_tables():
    """
    Creates tables if they don't exist.
    """
    SQLModel.metadata.create_all(engine)

def get_session():
    """
    Dependency generator for FastAPI routes.
    Ensures the DB session opens and closes correctly for every request.
    """
    with Session(engine) as session:
        yield session

# --- CONNECTION TEST (Optional) ---
if __name__ == "__main__":
    try:
        # Tries to connect to the DB
        with Session(engine) as session:
            print(f"✅ Successfully connected to database: {ATS_DB_NAME} at {DB_HOST}")
    except Exception as e:
        print(f"❌ Connection Failed: {e}")