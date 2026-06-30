# -*- coding: utf-8 -*-
{
    'name': 'Hotel Management',
    'version': '18.0.1.0.0',
    'category': 'Industries',
    'summary': 'Manage Hotel Rooms, Reservations, Guests and Services',
    'description': """
        Hotel Management System for Odoo 18
        =====================================
        Features:
        - Room Type & Room Management
        - Guest Registration
        - Reservation / Booking Management
        - Additional Services (Room Service, Laundry, etc.)
        - Folio (Invoice) Management
        - Check-in / Check-out Workflow
        - Dashboard & Reporting
    """,
    'author': 'Custom',
    'website': '',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'account',
    ],
    'data': [
        # Security
        'security/hotel_security.xml',
        'security/ir.model.access.csv',
        # Data
        'data/hotel_sequence.xml',
        'data/hotel_data.xml',
        # Views
        'views/hotel_room_type_views.xml',
        'views/hotel_room_views.xml',
        'views/hotel_guest_views.xml',
        'views/hotel_reservation_views.xml',
        'views/hotel_service_views.xml',
        'views/hotel_folio_views.xml',
        'views/hotel_dashboard_views.xml',
        'views/hotel_menu.xml',
        # Reports
        'report/hotel_report.xml',
        'report/hotel_reservation_report_template.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'images': ['static/description/banner.png'],
}
