from datetime import date, datetime
from odoo.tests.common import TransactionCase
from odoo.exceptions import AccessError, UserError


class TestSecurity(TransactionCase):

    def setUp(self):
        super(TestSecurity, self).setUp()

        self.group_employee = self.env.ref('dayflow_hrms.group_dayflow_employee')
        self.group_hr_officer = self.env.ref('dayflow_hrms.group_dayflow_hr_officer')

        # Users
        self.user_emp1 = self.env['res.users'].create({
            'name': 'Employee One',
            'login': 'emp1@dayflow.com',
            'groups_id': [(6, 0, [self.group_employee.id])],
        })
        self.user_emp2 = self.env['res.users'].create({
            'name': 'Employee Two',
            'login': 'emp2@dayflow.com',
            'groups_id': [(6, 0, [self.group_employee.id])],
        })
        self.user_hr = self.env['res.users'].create({
            'name': 'HR Officer',
            'login': 'hr@dayflow.com',
            'groups_id': [(6, 0, [self.group_hr_officer.id])],
        })

        # HR Employees
        self.employee1 = self.env['hr.employee'].create({
            'name': 'Employee One',
            'user_id': self.user_emp1.id,
        })
        self.employee2 = self.env['hr.employee'].create({
            'name': 'Employee Two',
            'user_id': self.user_emp2.id,
        })

        # Attendances
        self.att1 = self.env['hr.attendance'].create({
            'employee_id': self.employee1.id,
            'check_in': datetime(2026, 1, 1, 9, 0, 0),
        })
        self.att2 = self.env['hr.attendance'].create({
            'employee_id': self.employee2.id,
            'check_in': datetime(2026, 1, 1, 9, 0, 0),
        })

        # Leave Types & Leaves
        self.leave_type = self.env['hr.leave.type'].create({
            'name': 'Paid Leave',
            'requires_allocation': 'no',
        })
        self.leave1 = self.env['hr.leave'].create({
            'name': 'Vacation Emp 1',
            'employee_id': self.employee1.id,
            'holiday_status_id': self.leave_type.id,
            'request_date_from': date(2026, 5, 1),
            'request_date_to': date(2026, 5, 2),
        })
        self.leave2 = self.env['hr.leave'].create({
            'name': 'Vacation Emp 2',
            'employee_id': self.employee2.id,
            'holiday_status_id': self.leave_type.id,
            'request_date_from': date(2026, 5, 1),
            'request_date_to': date(2026, 5, 2),
        })

        # Salary Structures
        self.salary_struct1 = self.env['hrms.salary.structure'].create({
            'employee_id': self.employee1.id,
            'basic_salary': 5000.0,
            'effective_from': date(2026, 1, 1),
        })
        self.salary_struct2 = self.env['hrms.salary.structure'].create({
            'employee_id': self.employee2.id,
            'basic_salary': 6000.0,
            'effective_from': date(2026, 1, 1),
        })

        # Payslips
        self.payslip1 = self.env['hrms.payslip'].create({
            'employee_id': self.employee1.id,
            'salary_structure_id': self.salary_struct1.id,
            'month': 1,
            'year': 2026,
        })
        self.payslip2 = self.env['hrms.payslip'].create({
            'employee_id': self.employee2.id,
            'salary_structure_id': self.salary_struct2.id,
            'month': 1,
            'year': 2026,
        })

    # --- EMPLOYEE ISOLATION TESTS ---

    def test_sec_01_02_employee_profile_isolation(self):
        emp_env = self.env['hr.employee'].with_user(self.user_emp1)
        self.assertTrue(emp_env.browse(self.employee1.id).exists())
        self.assertFalse(emp_env.browse(self.employee2.id).exists())
        self.assertEqual(emp_env.search([]), self.employee1)

    def test_sec_03_04_employee_attendance_isolation(self):
        att_env = self.env['hr.attendance'].with_user(self.user_emp1)
        self.assertTrue(att_env.browse(self.att1.id).exists())
        self.assertFalse(att_env.browse(self.att2.id).exists())
        self.assertEqual(att_env.search([]), self.att1)

    def test_sec_05_06_employee_leave_isolation(self):
        leave_env = self.env['hr.leave'].with_user(self.user_emp1)
        self.assertTrue(leave_env.browse(self.leave1.id).exists())
        self.assertFalse(leave_env.browse(self.leave2.id).exists())
        self.assertEqual(leave_env.search([]), self.leave1)

    def test_sec_07_employee_salary_structure_no_access(self):
        struct_env = self.env['hrms.salary.structure'].with_user(self.user_emp1)
        with self.assertRaises(AccessError):
            struct_env.search([])
        with self.assertRaises(AccessError):
            struct_env.browse(self.salary_struct1.id).read(['basic_salary'])

    def test_sec_08_09_employee_payslip_isolation(self):
        payslip_env = self.env['hrms.payslip'].with_user(self.user_emp1)
        self.assertTrue(payslip_env.browse(self.payslip1.id).exists())
        self.assertFalse(payslip_env.browse(self.payslip2.id).exists())
        self.assertEqual(payslip_env.search([]), self.payslip1)

    def test_sec_10_employee_cannot_modify_delete_payslip(self):
        payslip_env = self.env['hrms.payslip'].with_user(self.user_emp1)
        own_payslip = payslip_env.browse(self.payslip1.id)
        with self.assertRaises((AccessError, UserError)):
            own_payslip.write({'basic_salary': 9000.0})
        with self.assertRaises((AccessError, UserError)):
            own_payslip.unlink()

    # --- HR OFFICER FULL ACCESS TESTS ---

    def test_sec_11_hr_officer_employee_full_access(self):
        hr_emp_env = self.env['hr.employee'].with_user(self.user_hr)
        self.assertTrue(hr_emp_env.browse(self.employee1.id).exists())
        self.assertTrue(hr_emp_env.browse(self.employee2.id).exists())
        self.assertEqual(set(hr_emp_env.search([])), {self.employee1, self.employee2})

    def test_sec_12_hr_officer_attendance_full_access(self):
        hr_att_env = self.env['hr.attendance'].with_user(self.user_hr)
        self.assertTrue(hr_att_env.browse(self.att1.id).exists())
        self.assertTrue(hr_att_env.browse(self.att2.id).exists())
        self.assertEqual(set(hr_att_env.search([])), {self.att1, self.att2})

    def test_sec_13_hr_officer_leave_full_access(self):
        hr_leave_env = self.env['hr.leave'].with_user(self.user_hr)
        self.assertTrue(hr_leave_env.browse(self.leave1.id).exists())
        self.assertTrue(hr_leave_env.browse(self.leave2.id).exists())
        self.assertEqual(set(hr_leave_env.search([])), {self.leave1, self.leave2})

    def test_sec_14_hr_officer_salary_structure_full_access(self):
        hr_struct_env = self.env['hrms.salary.structure'].with_user(self.user_hr)
        self.assertTrue(hr_struct_env.browse(self.salary_struct1.id).exists())
        self.assertTrue(hr_struct_env.browse(self.salary_struct2.id).exists())
        self.assertEqual(set(hr_struct_env.search([])), {self.salary_struct1, self.salary_struct2})

    def test_sec_15_hr_officer_payslip_full_access(self):
        hr_payslip_env = self.env['hrms.payslip'].with_user(self.user_hr)
        self.assertTrue(hr_payslip_env.browse(self.payslip1.id).exists())
        self.assertTrue(hr_payslip_env.browse(self.payslip2.id).exists())
        self.assertEqual(set(hr_payslip_env.search([])), {self.payslip1, self.payslip2})
