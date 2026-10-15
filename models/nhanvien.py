# -*- coding: utf-8 -*-
import re

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import AccessError, ValidationError


class NhanVien(models.Model):
    _name = 'nhanvien'
    _description = 'Nhân viên'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'empid, name'

    # --- Thông tin cơ bản ---
    name = fields.Char(string="Họ và tên", required=True, tracking=True)
    empid = fields.Integer(string="Mã nhân viên", required=True, tracking=True)
    image_1920 = fields.Image(string="Ảnh", max_width=1920, max_height=1920)
    gender = fields.Selection([
        ('nam', 'Nam'),
        ('nu', 'Nữ'),
        ('khac', 'Khác'),
    ], string="Giới tính")
    birthday = fields.Date(string="Ngày sinh")
    age = fields.Integer(string="Tuổi", compute='_compute_age')
    cccd = fields.Char(string="CCCD/CMND", groups="kiemtra3.group_nhansu_user")
    phone = fields.Char(string="Điện thoại", tracking=True)
    email = fields.Char(string="Email")
    address = fields.Char(string="Địa chỉ")

    # --- Công việc ---
    phong_id = fields.Many2one('phong', string="Phòng", tracking=True, ondelete='restrict')
    chucvu_id = fields.Many2one('chucvu', string="Chức vụ", tracking=True, ondelete='restrict')
    ngay_vao_lam = fields.Date(string="Ngày vào làm", default=fields.Date.context_today)
    ngay_nghi_viec = fields.Date(string="Ngày nghỉ việc", tracking=True)
    nam_cong_tac = fields.Float(string="Thâm niên (năm)", compute='_compute_nam_cong_tac', digits=(6, 1))
    state = fields.Selection([
        ('thu_viec', 'Thử việc'),
        ('chinh_thuc', 'Chính thức'),
        ('nghi_viec', 'Đã nghỉ việc'),
    ], string="Trạng thái", default='thu_viec', required=True, tracking=True)

    # --- Lương & hợp đồng ---
    company_id = fields.Many2one('res.company', string="Công ty", default=lambda self: self.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id', string="Tiền tệ")
    luong_co_ban = fields.Monetary(string="Lương cơ bản", currency_field='currency_id', tracking=True,
                                groups="kiemtra3.group_nhansu_user")
    hopdong_ids = fields.One2many('hopdong', 'nhanvien_id', string="Hợp đồng",
                                  groups="kiemtra3.group_nhansu_user")
    hopdong_count = fields.Integer(string="Số hợp đồng", compute='_compute_hopdong_count',
                                  groups="kiemtra3.group_nhansu_user")

    active = fields.Boolean(string="Đang sử dụng", default=True)
    note = fields.Html(string="Ghi chú")

    _sql_constraints = [
        ('empid_uniq', 'unique(empid)', 'Mã nhân viên đã tồn tại!'),
    ]

    # ---------- compute ----------
    @api.depends('birthday')
    def _compute_age(self):
        today = fields.Date.context_today(self)
        for rec in self:
            rec.age = relativedelta(today, rec.birthday).years if rec.birthday else 0

    @api.depends('ngay_vao_lam', 'ngay_nghi_viec')
    def _compute_nam_cong_tac(self):
        today = fields.Date.context_today(self)
        for rec in self:
            if rec.ngay_vao_lam:
                end = rec.ngay_nghi_viec or today
                rec.nam_cong_tac = max((end - rec.ngay_vao_lam).days, 0) / 365.25
            else:
                rec.nam_cong_tac = 0.0

    @api.depends('hopdong_ids')
    def _compute_hopdong_count(self):
        data = self.env['hopdong']._read_group(
            [('nhanvien_id', 'in', self.ids)], ['nhanvien_id'], ['__count'])
        counts = {nv.id: count for nv, count in data}
        for rec in self:
            rec.hopdong_count = counts.get(rec.id, 0)

    @api.depends('name', 'empid')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = "[%s] %s" % (rec.empid, rec.name) if rec.name else ''

    # ---------- constraints ----------
    @api.constrains('empid')
    def _check_empid(self):
        for rec in self:
            if rec.empid <= 0:
                raise ValidationError("Mã nhân viên phải là số nguyên dương!")

    @api.constrains('phone')
    def _check_phone(self):
        for rec in self:
            if rec.phone and not re.fullmatch(r'(\+84|0)\d{9,10}', rec.phone.replace(' ', '')):
                raise ValidationError(
                    "Số điện thoại không hợp lệ (ví dụ: 0977873516 hoặc +84977873516)!")

    @api.constrains('email')
    def _check_email(self):
        for rec in self:
            if rec.email and not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', rec.email):
                raise ValidationError("Email không hợp lệ!")

    @api.constrains('cccd')
    def _check_cccd(self):
        for rec in self:
            if rec.cccd and not re.fullmatch(r'\d{9}|\d{12}', rec.cccd):
                raise ValidationError("CCCD phải gồm 12 chữ số (hoặc CMND 9 chữ số)!")

    @api.constrains('birthday')
    def _check_birthday(self):
        today = fields.Date.context_today(self)
        for rec in self:
            if rec.birthday and relativedelta(today, rec.birthday).years < 18:
                raise ValidationError("Nhân viên phải đủ 18 tuổi!")

    @api.constrains('ngay_vao_lam', 'ngay_nghi_viec')
    def _check_dates(self):
        for rec in self:
            if rec.ngay_vao_lam and rec.ngay_nghi_viec and rec.ngay_nghi_viec < rec.ngay_vao_lam:
                raise ValidationError("Ngày nghỉ việc phải sau ngày vào làm!")

    @api.constrains('luong_co_ban')
    def _check_luong(self):
        for rec in self:
            if rec.luong_co_ban < 0:
                raise ValidationError("Lương cơ bản không được âm!")

    # ---------- actions ----------
    def _check_hr_rights(self):
        if not self.env.user.has_group('kiemtra3.group_nhansu_user'):
            raise AccessError("Bạn không có quyền thực hiện thao tác này!")

    def action_chinh_thuc(self):
        self._check_hr_rights()
        self.write({'state': 'chinh_thuc'})

    def action_nghi_viec(self):
        self._check_hr_rights()
        self.write({'state': 'nghi_viec', 'ngay_nghi_viec': fields.Date.context_today(self)})

    def action_quay_lai_lam_viec(self):
        self._check_hr_rights()
        self.write({'state': 'chinh_thuc', 'ngay_nghi_viec': False})

    def action_view_hopdong(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': "Hợp đồng - %s" % self.name,
            'res_model': 'hopdong',
            'view_mode': 'list,form',
            'domain': [('nhanvien_id', '=', self.id)],
            'context': {'default_nhanvien_id': self.id, 'default_luong': self.luong_co_ban},
        }
