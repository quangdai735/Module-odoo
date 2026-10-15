# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class HopDong(models.Model):
    _name = 'hopdong'
    _description = 'Hợp đồng lao động'
    _inherit = ['mail.thread']
    _order = 'ngay_bat_dau desc, id desc'

    name = fields.Char(string="Số hợp đồng", required=True, copy=False, readonly=True,
                       default='Mới')
    nhanvien_id = fields.Many2one('nhanvien', string="Nhân viên", required=True,
                                  ondelete='cascade', tracking=True)
    phong_id = fields.Many2one(related='nhanvien_id.phong_id', string="Phòng", store=True)
    loai = fields.Selection([
        ('thu_viec', 'Thử việc'),
        ('xac_dinh', 'Xác định thời hạn'),
        ('khong_xac_dinh', 'Không xác định thời hạn'),
    ], string="Loại hợp đồng", required=True, default='thu_viec', tracking=True)
    ngay_bat_dau = fields.Date(string="Ngày bắt đầu", required=True,
                               default=fields.Date.context_today, tracking=True)
    ngay_ket_thuc = fields.Date(string="Ngày kết thúc", tracking=True)
    company_id = fields.Many2one('res.company', string="Công ty", default=lambda self: self.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id')
    luong = fields.Monetary(string="Mức lương", currency_field='currency_id', tracking=True)
    state = fields.Selection([
        ('nhap', 'Nháp'),
        ('hieu_luc', 'Đang hiệu lực'),
        ('het_han', 'Hết hạn'),
        ('huy', 'Đã huỷ'),
    ], string="Trạng thái", default='nhap', required=True, tracking=True)
    note = fields.Text(string="Ghi chú")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Mới') == 'Mới':
                vals['name'] = self.env['ir.sequence'].next_by_code('hopdong') or 'Mới'
        return super().create(vals_list)

    @api.constrains('ngay_bat_dau', 'ngay_ket_thuc', 'loai')
    def _check_dates(self):
        for rec in self:
            if rec.ngay_ket_thuc and rec.ngay_ket_thuc < rec.ngay_bat_dau:
                raise ValidationError("Ngày kết thúc phải sau ngày bắt đầu!")
            if rec.loai != 'khong_xac_dinh' and not rec.ngay_ket_thuc:
                raise ValidationError("Hợp đồng có thời hạn phải nhập ngày kết thúc!")

    @api.constrains('luong')
    def _check_luong(self):
        for rec in self:
            if rec.luong < 0:
                raise ValidationError("Mức lương không được âm!")

    @api.constrains('nhanvien_id', 'state')
    def _check_one_active(self):
        for rec in self.filtered(lambda r: r.state == 'hieu_luc'):
            if self.search_count([('nhanvien_id', '=', rec.nhanvien_id.id),
                                  ('state', '=', 'hieu_luc'), ('id', '!=', rec.id)]):
                raise ValidationError("Nhân viên chỉ được có một hợp đồng đang hiệu lực!")

    def action_xac_nhan(self):
        self.write({'state': 'hieu_luc'})
        for rec in self:
            if rec.loai != 'thu_viec' and rec.nhanvien_id.state == 'thu_viec':
                rec.nhanvien_id.state = 'chinh_thuc'
            rec.nhanvien_id.luong_co_ban = rec.luong

    def action_het_han(self):
        self.write({'state': 'het_han'})

    def action_huy(self):
        self.write({'state': 'huy'})

    def action_ve_nhap(self):
        self.write({'state': 'nhap'})

    @api.model
    def _cron_het_han_hopdong(self):
        """Tự động chuyển hợp đồng quá hạn sang 'Hết hạn'."""
        today = fields.Date.context_today(self)
        self.search([('state', '=', 'hieu_luc'), ('ngay_ket_thuc', '<', today)]).action_het_han()
