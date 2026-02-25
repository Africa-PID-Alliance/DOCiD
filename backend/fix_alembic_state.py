"""
One-time script to fix Alembic migration state on production.

Production DB was created via db.create_all() and has a stale
alembic_version stamp (854dc1b37b89) that doesn't match any
migration file. This script:
  1. Creates the account_types table if missing
  2. Seeds Individual/Institutional account types
  3. Adds account_type_id column to user_accounts if missing
  4. Stamps alembic_version to current migration head (30fd2740d9c1)

Safe to run multiple times (all operations are idempotent).
"""
import os
import sys

def get_database_url():
    database_url = os.environ.get("DATABASE_URL", "")
    if database_url:
        return database_url
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path) as env_file:
            for line in env_file:
                stripped = line.strip()
                if stripped.startswith("DATABASE_URL"):
                    return stripped.split("=", 1)[1].strip().strip('"').strip("'")
    return ""

def main():
    try:
        import psycopg2
    except ImportError:
        print("ERROR: psycopg2 not installed")
        sys.exit(1)

    database_url = get_database_url()
    if not database_url:
        print("ERROR: Could not find DATABASE_URL")
        sys.exit(1)

    connection = psycopg2.connect(database_url)
    connection.autocommit = True
    cursor = connection.cursor()

    # 1. Create account_types table if missing
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS account_types (
            id SERIAL PRIMARY KEY,
            account_type_name VARCHAR(50) NOT NULL UNIQUE
        )
    """)
    print("account_types table: OK")

    # 2. Seed account types
    cursor.execute("""
        INSERT INTO account_types (id, account_type_name)
        VALUES (1, 'Individual'), (2, 'Institutional')
        ON CONFLICT DO NOTHING
    """)
    print("account_types seed data: OK")

    # 3. Add account_type_id column to user_accounts if missing
    cursor.execute("""
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'user_accounts' AND column_name = 'account_type_id'
    """)
    if cursor.fetchone() is None:
        cursor.execute("""
            ALTER TABLE user_accounts
            ADD COLUMN account_type_id INTEGER REFERENCES account_types(id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS ix_user_accounts_account_type_id
            ON user_accounts(account_type_id)
        """)
        print("account_type_id column: ADDED")
    else:
        print("account_type_id column: already exists")

    # 4. Add Cordra columns to publications if missing
    cordra_columns = {
        "cordra_status": "VARCHAR(20) NOT NULL DEFAULT 'PENDING'",
        "cordra_error": "TEXT",
        "cordra_object_id": "VARCHAR(128)",
    }
    for column_name, column_definition in cordra_columns.items():
        cursor.execute("""
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'publications' AND column_name = %s
        """, (column_name,))
        if cursor.fetchone() is None:
            cursor.execute(
                f"ALTER TABLE publications ADD COLUMN {column_name} {column_definition}"
            )
            print(f"publications.{column_name}: ADDED")
        else:
            print(f"publications.{column_name}: already exists")

    # Create indexes for cordra columns if missing
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS ix_publications_cordra_status
        ON publications(cordra_status)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS ix_publications_cordra_object_id
        ON publications(cordra_object_id)
    """)
    print("Cordra indexes: OK")

    # 5. Stamp alembic_version to current head
    cursor.execute("SELECT version_num FROM alembic_version LIMIT 1")
    current_version = cursor.fetchone()
    if current_version:
        current_version = current_version[0]
        print(f"Current alembic version: {current_version}")
        if current_version != "30fd2740d9c1":
            cursor.execute("""
                UPDATE alembic_version SET version_num = '30fd2740d9c1'
            """)
            print("alembic_version stamped to: 30fd2740d9c1")
        else:
            print("alembic_version: already at head")
    else:
        cursor.execute("""
            INSERT INTO alembic_version (version_num) VALUES ('30fd2740d9c1')
        """)
        print("alembic_version: inserted 30fd2740d9c1")

    cursor.close()
    connection.close()
    print("Schema fix completed successfully")

if __name__ == "__main__":
    main()
