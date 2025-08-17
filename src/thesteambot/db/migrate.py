import argparse
import asyncio
import importlib.resources
import re
import sys
from typing import Iterable, NamedTuple, Self

import asyncpg

from thesteambot.db.connection import connect

assert __package__ is not None
package = importlib.resources.files(__package__)


def main() -> None:
    asyncio.run(amain())


async def amain() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host")
    parser.add_argument("--port", type=int)
    parser.add_argument("--user")
    parser.add_argument("--password")
    parser.add_argument("--database")

    args = parser.parse_args()

    async with connect(
        host=args.host,
        port=args.port,
        user=args.user,
        password=args.password,
        database=args.database,
    ) as conn:
        await run_default_migrations(conn)
    print("Database is up to date! 🙂")


async def run_default_migrations(conn: asyncpg.Connection) -> None:
    migrations = MigrationFinder().discover()
    migrator = Migrator(conn)
    await migrator.run_migrations(migrations)


class Migration(NamedTuple):
    version: int
    sql: str


class Migrations(tuple[Migration, ...]):
    def after_version(self, version: int) -> Self:
        """Return a copy of self with only migrations after the given version."""
        return type(self)(m for m in self if m.version > version)

    def version_exists(self, version: int) -> bool:
        return any(m.version == version for m in self)

    @classmethod
    def from_iterable_unsorted(cls, it: Iterable[Migration]) -> Self:
        return cls(sorted(it, key=lambda m: m.version))


class MigrationFinder:
    _FILE_PATTERN = re.compile(r"(\d+)-(.+)\.sql")

    def discover(self) -> Migrations:
        migrations: list[Migration] = [Migration(version=-1, sql="")]

        assert __package__ is not None
        path = importlib.resources.files(__package__).joinpath("migrations/")

        for file in path.iterdir():
            if not file.is_file():
                continue

            m = self._FILE_PATTERN.fullmatch(file.name)
            if m is None:
                continue

            version = int(m[1])
            sql = file.read_text("utf-8")
            migrations.append(Migration(version=version, sql=sql))

        return Migrations.from_iterable_unsorted(migrations)


class Migrator:
    def __init__(self, conn: asyncpg.Connection) -> None:
        self.conn = conn

    async def run_migrations(self, migrations: Migrations) -> None:
        version = await self.get_version()
        if version > 0 and not migrations.version_exists(version):
            sys.exit(f"Unrecognized database version: {version}")
            return

        async with self.conn.transaction():
            for version, script in migrations.after_version(version):
                print(f"Migrating database to v{version}")
                await self.conn.execute(script)

            await self.conn.execute("UPDATE schema_version SET version = $1", version)

    async def get_version(self) -> int:
        try:
            version = await self.conn.fetchval("SELECT version FROM schema_version")
        except asyncpg.UndefinedTableError:
            await self.conn.execute(
                "CREATE TABLE schema_version (version INTEGER NOT NULL)"
            )
            version = await self.conn.fetchval(
                "INSERT INTO schema_version VALUES (0) RETURNING version"
            )

        assert isinstance(version, int)
        return version


if __name__ == "__main__":
    main()
