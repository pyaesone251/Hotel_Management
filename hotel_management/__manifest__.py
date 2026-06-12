# -*- coding: utf-8 -*-
{
    'name': 'Hotel Management',
    'version': '18.0.1.0.0',
    'summary': 'Manage hotel rooms, guests, and bookings',
    'description': """
        Comprehensive Hotel Management System
        ======================================
        This module provides a full-featured hotel management solution including:
        - Room inventory and status tracking
        - Guest registration and history
        - Booking lifecycle management with confirmations
        - PDF booking receipt reports
        - Kanban board for room availability
    """,
    'author': 'Custom',
    'category': 'Services/Hotel',
    'license': 'LGPL-3',
    'depends': ['base', 'mail'],
    'data': [
        'security/hotel_security.xml',
        'security/ir.model.access.csv',
        'views/hotel_views.xml',
        'views/hotel_kanban.xml',
        'reports/booking_report.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
