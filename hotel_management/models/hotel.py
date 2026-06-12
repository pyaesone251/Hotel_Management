# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import timedelta


class HotelRoom(models.Model):
    _name = 'hotel.room'
    _description = 'Hotel Room'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(
        string='Room Number',
        required=True,
        tracking=True,
    )
    room_type = fields.Selection(
        selection=[
            ('single', 'Single'),
            ('double', 'Double'),
            ('suite', 'Suite'),
            ('deluxe', 'Deluxe'),
        ],
        string='Room Type',
        required=True,
        default='single',
        tracking=True,
    )
    floor = fields.Integer(string='Floor', default=1)
    capacity = fields.Integer(string='Capacity', default=1, required=True)
    price_per_night = fields.Float(
        string='Price per Night',
        required=True,
        tracking=True,
    )
    amenities = fields.Text(string='Amenities')
    state = fields.Selection(
        selection=[
            ('available', 'Available'),
            ('occupied', 'Occupied'),
            ('maintenance', 'Maintenance'),
        ],
        string='Status',
        default='available',
        required=True,
        tracking=True,
    )
    booking_ids = fields.One2many(
        comodel_name='hotel.booking',
        inverse_name='room_id',
        string='Bookings',
    )
    booking_count = fields.Integer(
        string='Booking Count',
        compute='_compute_booking_count',
    )
    active = fields.Boolean(string='Active', default=True)
    image = fields.Image(string='Room Image', max_width=1024, max_height=1024)
    description = fields.Html(string='Description')

    _sql_constraints = [
        ('name_unique', 'UNIQUE(name)', 'Room number must be unique!'),
        ('price_positive', 'CHECK(price_per_night >= 0)', 'Price per night must be positive!'),
        ('capacity_positive', 'CHECK(capacity > 0)', 'Capacity must be at least 1!'),
    ]

    @api.depends('booking_ids')
    def _compute_booking_count(self):
        for room in self:
            room.booking_count = len(room.booking_ids)

    def action_set_available(self):
        self.write({'state': 'available'})

    def action_set_maintenance(self):
        self.write({'state': 'maintenance'})

    def action_view_bookings(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Bookings',
            'res_model': 'hotel.booking',
            'view_mode': 'tree,form',
            'domain': [('room_id', '=', self.id)],
            'context': {'default_room_id': self.id},
        }


class HotelGuest(models.Model):
    _name = 'hotel.guest'
    _description = 'Hotel Guest'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'
    _rec_name = 'name'

    name = fields.Char(string='Full Name', required=True, tracking=True)
    email = fields.Char(string='Email', tracking=True)
    phone = fields.Char(string='Phone', tracking=True)
    id_type = fields.Selection(
        selection=[
            ('passport', 'Passport'),
            ('national_id', 'National ID'),
            ('driving_license', 'Driving License'),
        ],
        string='ID Type',
        default='passport',
    )
    id_number = fields.Char(string='ID Number')
    gender = fields.Selection(
        selection=[
            ('male', 'Male'),
            ('female', 'Female'),
            ('other', 'Other'),
        ],
        string='Gender',
    )
    date_of_birth = fields.Date(string='Date of Birth')
    nationality = fields.Char(string='Nationality')
    street = fields.Char(string='Street')
    city = fields.Char(string='City')
    state_id = fields.Many2one('res.country.state', string='State')
    country_id = fields.Many2one('res.country', string='Country')
    zip_code = fields.Char(string='ZIP Code')
    vip = fields.Boolean(string='VIP Guest', default=False, tracking=True)
    notes = fields.Text(string='Internal Notes')
    booking_ids = fields.One2many(
        comodel_name='hotel.booking',
        inverse_name='guest_id',
        string='Bookings',
    )
    booking_count = fields.Integer(
        string='Booking Count',
        compute='_compute_booking_count',
    )
    image = fields.Image(string='Photo', max_width=512, max_height=512)
    active = fields.Boolean(string='Active', default=True)

    @api.depends('booking_ids')
    def _compute_booking_count(self):
        for guest in self:
            guest.booking_count = len(guest.booking_ids)

    def action_view_bookings(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Guest Bookings',
            'res_model': 'hotel.booking',
            'view_mode': 'tree,form',
            'domain': [('guest_id', '=', self.id)],
            'context': {'default_guest_id': self.id},
        }


class HotelBooking(models.Model):
    _name = 'hotel.booking'
    _description = 'Hotel Booking'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'checkin_date desc'
    _rec_name = 'reference'

    reference = fields.Char(
        string='Booking Reference',
        required=True,
        copy=False,
        readonly=True,
        default='New',
    )
    guest_id = fields.Many2one(
        comodel_name='hotel.guest',
        string='Guest',
        required=True,
        tracking=True,
    )
    room_id = fields.Many2one(
        comodel_name='hotel.room',
        string='Room',
        required=True,
        tracking=True,
    )
    checkin_date = fields.Date(
        string='Check-in Date',
        required=True,
        tracking=True,
    )
    checkout_date = fields.Date(
        string='Check-out Date',
        required=True,
        tracking=True,
    )
    duration = fields.Integer(
        string='Duration (Nights)',
        compute='_compute_duration',
        store=True,
    )
    price_per_night = fields.Float(
        string='Price per Night',
        related='room_id.price_per_night',
        store=True,
        readonly=False,
    )
    total_price = fields.Float(
        string='Total Price',
        compute='_compute_total_price',
        store=True,
        tracking=True,
    )
    num_guests = fields.Integer(string='Number of Guests', default=1)
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('confirmed', 'Confirmed'),
            ('checkin', 'Checked In'),
            ('checkout', 'Checked Out'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='draft',
        required=True,
        tracking=True,
    )
    special_requests = fields.Text(string='Special Requests')
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
    )
    guest_email = fields.Char(
        string='Guest Email',
        related='guest_id.email',
        readonly=True,
    )
    guest_phone = fields.Char(
        string='Guest Phone',
        related='guest_id.phone',
        readonly=True,
    )
    room_type = fields.Selection(
        string='Room Type',
        related='room_id.room_type',
        readonly=True,
        store=True,
    )

    _sql_constraints = [
        ('check_dates', 'CHECK(checkout_date > checkin_date)',
         'Check-out date must be after check-in date!'),
        ('check_num_guests', 'CHECK(num_guests > 0)',
         'Number of guests must be at least 1!'),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('reference', 'New') == 'New':
                vals['reference'] = self.env['ir.sequence'].next_by_code(
                    'hotel.booking'
                ) or 'New'
        return super().create(vals_list)

    @api.depends('checkin_date', 'checkout_date')
    def _compute_duration(self):
        for booking in self:
            if booking.checkin_date and booking.checkout_date:
                delta = booking.checkout_date - booking.checkin_date
                booking.duration = delta.days if delta.days > 0 else 0
            else:
                booking.duration = 0

    @api.depends('duration', 'price_per_night')
    def _compute_total_price(self):
        for booking in self:
            booking.total_price = booking.duration * booking.price_per_night

    @api.constrains('checkin_date', 'checkout_date')
    def _check_dates(self):
        for booking in self:
            if booking.checkin_date and booking.checkout_date:
                if booking.checkout_date <= booking.checkin_date:
                    raise ValidationError(
                        'Check-out date must be after the check-in date!'
                    )

    @api.constrains('num_guests', 'room_id')
    def _check_capacity(self):
        for booking in self:
            if booking.room_id and booking.num_guests > booking.room_id.capacity:
                raise ValidationError(
                    'Number of guests (%s) exceeds room capacity (%s)!'
                    % (booking.num_guests, booking.room_id.capacity)
                )

    def action_confirm(self):
        for booking in self:
            if booking.state != 'draft':
                raise ValidationError('Only draft bookings can be confirmed.')
            booking.state = 'confirmed'
            booking.room_id.state = 'available'

    def action_checkin(self):
        for booking in self:
            if booking.state != 'confirmed':
                raise ValidationError(
                    'Only confirmed bookings can be checked in.'
                )
            booking.state = 'checkin'
            booking.room_id.state = 'occupied'

    def action_checkout(self):
        for booking in self:
            if booking.state != 'checkin':
                raise ValidationError(
                    'Only checked-in bookings can be checked out.'
                )
            booking.state = 'checkout'
            booking.room_id.state = 'available'

    def action_cancel(self):
        for booking in self:
            if booking.state in ('checkout',):
                raise ValidationError(
                    'Cannot cancel a booking that has already been checked out.'
                )
            if booking.state == 'checkin':
                booking.room_id.state = 'available'
            booking.state = 'cancelled'

    def action_reset_to_draft(self):
        for booking in self:
            if booking.state != 'cancelled':
                raise ValidationError(
                    'Only cancelled bookings can be reset to draft.'
                )
            booking.state = 'draft'
