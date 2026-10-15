# -*- coding: utf-8 -*-
from odoo import fields, models


class ChucVu(models.Model):
    _name = 'chucvu'
    _description = 'Chức vụ'
    _order = 'sequence, name'

    name = fields.Char(string="Tên chức vụ", required=True)
    sequence = fields.Integer(string="Thứ tự", default=10)
    description = fields.Text(string="Mô tả")
    active = fields.Boolean(string="Đang sử dụng", default=True)
    nhanvien_ids = fields.One2many('nhanvien', 'chucvu_id', string="Nhân viên")

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Tên chức vụ đã tồn tại!'),
    ]
