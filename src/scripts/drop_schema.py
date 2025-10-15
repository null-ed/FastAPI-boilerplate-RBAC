from sqlalchemy import create_engine, text
from app.core.config import settings


def main() -> None:
    engine = create_engine(settings.POSTGRES_SYNC_PREFIX + settings.POSTGRES_URI)
    with engine.connect() as conn:
        conn.execute(text('DROP SCHEMA IF EXISTS public CASCADE;'))
        conn.execute(text('CREATE SCHEMA public;'))
        conn.commit()
    print('Dropped and recreated schema public')


if __name__ == "__main__":
    main()