import unittest
import os
import re

class TestPostgreSQLSchemaSQL(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        schema_path = os.path.join(os.path.dirname(__file__), "..", "database", "schema.sql")
        cls.assertTrue(os.path.exists(schema_path), f"Schema file not found at {schema_path}")
        with open(schema_path, "r", encoding="utf-8") as f:
            cls.schema_content = f.read()

    def test_schema_file_exists(self):
        self.assertGreater(len(self.schema_content), 100)

    def test_all_tables_declared(self):
        expected_tables = [
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
        ]
        for table in expected_tables:
            pattern = re.compile(rf"CREATE\s+TABLE\s+(IF\s+NOT\s+EXISTS\s+)?{table}\b", re.IGNORECASE)
            self.assertTrue(pattern.search(self.schema_content), f"Table '{table}' creation statement missing in schema.sql")

    def test_primary_keys_declared(self):
        matches = re.findall(r"GENERATED\s+ALWAYS\s+AS\s+IDENTITY\s+PRIMARY\s+KEY", self.schema_content, re.IGNORECASE)
        self.assertEqual(len(matches), 10, f"Expected 10 identity primary keys, found {len(matches)}")

    def test_partial_unique_index_active_salary_structure(self):
        self.assertIn("uq_salary_structure_active", self.schema_content)
        self.assertIn("WHERE effective_to IS NULL", self.schema_content)

    def test_check_constraints_present(self):
        self.assertIn("CHECK (role IN ('Employee', 'HR'))", self.schema_content)
        self.assertIn("CHECK (check_out IS NULL OR check_in IS NULL OR check_out > check_in)", self.schema_content)
        self.assertIn("CHECK (start_date <= end_date)", self.schema_content)
        self.assertIn("CHECK (basic_salary >= 0)", self.schema_content)
        self.assertIn("CHECK (month BETWEEN 1 AND 12)", self.schema_content)

    def test_timestamp_trigger_function_declared(self):
        self.assertIn("CREATE OR REPLACE FUNCTION update_updated_at_column", self.schema_content)


if __name__ == "__main__":
    unittest.main()
