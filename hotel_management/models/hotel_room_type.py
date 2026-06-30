# -*- coding: utf-8 -*-
from odoo import models, fields, api


class HotelRoomType(models.Model):
    _name = 'hotel.room.type'
    _description = 'Hotel Room Type'
    _order = 'sequence, name'

    name = fields.Char(string='Room Type', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    code = fields.Char(string='Code', required=True)
    description = fields.Text(string='Description')
    base_price = fields.Float(string='Base Price per Night', required=True, default=0.0)
    max_adults = fields.Integer(string='Max Adults', default=2)
    max_children = fields.Integer(string='Max Children', default=1)
    amenities = fields.Text(string='Amenities')
    room_ids = fields.One2many('hotel.room', 'room_type_id', string='Rooms')
    room_count = fields.Integer(string='Room Count', compute='_compute_room_count', store=True)
    active = fields.Boolean(string='Active', default=True)
    image = fields.Binary(string='Image', attachment=True)

    _sql_constraints = [
        ('unique_code', 'UNIQUE(code)', 'Room type code must be unique!'),
    ]

    @api.depends('room_ids')
    def _compute_room_count(self):
        for rec in self:
            rec.room_count = len(rec.room_ids)
