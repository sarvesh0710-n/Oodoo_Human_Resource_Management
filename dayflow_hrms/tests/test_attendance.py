from datetime import datetime, date
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError, AccessError


class TestAttendanceBusinessLogic(TransactionCase):

    def setUp(self):
        super(TestAttendanceBusinessLogic, self).setUp()
        self.group_employee = self.env.ref('dayflow_hrms.group_dayflow_employee')
        self.group_hr_officer = self.env.ref('dayflow_hrms.group_dayflow_hr_officer')

        self.user_emp1 = self.env['res.users'].create({
            'name': 'Emp One',
            'login': 'att_emp1@dayflow.com',
            'groups_id': [(6, 0, [self.group_employee.id])],
        })
        self.user_emp2 = self.env['res.users'].create({
            'name': 'Emp Two',
            'login': 'att_emp2@dayflow.com',
            'groups_id': [(6, 0, [self.group_employee.id])],
        })
        self.user_hr = self.env['res.users'].create({
            'name': 'HR Officer Att',
            'login': 'att_hr@dayflow.com',
            'groups_id': [(6, 0, [self.group_hr_officer.id])],
        })

        self.employee1 = self.env['hr.employee'].create({
            'name': 'Emp One',
            'user_id': self.user_emp1.id,
        })
        self.employee2 = self.env['hr.employee'].create({
            'name': 'Emp Two',
            'user_id': self.user_emp2.id,
        })

    def test_att_01_second_active_checkin_rejected(self):
        self.env['hr.attendance'].create({
            'employee_id': self.employee1.id,
            'check_in': datetime(2026, 1, 1, 9, 0, 0),
        })
        with self.assertRaises(ValidationError):
            self.env['hr.attendance'].create({
                'employee_id': self.employee1.id,
                'check_in': datetime(2026, 1, 1, 10, 0, 0),
            })

    def test_att_02_valid_checkout_succeeds(self):
        att = self.env['hr.attendance'].create({
            'employee_id': self.employee1.id,
            'check_in': datetime(2026, 1, 1, 9, 0, 0),
        })
        att.write({'check_out': datetime(2026, 1, 1, 17, 0, 0)})
        self.assertEqual(att.check_out, datetime(2026, 1, 1, 17, 0, 0))

    def test_att_03_04_checkout_earlier_than_checkin_rejected(self):
        with self.assertRaises(ValidationError):
            self.env['hr.attendance'].create({
                'employee_id': self.employee1.id,
                'check_in': datetime(2026, 1, 1, 17, 0, 0),
                'check_out': datetime(2026, 1, 1, 9, 0, 0),
            })

    def test_att_05_employee_cannot_create_for_another(self):
        att_env = self.env['hr.attendance'].with_user(self.user_emp1)
        with self.assertRaises(AccessError):
            att_env.create({
                'employee_id': self.employee2.id,
                'check_in': datetime(2026, 1, 1, 9, 0, 0),
            })

    def test_att_06_employee_access_own_only(self):
        att1 = self.env['hr.attendance'].create({
            'employee_id': self.employee1.id,
            'check_in': datetime(2026, 1, 1, 9, 0, 0),
        })
        att2 = self.env['hr.attendance'].create({
            'employee_id': self.employee2.id,
            'check_in': datetime(2026, 1, 1, 9, 0, 0),
        })
        att_env = self.env['hr.attendance'].with_user(self.user_emp1)
        self.assertTrue(att_env.browse(att1.id).exists())
        self.assertFalse(att_env.browse(att2.id).exists())

    def test_att_08_hr_officer_can_manage_all(self):
        hr_att_env = self.env['hr.attendance'].with_user(self.user_hr)
        att = hr_att_env.create({
            'employee_id': self.employee1.id,
            'check_in': datetime(2026, 1, 1, 9, 0, 0),
            'check_out': datetime(2026, 1, 1, 17, 0, 0),
        })
        self.assertTrue(att.id)
