# -*- coding: utf-8 -*-
from odoo import models, fields


class HotelService(models.Model):
    _name = 'hotel.service'
    _description = 'Hotel Service'
    _order = 'category, sequence, name'

    name = fields.Char(string='Service Name', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    code = fields.Char(string='Code')
    category = fields.Selection([
        ('room_service', 'Room Service'),
        ('food', 'Food & Beverage'),
        ('laundry', 'Laundry'),
        ('transport', 'Transport'),
        ('spa', 'Spa & Wellness'),
        ('tour', 'Tour & Activities'),
        ('other', 'Other'),
    ], string='Category', default='other', required=True)
    price = fields.Float(string='Price', required=True, default=0.0)
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company,
    )

    _sql_constraints = [
        ('unique_code', 'UNIQUE(code)',
         'Service code must be unique!'),
    ]
