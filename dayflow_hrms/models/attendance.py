from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError, AccessError


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    @api.constrains('check_in', 'check_out')
    def _check_valid_timestamps(self):
        for record in self:
            if record.check_out and record.check_in and record.check_out <= record.check_in:
                raise ValidationError(_("Check-out time must be strictly after check-in time."))

    @api.constrains('employee_id', 'check_out')
    def _check_single_active_checkin(self):
        for record in self:
            if record.employee_id and not record.check_out:
                active_count = self.search_count([
                    ('employee_id', '=', record.employee_id.id),
                    ('check_out', '=', False),
                    ('id', '!=', record.id)
                ])
                if active_count > 0:
                    raise ValidationError(_("Employee already has an active check-in without check-out."))

    @api.model_create_multi
    def create(self, vals_list):
        is_hr_officer = self.env.user.has_group('dayflow_hrms.group_dayflow_hr_officer')
        user_employee = self.env.user.employee_id or self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

        for vals in vals_list:
            if not is_hr_officer and not self.env.context.get('bypass_attendance_ownership_check'):
                emp_id = vals.get('employee_id')
                if emp_id and user_employee and emp_id != user_employee.id:
                    raise AccessError(_("Employees can only record attendance for themselves."))
        return super(HrAttendance, self).create(vals_list)

    def write(self, vals):
        is_hr_officer = self.env.user.has_group('dayflow_hrms.group_dayflow_hr_officer')
        user_employee = self.env.user.employee_id or self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

        if not is_hr_officer and not self.env.context.get('bypass_attendance_ownership_check'):
            for record in self:
                if user_employee and record.employee_id and record.employee_id != user_employee:
                    raise AccessError(_("Employees can only edit attendance for themselves."))
        return super(HrAttendance, self).write(vals)
