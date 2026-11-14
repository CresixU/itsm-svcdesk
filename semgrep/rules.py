# ai-generated: 85% - Claude Code wrote these cases with the author; each rule has lines it must report and lines it must not
import datetime
import sqlite3
from datetime import datetime as dt_class
from datetime import timezone

conn = sqlite3.connect(":memory:")
ticket_id = "t-1"
state = "open"


def reads_with_literal_sql():
    # ok: svcdesk-sql-execute-non-literal
    conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
    # ok: svcdesk-sql-execute-non-literal
    return conn.execute("UPDATE tickets SET state = ? WHERE id = ?", (state, ticket_id))


def reads_with_assembled_sql():
    query = "SELECT * FROM tickets WHERE 1 = 1"
    query += " AND state = ?"
    # ruleid: svcdesk-sql-execute-non-literal
    conn.execute(query, [state])


def reads_with_formatted_sql():
    # ruleid: svcdesk-sql-execute-non-literal
    conn.execute(f"SELECT * FROM tickets WHERE state = '{state}'")


def reads_with_concatenation():
    # ruleid: svcdesk-sql-execute-non-literal
    conn.execute("SELECT * FROM tickets WHERE id = " + ticket_id)


def reads_the_clock_directly():
    # ruleid: svcdesk-direct-wall-clock
    now = dt_class.now(timezone.utc)
    return now


def reads_the_clock_through_the_module():
    # ruleid: svcdesk-direct-wall-clock
    return datetime.datetime.utcnow()


def uses_a_given_instant(instant):
    # ok: svcdesk-direct-wall-clock
    return instant.replace(microsecond=0)


def builds_a_fixed_instant():
    # ok: svcdesk-direct-wall-clock
    return datetime.datetime(2026, 11, 14, 8, 0, tzinfo=timezone.utc)
