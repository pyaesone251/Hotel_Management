# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HotelRoom(models.Model):
    _name = 'hotel.room'
    _description = 'Hotel Room'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'floor, name'

    name = fields.Char(string='Room Number', required=True, tracking=True)
    room_type_id = fields.Many2one(
        'hotel.room.type', string='Room Type',
        required=True, tracking=True,
    )
    floor = fields.Integer(string='Floor', default=1, tracking=True)
    state = fields.Selection([
        ('available', 'Available'),
        ('occupied', 'Occupied'),
        ('maintenance', 'Maintenance'),
        ('cleaning', 'Cleaning'),
    ], string='Status', default='available', tracking=True, required=True)
    price_per_night = fields.Float(
        string='Price per Night',
        related='room_type_id.base_price',
        store=True, readonly=False,
    )
    max_adults = fields.Integer(
        string='Max Adults',
        related='room_type_id.max_adults',
        store=True, readonly=False,
    )
    max_children = fields.Integer(
        string='Max Children',
        related='room_type_id.max_children',
        store=True, readonly=False,
    )
    amenities = fields.Text(string='Room Amenities')
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)
    image = fields.Binary(string='Room Image', attachment=True)
    color = fields.Integer(string='Color Index')

    # Computed
    current_reservation_id = fields.Many2one(
        'hotel.reservation', string='Current Reservation',
        compute='_compute_current_reservation',
    )
    current_guest_id = fields.Many2one(
        'hotel.guest', string='Current Guest',
        compute='_compute_current_reservation',
    )

    _sql_constraints = [
        ('unique_room_number', 'UNIQUE(name)', 'Room number must be unique!'),
    ]

    @api.depends('state')
    def _compute_current_reservation(self):
        for room in self:
            reservation = self.env['hotel.reservation'].search([
                ('room_id', '=', room.id),
                ('state', '=', 'checkin'),
            ], limit=1)
            room.current_reservation_id = reservation
            room.current_guest_id = reservation.guest_id if reservation else False

    def action_available(self):
        self.write({'state': 'available'})

    def action_maintenance(self):
        self.write({'state': 'maintenance'})

    def action_cleaning(self):
        self.write({'state': 'cleaning'})

    @api.constrains('floor')
    def _check_floor(self):
        for room in self:
            if room.floor < 0:
                raise ValidationError("Floor number cannot be negative.")
