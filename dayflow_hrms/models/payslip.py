from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class HrmsPayslip(models.Model):
    _name = 'hrms.payslip'
    _description = 'Employee Payslip Snapshot'
    _order = 'year desc, month desc, id desc'

    _sql_constraints = [
        (
            'unique_employee_month_year',
            'unique(employee_id, month, year)',
            'A payslip for this employee for the specified month and year already exists.'
        )
    ]

    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
        index=True,
        ondelete='restrict'
    )
    salary_structure_id = fields.Many2one(
        'hrms.salary.structure',
        string='Salary Structure',
        required=True,
        ondelete='restrict'
    )
    month = fields.Integer(
        string='Month',
        required=True
    )
    year = fields.Integer(
        string='Year',
        required=True
    )
    basic_salary = fields.Monetary(
        string='Basic Salary',
        required=True,
        currency_field='currency_id'
    )
    allowances = fields.Monetary(
        string='Allowances',
        default=0.0,
        currency_field='currency_id'
    )
    deductions = fields.Monetary(
        string='Deductions',
        default=0.0,
        currency_field='currency_id'
    )
    gross_salary = fields.Monetary(
        string='Gross Salary',
        required=True,
        currency_field='currency_id'
    )
    net_salary = fields.Monetary(
        string='Net Salary',
        required=True,
        currency_field='currency_id'
    )
    generated_at = fields.Datetime(
        string='Generated At',
        required=True,
        default=fields.Datetime.now,
        readonly=True
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='employee_id.company_id.currency_id',
        readonly=True
    )

    @api.constrains('month')
    def _check_month_validity(self):
        for record in self:
            if not (1 <= record.month <= 12):
                raise ValidationError(_("Month must be an integer between 1 and 12."))

    @api.constrains('year')
    def _check_year_validity(self):
        for record in self:
            if record.year < 1900 or record.year > 2100:
                raise ValidationError(_("Year must be a valid four-digit year."))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('salary_structure_id'):
                struct = self.env['hrms.salary.structure'].browse(vals['salary_structure_id'])
                if 'basic_salary' not in vals:
                    vals['basic_salary'] = struct.basic_salary
                if 'allowances' not in vals:
                    vals['allowances'] = struct.allowances
                if 'deductions' not in vals:
                    vals['deductions'] = struct.deductions

            basic = vals.get('basic_salary', 0.0)
            allowances = vals.get('allowances', 0.0)
            deductions = vals.get('deductions', 0.0)

            vals['gross_salary'] = basic + allowances
            vals['net_salary'] = vals['gross_salary'] - deductions

        return super(HrmsPayslip, self).create(vals_list)

    def write(self, vals):
        if not self.env.context.get('bypass_payslip_immutability'):
            raise UserError(_("Payslips are immutable once generated and cannot be modified."))
        return super(HrmsPayslip, self).write(vals)

    def unlink(self):
        if not self.env.context.get('bypass_payslip_immutability'):
            raise UserError(_("Payslips are immutable once generated and cannot be deleted."))
        return super(HrmsPayslip, self).unlink()
