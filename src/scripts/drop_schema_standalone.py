import os
from sqlalchemy import create_engine, text


def get_pg_uri() -> str:
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "postgres")
    host = os.getenv("POSTGRES_SERVER", "localhost")
    port = int(os.getenv("POSTGRES_PORT", "5432"))
    db = os.getenv("POSTGRES_DB", "postgres")
    prefix = os.getenv("POSTGRES_SYNC_PREFIX", "postgresql://")
    return f"{prefix}{user}:{password}@{host}:{port}/{db}"


def main() -> None:
    uri = get_pg_uri()
    engine = create_engine(uri)
    with engine.connect() as conn:
        conn.execute(text('DROP SCHEMA IF EXISTS public CASCADE;'))
        conn.execute(text('CREATE SCHEMA public;'))
        conn.commit()
    print('Dropped and recreated schema public')


if __name__ == "__main__":
    main()