from datetime import timedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError, AccessError


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    @api.constrains('request_date_from', 'request_date_to', 'date_from', 'date_to')
    def _check_leave_dates(self):
        for record in self:
            date_from = record.date_from or record.request_date_from
            date_to = record.date_to or record.request_date_to
            if date_from and date_to and date_to < date_from:
                raise ValidationError(_("Leave end date cannot be earlier than start date."))

    @api.constrains('employee_id', 'date_from', 'date_to', 'state')
    def _check_overlapping_leave(self):
        for record in self:
            if record.employee_id and record.state not in ['refuse', 'cancel']:
                date_from = record.date_from or record.request_date_from
                date_to = record.date_to or record.request_date_to
                if date_from and date_to:
                    overlap_count = self.search_count([
                        ('employee_id', '=', record.employee_id.id),
                        ('state', 'not in', ['refuse', 'cancel']),
                        ('id', '!=', record.id),
                        ('date_from', '<=', date_to),
                        ('date_to', '>=', date_from),
                    ])
                    if overlap_count > 0:
                        raise ValidationError(_("The employee already has a leave request overlapping with this period."))

    @api.model_create_multi
    def create(self, vals_list):
        is_hr_officer = self.env.user.has_group('dayflow_hrms.group_dayflow_hr_officer')
        user_employee = self.env.user.employee_id or self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

        for vals in vals_list:
            if not is_hr_officer and not self.env.context.get('bypass_leave_ownership_check'):
                emp_id = vals.get('employee_id')
                if emp_id and user_employee and emp_id != user_employee.id:
                    raise AccessError(_("Employees can only request leave for themselves."))
        return super(HrLeave, self).create(vals_list)

    def write(self, vals):
        is_hr_officer = self.env.user.has_group('dayflow_hrms.group_dayflow_hr_officer')
        user_employee = self.env.user.employee_id or self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

        for record in self:
            if not is_hr_officer and not self.env.context.get('bypass_leave_ownership_check'):
                if user_employee and record.employee_id and record.employee_id != user_employee:
                    raise AccessError(_("Employees can only modify their own leave requests."))
                if record.state == 'validate' and any(k not in ['state'] for k in vals.keys()):
                    raise UserError(_("Approved leave requests cannot be modified by employees."))

            if 'state' in vals and vals['state'] in ['validate', 'refuse'] and not is_hr_officer:
                if not self.env.context.get('bypass_leave_approval_check'):
                    raise AccessError(_("Employees cannot approve or refuse leave requests."))

        res = super(HrLeave, self).write(vals)

        if 'state' in vals and vals['state'] == 'validate':
            self._sync_leave_to_attendance()

        return res

    def unlink(self):
        is_hr_officer = self.env.user.has_group('dayflow_hrms.group_dayflow_hr_officer')
        for record in self:
            if not is_hr_officer and not self.env.context.get('bypass_leave_ownership_check'):
                if record.state == 'validate':
                    raise UserError(_("Approved leave requests cannot be deleted by employees."))
        return super(HrLeave, self).unlink()

    def action_validate(self):
        is_hr_officer = self.env.user.has_group('dayflow_hrms.group_dayflow_hr_officer')
        if not is_hr_officer and not self.env.context.get('bypass_leave_approval_check'):
            raise AccessError(_("Only HR Officers can approve leave requests."))
        res = super(HrLeave, self).action_validate() if hasattr(super(HrLeave, self), 'action_validate') else True
        self._sync_leave_to_attendance()
        return res

    def action_approve(self):
        is_hr_officer = self.env.user.has_group('dayflow_hrms.group_dayflow_hr_officer')
        if not is_hr_officer and not self.env.context.get('bypass_leave_approval_check'):
            raise AccessError(_("Only HR Officers can approve leave requests."))
        res = super(HrLeave, self).action_approve() if hasattr(super(HrLeave, self), 'action_approve') else True
        self._sync_leave_to_attendance()
        return res

    def _sync_leave_to_attendance(self):
        """
        Synchronizes approved leave range to hr.attendance rows.
        Creates attendance records for days in the leave range if none exist.
        """
        Attendance = self.env['hr.attendance'].with_context(bypass_attendance_ownership_check=True)
        for leave in self:
            if leave.state == 'validate' and leave.employee_id:
                start_dt = leave.date_from or (fields.Datetime.from_string(str(leave.request_date_from) + ' 00:00:00') if leave.request_date_from else False)
                end_dt = leave.date_to or (fields.Datetime.from_string(str(leave.request_date_to) + ' 23:59:59') if leave.request_date_to else False)

                if not start_dt or not end_dt:
                    continue

                curr_date = start_dt.date() if hasattr(start_dt, 'date') else start_dt
                end_date = end_dt.date() if hasattr(end_dt, 'date') else end_dt

                while curr_date <= end_date:
                    day_start = fields.Datetime.from_string(f"{curr_date} 09:00:00")
                    day_end = fields.Datetime.from_string(f"{curr_date} 17:00:00")

                    existing = Attendance.search([
                        ('employee_id', '=', leave.employee_id.id),
                        ('check_in', '>=', fields.Datetime.from_string(f"{curr_date} 00:00:00")),
                        ('check_in', '<=', fields.Datetime.from_string(f"{curr_date} 23:59:59")),
                    ], limit=1)

                    if not existing:
                        Attendance.create({
                            'employee_id': leave.employee_id.id,
                            'check_in': day_start,
                            'check_out': day_end,
                        })

                    curr_date += timedelta(days=1)
