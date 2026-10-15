# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class Phong(models.Model):
    _name = 'phong'
    _description = 'Phòng ban'
    _inherit = ['mail.thread']
    _order = 'depid, name'

    name = fields.Char(string="Tên phòng", required=True, tracking=True)
    depid = fields.Integer(string="Mã phòng", required=True, tracking=True)
    parent_id = fields.Many2one('phong', string="Phòng cấp trên", ondelete='restrict')
    child_ids = fields.One2many('phong', 'parent_id', string="Phòng trực thuộc")
    manager_id = fields.Many2one(
        'nhanvien', string="Trưởng phòng", tracking=True, ondelete='set null',
        domain="[('phong_id', '=', id)]")
    nhanvien_ids = fields.One2many('nhanvien', 'phong_id', string="Nhân viên")
    nhanvien_count = fields.Integer(string="Số nhân viên", compute='_compute_nhanvien_count')
    description = fields.Text(string="Mô tả")
    active = fields.Boolean(string="Đang hoạt động", default=True)
    company_id = fields.Many2one(
        'res.company', string="Công ty", default=lambda self: self.env.company)

    _sql_constraints = [
        ('depid_uniq', 'unique(depid)', 'Mã phòng đã tồn tại!'),
    ]

    @api.depends('nhanvien_ids')
    def _compute_nhanvien_count(self):
        data = self.env['nhanvien']._read_group(
            [('phong_id', 'in', self.ids)], ['phong_id'], ['__count'])
        counts = {phong.id: count for phong, count in data}
        for rec in self:
            rec.nhanvien_count = counts.get(rec.id, 0)

    @api.constrains('parent_id')
    def _check_parent_recursion(self):
        if self._has_cycle():
            raise ValidationError("Không thể tạo phòng cấp trên đệ quy!")

    @api.depends('name', 'depid')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = "[%s] %s" % (rec.depid, rec.name) if rec.name else ''

    def action_view_nhanvien(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': "Nhân viên - %s" % self.name,
            'res_model': 'nhanvien',
            'view_mode': 'list,form',
            'domain': [('phong_id', '=', self.id)],
            'context': {'default_phong_id': self.id},
        }
