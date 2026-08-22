from datetime import date, datetime
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError, AccessError, UserError


class TestLeaveBusinessLogic(TransactionCase):

    def setUp(self):
        super(TestLeaveBusinessLogic, self).setUp()
        self.group_employee = self.env.ref('dayflow_hrms.group_dayflow_employee')
        self.group_hr_officer = self.env.ref('dayflow_hrms.group_dayflow_hr_officer')

        self.user_emp1 = self.env['res.users'].create({
            'name': 'Leave Emp One',
            'login': 'leave_emp1@dayflow.com',
            'groups_id': [(6, 0, [self.group_employee.id])],
        })
        self.user_emp2 = self.env['res.users'].create({
            'name': 'Leave Emp Two',
            'login': 'leave_emp2@dayflow.com',
            'groups_id': [(6, 0, [self.group_employee.id])],
        })
        self.user_hr = self.env['res.users'].create({
            'name': 'Leave HR Officer',
            'login': 'leave_hr@dayflow.com',
            'groups_id': [(6, 0, [self.group_hr_officer.id])],
        })

        self.employee1 = self.env['hr.employee'].create({
            'name': 'Leave Emp One',
            'user_id': self.user_emp1.id,
        })
        self.employee2 = self.env['hr.employee'].create({
            'name': 'Leave Emp Two',
            'user_id': self.user_emp2.id,
        })

        self.leave_type = self.env['hr.leave.type'].create({
            'name': 'Annual Leave',
            'requires_allocation': 'no',
        })

    def test_leave_01_invalid_date_range_rejected(self):
        with self.assertRaises(ValidationError):
            self.env['hr.leave'].create({
                'name': 'Invalid Dates',
                'employee_id': self.employee1.id,
                'holiday_status_id': self.leave_type.id,
                'request_date_from': date(2026, 5, 10),
                'request_date_to': date(2026, 5, 5),
                'date_from': datetime(2026, 5, 10, 0, 0, 0),
                'date_to': datetime(2026, 5, 5, 23, 59, 59),
            })

    def test_leave_02_03_overlapping_leave_rejected(self):
        self.env['hr.leave'].create({
            'name': 'Leave 1',
            'employee_id': self.employee1.id,
            'holiday_status_id': self.leave_type.id,
            'request_date_from': date(2026, 5, 10),
            'request_date_to': date(2026, 5, 12),
            'date_from': datetime(2026, 5, 10, 0, 0, 0),
            'date_to': datetime(2026, 5, 12, 23, 59, 59),
        })

        with self.assertRaises(ValidationError):
            self.env['hr.leave'].create({
                'name': 'Overlapping Leave',
                'employee_id': self.employee1.id,
                'holiday_status_id': self.leave_type.id,
                'request_date_from': date(2026, 5, 11),
                'request_date_to': date(2026, 5, 15),
                'date_from': datetime(2026, 5, 11, 0, 0, 0),
                'date_to': datetime(2026, 5, 15, 23, 59, 59),
            })

        # Non-overlapping leave for same employee succeeds
        non_overlap = self.env['hr.leave'].create({
            'name': 'Non-overlapping Leave',
            'employee_id': self.employee1.id,
            'holiday_status_id': self.leave_type.id,
            'request_date_from': date(2026, 5, 20),
            'request_date_to': date(2026, 5, 22),
            'date_from': datetime(2026, 5, 20, 0, 0, 0),
            'date_to': datetime(2026, 5, 22, 23, 59, 59),
        })
        self.assertTrue(non_overlap.id)

        # Overlapping leave for DIFFERENT employee succeeds
        diff_emp_leave = self.env['hr.leave'].create({
            'name': 'Emp 2 Overlap Date',
            'employee_id': self.employee2.id,
            'holiday_status_id': self.leave_type.id,
            'request_date_from': date(2026, 5, 11),
            'request_date_to': date(2026, 5, 15),
            'date_from': datetime(2026, 5, 11, 0, 0, 0),
            'date_to': datetime(2026, 5, 15, 23, 59, 59),
        })
        self.assertTrue(diff_emp_leave.id)

    def test_leave_04_employee_cannot_create_for_another(self):
        leave_env = self.env['hr.leave'].with_user(self.user_emp1)
        with self.assertRaises(AccessError):
            leave_env.create({
                'name': 'For Emp 2',
                'employee_id': self.employee2.id,
                'holiday_status_id': self.leave_type.id,
                'request_date_from': date(2026, 6, 1),
                'request_date_to': date(2026, 6, 2),
                'date_from': datetime(2026, 6, 1, 0, 0, 0),
                'date_to': datetime(2026, 6, 2, 23, 59, 59),
            })

    def test_leave_05_06_pending_edit_and_approved_immutability(self):
        leave = self.env['hr.leave'].with_user(self.user_emp1).create({
            'name': 'Pending Leave',
            'employee_id': self.employee1.id,
            'holiday_status_id': self.leave_type.id,
            'request_date_from': date(2026, 6, 1),
            'request_date_to': date(2026, 6, 2),
            'date_from': datetime(2026, 6, 1, 0, 0, 0),
            'date_to': datetime(2026, 6, 2, 23, 59, 59),
        })
        leave.write({'name': 'Updated Pending Leave'})
        self.assertEqual(leave.name, 'Updated Pending Leave')

        # Sudo/HR approves leave
        leave.with_user(self.user_hr).write({'state': 'validate'})

        # Employee cannot modify approved leave
        with self.assertRaises(UserError):
            leave.with_user(self.user_emp1).write({'name': 'Try Modify Approved'})

        # Employee cannot delete approved leave
        with self.assertRaises(UserError):
            leave.with_user(self.user_emp1).unlink()

    def test_leave_07_08_employee_cannot_approve_hr_can(self):
        leave = self.env['hr.leave'].with_user(self.user_emp1).create({
            'name': 'Leave Approval Test',
            'employee_id': self.employee1.id,
            'holiday_status_id': self.leave_type.id,
            'request_date_from': date(2026, 7, 1),
            'request_date_to': date(2026, 7, 2),
            'date_from': datetime(2026, 7, 1, 0, 0, 0),
            'date_to': datetime(2026, 7, 2, 23, 59, 59),
        })

        with self.assertRaises(AccessError):
            leave.with_user(self.user_emp1).write({'state': 'validate'})

        leave.with_user(self.user_hr).write({'state': 'validate'})
        self.assertEqual(leave.state, 'validate')

    def test_leave_09_approved_leave_syncs_with_attendance(self):
        leave = self.env['hr.leave'].create({
            'name': 'Sync Test Leave',
            'employee_id': self.employee1.id,
            'holiday_status_id': self.leave_type.id,
            'request_date_from': date(2026, 8, 10),
            'request_date_to': date(2026, 8, 11),
            'date_from': datetime(2026, 8, 10, 0, 0, 0),
            'date_to': datetime(2026, 8, 11, 23, 59, 59),
        })

        # Approve leave
        leave.with_user(self.user_hr).write({'state': 'validate'})

        att_count = self.env['hr.attendance'].search_count([
            ('employee_id', '=', self.employee1.id),
            ('check_in', '>=', datetime(2026, 8, 10, 0, 0, 0)),
            ('check_in', '<=', datetime(2026, 8, 11, 23, 59, 59)),
        ])
        self.assertEqual(att_count, 2)

        # Approving twice does not duplicate attendance
        leave._sync_leave_to_attendance()
        att_count_after = self.env['hr.attendance'].search_count([
            ('employee_id', '=', self.employee1.id),
            ('check_in', '>=', datetime(2026, 8, 10, 0, 0, 0)),
            ('check_in', '<=', datetime(2026, 8, 11, 23, 59, 59)),
        ])
        self.assertEqual(att_count_after, 2)
