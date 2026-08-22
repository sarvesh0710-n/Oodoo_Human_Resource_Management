from datetime import date
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestSalaryStructure(TransactionCase):

    def setUp(self):
        super(TestSalaryStructure, self).setUp()
        self.employee = self.env['hr.employee'].create({
            'name': 'Test Employee',
        })

    def test_create_salary_structure(self):
        structure = self.env['hrms.salary.structure'].create({
            'employee_id': self.employee.id,
            'basic_salary': 5000.0,
            'allowances': 1000.0,
            'deductions': 500.0,
            'effective_from': date(2026, 1, 1),
        })
        self.assertTrue(structure.id)
        self.assertEqual(structure.basic_salary, 5000.0)
        self.assertFalse(structure.effective_to)

    def test_reject_negative_salary(self):
        with self.assertRaises(ValidationError):
            self.env['hrms.salary.structure'].create({
                'employee_id': self.employee.id,
                'basic_salary': -1000.0,
                'effective_from': date(2026, 1, 1),
            })

    def test_reject_invalid_date_range(self):
        with self.assertRaises(ValidationError):
            self.env['hrms.salary.structure'].create({
                'employee_id': self.employee.id,
                'basic_salary': 5000.0,
                'effective_from': date(2026, 6, 1),
                'effective_to': date(2026, 5, 1),
            })

    def test_new_active_salary_closes_previous(self):
        first_struct = self.env['hrms.salary.structure'].create({
            'employee_id': self.employee.id,
            'basic_salary': 5000.0,
            'effective_from': date(2026, 1, 1),
        })
        self.assertFalse(first_struct.effective_to)

        second_struct = self.env['hrms.salary.structure'].create({
            'employee_id': self.employee.id,
            'basic_salary': 6000.0,
            'effective_from': date(2026, 7, 1),
        })

        self.assertEqual(first_struct.effective_to, date(2026, 6, 30))
        self.assertFalse(second_struct.effective_to)

        active_count = self.env['hrms.salary.structure'].search_count([
            ('employee_id', '=', self.employee.id),
            ('effective_to', '=', False),
        ])
        self.assertEqual(active_count, 1)
