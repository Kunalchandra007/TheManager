"""Apply tracked PostgreSQL migrations through the Aurora RDS Data API.

The runner is safe to invoke again: applied files are recorded by SHA-256 checksum,
and any changed historical migration is rejected instead of silently re-applied.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from typing import Iterator

import boto3


MIGRATIONS = Path(__file__).resolve().parents[1] / "migrations" / "postgres"


def split_sql(source: str) -> Iterator[str]:
    """Split the repository's statement-only SQL, preserving quoted semicolons."""
    statement: list[str] = []
    quoted = False

    for character in source:
        if character == "'":
            quoted = not quoted

        if character == ";" and not quoted:
            sql = "".join(statement).strip()
            if sql:
                yield sql
            statement = []
        else:
            statement.append(character)

    sql = "".join(statement).strip()
    if sql:
        yield sql


def scalar(record: list[dict]) -> str | None:
    if not record:
        return None

    value = record[0]
    return (
        value.get("stringValue") or str(value.get("longValue"))
        if value
        else None
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resource-arn", required=True)
    parser.add_argument("--secret-arn", required=True)
    parser.add_argument("--region", default="ap-south-1")
    parser.add_argument("--database", default="themanager")
    parser.add_argument("--profile", help="Optional named AWS SSO profile")
    arguments = parser.parse_args()

    session = boto3.Session(
        profile_name=arguments.profile,
        region_name=arguments.region,
    )
    client = session.client("rds-data")

    # Parameters accepted by begin/commit/rollback_transaction.
    base = {
        "resourceArn": arguments.resource_arn,
        "secretArn": arguments.secret_arn,
    }

    # Parameters accepted by execute_statement.
    sql_base = {
        **base,
        "database": arguments.database,
    }

    client.execute_statement(
        **sql_base,
        sql=(
            "CREATE TABLE IF NOT EXISTS schema_migrations "
            "(filename TEXT PRIMARY KEY, "
            "checksum TEXT NOT NULL, "
            "applied_at TIMESTAMPTZ NOT NULL DEFAULT now())"
        ),
    )

    for path in sorted(MIGRATIONS.glob("*.sql")):
        source = path.read_text(encoding="utf-8")
        checksum = hashlib.sha256(source.encode("utf-8")).hexdigest()

        existing = client.execute_statement(
            **sql_base,
            sql=(
                "SELECT checksum FROM schema_migrations "
                "WHERE filename = :filename"
            ),
            parameters=[
                {
                    "name": "filename",
                    "value": {"stringValue": path.name},
                }
            ],
        ).get("records", [])

        if existing:
            if scalar(existing[0]) != checksum:
                raise RuntimeError(
                    f"Migration checksum changed after application: {path.name}"
                )

            print(f"SKIP {path.name} (already applied)")
            continue

        transaction = client.begin_transaction(**sql_base)["transactionId"]

        try:
            for statement in split_sql(source):
                client.execute_statement(
                    **sql_base,
                    transactionId=transaction,
                    sql=statement,
                )

            client.execute_statement(
                **sql_base,
                transactionId=transaction,
                sql=(
                    "INSERT INTO schema_migrations "
                    "(filename, checksum) "
                    "VALUES (:filename, :checksum)"
                ),
                parameters=[
                    {
                        "name": "filename",
                        "value": {"stringValue": path.name},
                    },
                    {
                        "name": "checksum",
                        "value": {"stringValue": checksum},
                    },
                ],
            )

            client.commit_transaction(
                **base,
                transactionId=transaction,
            )

            print(f"APPLIED {path.name}")

        except Exception:
            client.rollback_transaction(
                **base,
                transactionId=transaction,
            )
            raise


if __name__ == "__main__":
    main()