from datetime import date
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError, UserError
from odoo.tools import mute_logger


class TestPayslip(TransactionCase):

    def setUp(self):
        super(TestPayslip, self).setUp()
        self.employee = self.env['hr.employee'].create({
            'name': 'Test Employee',
        })
        self.salary_structure = self.env['hrms.salary.structure'].create({
            'employee_id': self.employee.id,
            'basic_salary': 5000.0,
            'allowances': 1000.0,
            'deductions': 500.0,
            'effective_from': date(2026, 1, 1),
        })

    def test_create_payslip_and_calculations(self):
        payslip = self.env['hrms.payslip'].create({
            'employee_id': self.employee.id,
            'salary_structure_id': self.salary_structure.id,
            'month': 1,
            'year': 2026,
        })
        self.assertEqual(payslip.basic_salary, 5000.0)
        self.assertEqual(payslip.allowances, 1000.0)
        self.assertEqual(payslip.deductions, 500.0)
        self.assertEqual(payslip.gross_salary, 6000.0)
        self.assertEqual(payslip.net_salary, 5500.0)

    def test_duplicate_payslip_rejected(self):
        self.env['hrms.payslip'].create({
            'employee_id': self.employee.id,
            'salary_structure_id': self.salary_structure.id,
            'month': 1,
            'year': 2026,
        })
        with mute_logger('odoo.sql_db'), self.assertRaises(Exception):
            self.env['hrms.payslip'].create({
                'employee_id': self.employee.id,
                'salary_structure_id': self.salary_structure.id,
                'month': 1,
                'year': 2026,
            })

    def test_month_validation(self):
        with self.assertRaises(ValidationError):
            self.env['hrms.payslip'].create({
                'employee_id': self.employee.id,
                'salary_structure_id': self.salary_structure.id,
                'month': 13,
                'year': 2026,
            })

    def test_payslip_snapshot_immutability_on_salary_change(self):
        payslip = self.env['hrms.payslip'].create({
            'employee_id': self.employee.id,
            'salary_structure_id': self.salary_structure.id,
            'month': 1,
            'year': 2026,
        })

        self.env['hrms.salary.structure'].create({
            'employee_id': self.employee.id,
            'basic_salary': 8000.0,
            'allowances': 2000.0,
            'deductions': 1000.0,
            'effective_from': date(2026, 2, 1),
        })

        self.assertEqual(payslip.basic_salary, 5000.0)
        self.assertEqual(payslip.gross_salary, 6000.0)
        self.assertEqual(payslip.net_salary, 5500.0)

    def test_payslip_modification_rejected(self):
        payslip = self.env['hrms.payslip'].create({
            'employee_id': self.employee.id,
            'salary_structure_id': self.salary_structure.id,
            'month': 1,
            'year': 2026,
        })
        with self.assertRaises(UserError):
            payslip.write({'basic_salary': 7000.0})

    def test_payslip_deletion_rejected(self):
        payslip = self.env['hrms.payslip'].create({
            'employee_id': self.employee.id,
            'salary_structure_id': self.salary_structure.id,
            'month': 1,
            'year': 2026,
        })
        with self.assertRaises(UserError):
            payslip.unlink()
