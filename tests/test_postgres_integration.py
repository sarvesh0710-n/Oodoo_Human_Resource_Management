"""
tests/test_postgres_integration.py
===================================
Live PostgreSQL integration tests for Dayflow HRMS.

These tests execute `database/schema.sql` against a real PostgreSQL instance
and verify that all constraints, triggers, unique indexes, and foreign keys
behave exactly as specified in the Dayflow HRMS SRS.

Connection Strategy
-------------------
1. Reads ``TEST_DATABASE_URL`` or ``DATABASE_URL`` environment variable.
2. Falls back to a local socket connection on ports 5432 / 5433.
3. If no server is reachable, attempts to bootstrap an ephemeral PostgreSQL
   process using the system ``initdb`` / ``postgres`` binaries.
4. If none of the above succeeds the entire test class is skipped with a
   clear ``POSTGRESQL SERVER UNAVAILABLE`` message.

Isolation
---------
Each test method:
  - Drops the ``public`` schema.
  - Recreates it from a clean state.
  - Executes ``database/schema.sql`` in full.
  - Runs its assertions.
  - Rolls back / cleans up via tearDown.

This guarantees every test starts from an identical, empty database.

Running
-------
    pytest -v tests/test_postgres_integration.py

    # Override connection:
    TEST_DATABASE_URL="postgresql://user:pass@host/db" pytest -v tests/test_postgres_integration.py
"""

import os
import shutil
import subprocess
import tempfile
import time
import unittest

import psycopg2


# ---------------------------------------------------------------------------
# Helper: Connect to PostgreSQL or bootstrap an ephemeral instance
# ---------------------------------------------------------------------------

def _resolve_pg_connection() -> str | None:
    """
    Return a psycopg2 connection string or None if PostgreSQL is unavailable.

    Priority:
      1. ``TEST_DATABASE_URL`` env var
      2. ``DATABASE_URL`` env var
      3. Local Unix socket on port 5432 or 5433
    """
    for env_key in ("TEST_DATABASE_URL", "DATABASE_URL"):
        url = os.getenv(env_key)
        if url:
            try:
                conn = psycopg2.connect(url)
                conn.close()
                return url
            except Exception:
                pass

    for port in (5432, 5433):
        try:
            conn = psycopg2.connect(host="/tmp", port=port, dbname="postgres")
            conn.close()
            return f"host=/tmp port={port} dbname=postgres"
        except Exception:
            pass

    return None


def _start_ephemeral_postgres() -> tuple[subprocess.Popen | None, str | None, str | None]:
    """
    Try to initialise and start an ephemeral PostgreSQL process.

    Returns (process, tmp_data_dir, conn_string) or (None, None, None).
    """
    initdb = "/usr/lib/postgresql/17/bin/initdb"
    postgres_bin = "/usr/lib/postgresql/17/bin/postgres"

    if not (os.path.exists(initdb) and os.path.exists(postgres_bin)):
        return None, None, None

    tmp_dir = tempfile.mkdtemp(prefix="dayflow_pgtest_")
    subprocess.run(
        [initdb, "-D", tmp_dir],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    process = subprocess.Popen(
        [postgres_bin, "-D", tmp_dir, "-k", "/tmp", "-p", "5433"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    conn_str = None
    for _ in range(50):
        try:
            conn = psycopg2.connect(host="/tmp", port=5433, dbname="postgres")
            conn.close()
            conn_str = "host=/tmp port=5433 dbname=postgres"
            break
        except Exception:
            time.sleep(0.2)

    if conn_str is None:
        process.terminate()
        process.wait()
        shutil.rmtree(tmp_dir, ignore_errors=True)
        return None, None, None

    return process, tmp_dir, conn_str


# ---------------------------------------------------------------------------
# Test Suite
# ---------------------------------------------------------------------------

class TestPostgreSQLIntegration(unittest.TestCase):
    """
    Live integration tests against a real PostgreSQL instance.

    All 14 tests map directly to the requirements stated in the Dayflow HRMS
    SRS and the ``database/schema.sql`` specification.
    """

    _pg_process: subprocess.Popen | None = None
    _tmp_pgdir: str | None = None
    conn_str: str | None = None

    # ------------------------------------------------------------------
    # Class-level setup / teardown (one PostgreSQL server for all tests)
    # ------------------------------------------------------------------

    @classmethod
    def setUpClass(cls) -> None:
        cls.conn_str = _resolve_pg_connection()

        if cls.conn_str is None:
            cls._pg_process, cls._tmp_pgdir, cls.conn_str = _start_ephemeral_postgres()

        if cls.conn_str is None:
            raise unittest.SkipTest(
                "POSTGRESQL SERVER UNAVAILABLE.\n"
                "Set TEST_DATABASE_URL or ensure a PostgreSQL server is running "
                "on localhost:5432 / localhost:5433."
            )

        schema_path = os.path.join(
            os.path.dirname(__file__), "..", "database", "schema.sql"
        )
        if not os.path.exists(schema_path):
            raise FileNotFoundError(
                f"database/schema.sql not found at expected path: {schema_path}"
            )

        with open(schema_path, "r", encoding="utf-8") as fh:
            cls.schema_sql = fh.read()

    @classmethod
    def tearDownClass(cls) -> None:
        if cls._pg_process:
            cls._pg_process.terminate()
            cls._pg_process.wait()
        if cls._tmp_pgdir and os.path.exists(cls._tmp_pgdir):
            shutil.rmtree(cls._tmp_pgdir, ignore_errors=True)

    # ------------------------------------------------------------------
    # Per-test setup / teardown (clean schema per test)
    # ------------------------------------------------------------------

    def setUp(self) -> None:
        self.conn = psycopg2.connect(self.conn_str)
        self.conn.autocommit = True
        self.cur = self.conn.cursor()

        # Wipe and recreate the public schema for a clean slate
        self.cur.execute("DROP SCHEMA public CASCADE;")
        self.cur.execute("CREATE SCHEMA public;")
        self.cur.execute(self.schema_sql)

        self.conn.autocommit = False  # Use explicit transactions for assertions

    def tearDown(self) -> None:
        self.conn.rollback()
        self.cur.close()
        self.conn.close()

    # ------------------------------------------------------------------
    # Shared seed helpers
    # ------------------------------------------------------------------

    def _seed_user(self, code: str = "EMP001", email: str = "emp1@dayflow.com", role: str = "Employee") -> int:
        self.cur.execute(
            "INSERT INTO users (employee_code, email, password_hash, role) VALUES (%s, %s, 'hash', %s) RETURNING id;",
            (code, email, role),
        )
        return self.cur.fetchone()[0]

    def _seed_employee(self, user_id: int) -> int:
        self.cur.execute(
            "INSERT INTO employees (user_id, first_name, last_name, joining_date) VALUES (%s, 'John', 'Doe', '2026-01-01') RETURNING id;",
            (user_id,),
        )
        return self.cur.fetchone()[0]

    def _seed_salary_structure(self, employee_id: int, basic: float = 5000.0, effective_to: str | None = None) -> int:
        self.cur.execute(
            "INSERT INTO salary_structures (employee_id, basic_salary, effective_from, effective_to) VALUES (%s, %s, '2026-01-01', %s) RETURNING id;",
            (employee_id, basic, effective_to),
        )
        return self.cur.fetchone()[0]

    def _seed_leave_type(self, name: str = "Annual Leave") -> int:
        self.cur.execute(
            "INSERT INTO leave_types (name) VALUES (%s) RETURNING id;",
            (name,),
        )
        return self.cur.fetchone()[0]

    # ==================================================================
    # TEST 1 — Schema executes cleanly on an empty database
    # ==================================================================

    def test_01_schema_executes_on_empty_database(self) -> None:
        """Verify that database/schema.sql executes without error from scratch."""
        # setUp already executed the schema. If we reach this point, it passed.
        self.conn.commit()

    # ==================================================================
    # TEST 2 — All 10 tables exist
    # ==================================================================

    def test_02_all_ten_tables_exist(self) -> None:
        """Verify that all 10 required tables are present after schema execution."""
        self.cur.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
            """
        )
        tables = {row[0] for row in self.cur.fetchall()}
        expected = {
            "users",
            "departments",
            "employees",
            "attendance",
            "leave_types",
            "leave_requests",
            "salary_structures",
            "payslips",
            "employee_documents",
            "audit_logs",
        }
        missing = expected - tables
        self.assertFalse(missing, f"Missing tables: {missing}")

    # ==================================================================
    # TEST 3 — Foreign keys are registered in pg_catalog
    # ==================================================================

    def test_03_foreign_keys_registered(self) -> None:
        """Verify that at least 10 foreign key constraints exist in pg_catalog."""
        self.cur.execute(
            """
            SELECT count(*)
            FROM information_schema.table_constraints
            WHERE constraint_type = 'FOREIGN KEY' AND table_schema = 'public';
            """
        )
        count = self.cur.fetchone()[0]
        self.assertGreaterEqual(count, 10, f"Expected >= 10 FK constraints, found {count}")

    # ==================================================================
    # TEST 4 — UNIQUE(users.email) and UNIQUE(users.employee_code)
    # ==================================================================

    def test_04_users_unique_email_and_employee_code(self) -> None:
        """Duplicate users.email and users.employee_code must both be rejected."""
        self._seed_user(code="EMP001", email="alice@dayflow.com")
        self.conn.commit()

        # Duplicate email
        with self.assertRaises(psycopg2.Error, msg="Duplicate email should be rejected"):
            self.cur.execute(
                "INSERT INTO users (employee_code, email, password_hash, role) VALUES ('EMP002', 'alice@dayflow.com', 'hash', 'Employee');"
            )
        self.conn.rollback()

        # Duplicate employee_code
        with self.assertRaises(psycopg2.Error, msg="Duplicate employee_code should be rejected"):
            self.cur.execute(
                "INSERT INTO users (employee_code, email, password_hash, role) VALUES ('EMP001', 'bob@dayflow.com', 'hash', 'Employee');"
            )
        self.conn.rollback()

    # ==================================================================
    # TEST 5 — UNIQUE(employees.user_id) — one employee per user account
    # ==================================================================

    def test_05_employees_unique_user_id(self) -> None:
        """A user_id must map to exactly one employee record."""
        u_id = self._seed_user()
        self._seed_employee(u_id)
        self.conn.commit()

        with self.assertRaises(psycopg2.Error, msg="Duplicate user_id on employees should be rejected"):
            self.cur.execute(
                "INSERT INTO employees (user_id, first_name, last_name, joining_date) VALUES (%s, 'Jane', 'Doe', '2026-01-01');",
                (u_id,),
            )
        self.conn.rollback()

    # ==================================================================
    # TEST 6 — UNIQUE(attendance.employee_id, attendance_date)
    # ==================================================================

    def test_06_attendance_unique_employee_date(self) -> None:
        """Only one attendance record is allowed per employee per calendar day."""
        u_id = self._seed_user()
        e_id = self._seed_employee(u_id)
        self.conn.commit()

        self.cur.execute(
            "INSERT INTO attendance (employee_id, attendance_date, check_in) VALUES (%s, '2026-08-22', '2026-08-22 09:00:00+00');",
            (e_id,),
        )
        self.conn.commit()

        with self.assertRaises(psycopg2.Error, msg="Second attendance record for same employee/date should be rejected"):
            self.cur.execute(
                "INSERT INTO attendance (employee_id, attendance_date, check_in) VALUES (%s, '2026-08-22', '2026-08-22 10:00:00+00');",
                (e_id,),
            )
        self.conn.rollback()

    # ==================================================================
    # TEST 7 — UNIQUE(payslips.employee_id, month, year)
    # ==================================================================

    def test_07_payslips_unique_employee_month_year(self) -> None:
        """Duplicate payslip for the same employee/month/year must be rejected."""
        u_id = self._seed_user()
        e_id = self._seed_employee(u_id)
        s_id = self._seed_salary_structure(e_id)
        self.conn.commit()

        self.cur.execute(
            "INSERT INTO payslips (employee_id, salary_structure_id, month, year, basic_salary, allowances, deductions, gross_salary, net_salary) VALUES (%s, %s, 8, 2026, 5000, 1000, 500, 6000, 5500);",
            (e_id, s_id),
        )
        self.conn.commit()

        with self.assertRaises(psycopg2.Error, msg="Duplicate payslip should be rejected"):
            self.cur.execute(
                "INSERT INTO payslips (employee_id, salary_structure_id, month, year, basic_salary, allowances, deductions, gross_salary, net_salary) VALUES (%s, %s, 8, 2026, 5000, 1000, 500, 6000, 5500);",
                (e_id, s_id),
            )
        self.conn.rollback()

    # ==================================================================
    # TEST 8 — Partial unique index: one active salary structure per employee
    # ==================================================================

    def test_08_partial_unique_index_active_salary_structure(self) -> None:
        """
        An employee may have at most one salary structure with effective_to IS NULL.
        A second active insert must fail on the partial unique index.
        A historical (closed) structure alongside an active one must succeed.
        """
        u_id = self._seed_user()
        e_id = self._seed_employee(u_id)
        # First active structure
        self._seed_salary_structure(e_id, basic=5000.0)
        self.conn.commit()

        # Second active structure — must fail
        with self.assertRaises(psycopg2.Error, msg="Second active salary structure should be rejected"):
            self._seed_salary_structure(e_id, basic=6000.0)
        self.conn.rollback()

        # Closed structure alongside the active one — must succeed.
        # effective_from must be before effective_to (check_effective_dates constraint).
        self.cur.execute(
            "INSERT INTO salary_structures (employee_id, basic_salary, effective_from, effective_to) VALUES (%s, %s, '2024-01-01', '2025-12-31') RETURNING id;",
            (e_id, 4000.0),
        )
        self.conn.commit()  # no error expected

    # ==================================================================
    # TEST 9 — Salary CHECK constraints (no negative amounts)
    # ==================================================================

    def test_09_salary_structure_no_negative_amounts(self) -> None:
        """basic_salary, allowances, and deductions must all be >= 0."""
        u_id = self._seed_user()
        e_id = self._seed_employee(u_id)
        self.conn.commit()

        # Negative basic_salary
        with self.assertRaises(psycopg2.Error):
            self.cur.execute(
                "INSERT INTO salary_structures (employee_id, basic_salary, effective_from) VALUES (%s, -100.00, '2026-01-01');",
                (e_id,),
            )
        self.conn.rollback()

        # Negative allowances
        with self.assertRaises(psycopg2.Error):
            self.cur.execute(
                "INSERT INTO salary_structures (employee_id, basic_salary, allowances, effective_from) VALUES (%s, 5000.00, -50.00, '2026-01-01');",
                (e_id,),
            )
        self.conn.rollback()

        # Negative deductions
        with self.assertRaises(psycopg2.Error):
            self.cur.execute(
                "INSERT INTO salary_structures (employee_id, basic_salary, deductions, effective_from) VALUES (%s, 5000.00, -50.00, '2026-01-01');",
                (e_id,),
            )
        self.conn.rollback()

    # ==================================================================
    # TEST 10 — Attendance: check_out must be after check_in
    # ==================================================================

    def test_10_attendance_checkout_must_be_after_checkin(self) -> None:
        """
        CHECK constraint check_checkout_after_checkin must reject
        any record where check_out <= check_in.
        """
        u_id = self._seed_user()
        e_id = self._seed_employee(u_id)
        self.conn.commit()

        # check_out earlier than check_in
        with self.assertRaises(psycopg2.Error, msg="check_out <= check_in should be rejected"):
            self.cur.execute(
                "INSERT INTO attendance (employee_id, attendance_date, check_in, check_out) VALUES (%s, '2026-08-22', '2026-08-22 17:00:00+00', '2026-08-22 09:00:00+00');",
                (e_id,),
            )
        self.conn.rollback()

        # check_out equal to check_in
        with self.assertRaises(psycopg2.Error, msg="check_out == check_in should be rejected"):
            self.cur.execute(
                "INSERT INTO attendance (employee_id, attendance_date, check_in, check_out) VALUES (%s, '2026-08-23', '2026-08-23 09:00:00+00', '2026-08-23 09:00:00+00');",
                (e_id,),
            )
        self.conn.rollback()

    # ==================================================================
    # TEST 11 — Leave requests: start_date must be <= end_date
    # ==================================================================

    def test_11_leave_request_date_range_constraint(self) -> None:
        """CHECK constraint check_leave_dates rejects start_date > end_date."""
        u_id = self._seed_user()
        e_id = self._seed_employee(u_id)
        lt_id = self._seed_leave_type()
        self.conn.commit()

        with self.assertRaises(psycopg2.Error, msg="start_date > end_date should be rejected"):
            self.cur.execute(
                "INSERT INTO leave_requests (employee_id, leave_type_id, start_date, end_date) VALUES (%s, %s, '2026-05-15', '2026-05-10');",
                (e_id, lt_id),
            )
        self.conn.rollback()

    # ==================================================================
    # TEST 12 — Payslip: month must be between 1 and 12
    # ==================================================================

    def test_12_payslip_month_range_constraint(self) -> None:
        """CHECK constraint on payslips.month rejects month = 0 and month = 13."""
        u_id = self._seed_user()
        e_id = self._seed_employee(u_id)
        s_id = self._seed_salary_structure(e_id)
        self.conn.commit()

        for invalid_month in (0, 13):
            with self.assertRaises(psycopg2.Error, msg=f"month={invalid_month} should be rejected"):
                self.cur.execute(
                    "INSERT INTO payslips (employee_id, salary_structure_id, month, year, basic_salary, allowances, deductions, gross_salary, net_salary) VALUES (%s, %s, %s, 2026, 5000, 1000, 500, 6000, 5500);",
                    (e_id, s_id, invalid_month),
                )
            self.conn.rollback()

    # ==================================================================
    # TEST 13 — users.role must be 'Employee' or 'HR'
    # ==================================================================

    def test_13_users_role_constraint(self) -> None:
        """CHECK constraint on users.role rejects any value outside ('Employee', 'HR')."""
        for invalid_role in ("Admin", "Manager", "admin_hr", "superuser", ""):
            with self.assertRaises(psycopg2.Error, msg=f"role='{invalid_role}' should be rejected"):
                self.cur.execute(
                    "INSERT INTO users (employee_code, email, password_hash, role) VALUES ('EMP999', 'x@dayflow.com', 'hash', %s);",
                    (invalid_role,),
                )
            self.conn.rollback()

    # ==================================================================
    # TEST 14 — updated_at trigger auto-updates on row modification
    # ==================================================================

    def test_14_updated_at_trigger_fires_on_update(self) -> None:
        """
        The plpgsql trigger must advance updated_at whenever any mutable
        table row is updated. Verified on the users table.
        """
        u_id = self._seed_user()
        self.cur.execute("SELECT updated_at FROM users WHERE id = %s;", (u_id,))
        t_before = self.cur.fetchone()[0]
        self.conn.commit()

        # Small sleep to ensure clock advances
        time.sleep(0.05)

        self.cur.execute("UPDATE users SET is_verified = TRUE WHERE id = %s;", (u_id,))
        self.cur.execute("SELECT updated_at FROM users WHERE id = %s;", (u_id,))
        t_after = self.cur.fetchone()[0]
        self.conn.commit()

        self.assertGreater(t_after, t_before, "updated_at should advance after UPDATE")

    # ==================================================================
    # TEST 15 — End-to-end CRUD: full workflow across all 10 tables
    # ==================================================================

    def test_15_crud_smoke_test_all_tables(self) -> None:
        """
        Insert one representative row into each of the 10 tables and verify
        the data can be read back. This smoke test exercises every FK chain
        in the schema, including the circular departments ↔ employees reference.
        """
        # users
        u_id = self._seed_user(code="EMP010", email="hr@dayflow.com", role="HR")
        e_u_id = self._seed_user(code="EMP011", email="emp@dayflow.com", role="Employee")

        # departments (manager_id is NULL initially — circular reference resolved after employee)
        self.cur.execute("INSERT INTO departments (name, description) VALUES ('Engineering', 'R&D') RETURNING id;")
        dept_id = self.cur.fetchone()[0]

        # employees
        e_id = self._seed_employee(e_u_id)

        # Resolve circular FK: set department manager
        self.cur.execute("UPDATE departments SET manager_id = %s WHERE id = %s;", (e_id, dept_id))

        # attendance
        self.cur.execute(
            "INSERT INTO attendance (employee_id, attendance_date, check_in, check_out) VALUES (%s, '2026-08-22', '2026-08-22 09:00:00+00', '2026-08-22 17:00:00+00') RETURNING id;",
            (e_id,),
        )
        att_id = self.cur.fetchone()[0]

        # leave_types
        lt_id = self._seed_leave_type(name="Paid Leave")

        # leave_requests
        self.cur.execute(
            "INSERT INTO leave_requests (employee_id, leave_type_id, start_date, end_date, status) VALUES (%s, %s, '2026-09-01', '2026-09-05', 'Pending') RETURNING id;",
            (e_id, lt_id),
        )
        lr_id = self.cur.fetchone()[0]

        # salary_structures
        s_id = self._seed_salary_structure(e_id, basic=6000.0)

        # payslips
        self.cur.execute(
            "INSERT INTO payslips (employee_id, salary_structure_id, month, year, basic_salary, allowances, deductions, gross_salary, net_salary) VALUES (%s, %s, 8, 2026, 6000, 1000, 500, 7000, 6500) RETURNING id;",
            (e_id, s_id),
        )
        ps_id = self.cur.fetchone()[0]

        # employee_documents
        self.cur.execute(
            "INSERT INTO employee_documents (employee_id, document_name, file_path, uploaded_by) VALUES (%s, 'Offer Letter', 'docs/offer_letter.pdf', %s) RETURNING id;",
            (e_id, u_id),
        )
        doc_id = self.cur.fetchone()[0]

        # audit_logs
        self.cur.execute(
            "INSERT INTO audit_logs (user_id, action, entity, entity_id, details) VALUES (%s, 'PAYSLIP_GENERATED', 'payslips', %s, '{\"month\": 8, \"year\": 2026}') RETURNING id;",
            (u_id, ps_id),
        )
        log_id = self.cur.fetchone()[0]

        self.conn.commit()

        # Verify each row was written
        for table, pk_id in [
            ("attendance", att_id),
            ("leave_requests", lr_id),
            ("salary_structures", s_id),
            ("payslips", ps_id),
            ("employee_documents", doc_id),
            ("audit_logs", log_id),
        ]:
            self.cur.execute(f"SELECT id FROM {table} WHERE id = %s;", (pk_id,))
            row = self.cur.fetchone()
            self.assertIsNotNone(row, f"Row not found in {table} with id={pk_id}")


if __name__ == "__main__":
    unittest.main()
