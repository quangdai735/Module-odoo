# -*- coding: utf-8 -*-
{
    'name': "Quản lý nhân sự",
    'summary': "Quản lý phòng ban, chức vụ, nhân viên và hợp đồng lao động",
    'description': """
Module quản lý nhân sự (Odoo 18)
================================

* Phòng ban: phòng cấp trên, trưởng phòng, thống kê số nhân viên
* Chức vụ
* Nhân viên: thông tin cá nhân, công việc, lương, trạng thái thử việc / chính thức / nghỉ việc
* Hợp đồng lao động: số tự động, quy trình trạng thái, cron tự động hết hạn
* Phân quyền: Nhân viên nhân sự / Quản lý nhân sự, quy tắc đa công ty
* Chatter, lọc và nhóm, kanban, pivot, graph
    """,
    'author': "Bui Quang Dai",
    'website': "https://www.google.com",
    'category': 'Human Resources',
    'version': '18.0.1.0.0',
    'license': 'LGPL-3',
    'depends': ['base', 'mail'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/chucvu_views.xml',
        'views/phong_views.xml',
        'views/nhanvien_views.xml',
        'views/hopdong_views.xml',
        'views/menus.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
    'application': True,
    'installable': True,
}
