from datetime import timedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HrmsSalaryStructure(models.Model):
    _name = 'hrms.salary.structure'
    _description = 'Employee Salary Structure'
    _order = 'effective_from desc, id desc'

    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
        index=True,
        ondelete='cascade'
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
    effective_from = fields.Date(
        string='Effective From',
        required=True,
        default=fields.Date.context_today
    )
    effective_to = fields.Date(
        string='Effective To'
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='employee_id.company_id.currency_id',
        readonly=True
    )

    @api.constrains('basic_salary', 'allowances', 'deductions')
    def _check_non_negative_amounts(self):
        for record in self:
            if record.basic_salary < 0 or record.allowances < 0 or record.deductions < 0:
                raise ValidationError(_("Salary amounts (basic salary, allowances, deductions) cannot be negative."))

    @api.constrains('effective_from', 'effective_to')
    def _check_date_range(self):
        for record in self:
            if record.effective_to and record.effective_to < record.effective_from:
                raise ValidationError(_("Effective To date cannot be earlier than Effective From date."))

    @api.constrains('employee_id', 'effective_to')
    def _check_single_active_structure(self):
        for record in self:
            if not record.effective_to:
                active_count = self.search_count([
                    ('employee_id', '=', record.employee_id.id),
                    ('effective_to', '=', False),
                    ('id', '!=', record.id)
                ])
                if active_count > 0:
                    raise ValidationError(_("An employee can only have one active salary structure at a time."))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('effective_to') and vals.get('employee_id') and vals.get('effective_from'):
                eff_from = fields.Date.from_string(vals['effective_from'])
                prev_active = self.search([
                    ('employee_id', '=', vals['employee_id']),
                    ('effective_to', '=', False)
                ])
                for prev in prev_active:
                    prev.write({'effective_to': eff_from - timedelta(days=1)})
        return super(HrmsSalaryStructure, self).create(vals_list)
