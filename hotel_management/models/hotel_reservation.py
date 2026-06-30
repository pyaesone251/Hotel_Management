# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta


class HotelReservation(models.Model):
    _name = 'hotel.reservation'
    _description = 'Hotel Reservation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'checkin_date desc, id desc'

    name = fields.Char(
        string='Reservation No.', required=True, readonly=True,
        default='New', copy=False, tracking=True,
    )
    guest_id = fields.Many2one(
        'hotel.guest', string='Guest', required=True,
        tracking=True, index=True,
    )
    partner_id = fields.Many2one(
        'res.partner', string='Contact',
        related='guest_id.partner_id', store=True,
    )
    room_id = fields.Many2one(
        'hotel.room', string='Room', required=True,
        tracking=True, index=True,
    )
    room_type_id = fields.Many2one(
        'hotel.room.type', string='Room Type',
        related='room_id.room_type_id', store=True,
    )

    # Dates
    checkin_date = fields.Datetime(
        string='Check-in Date', required=True,
        tracking=True,
        default=fields.Datetime.now,
    )
    checkout_date = fields.Datetime(
        string='Check-out Date', required=True,
        tracking=True,
    )
    duration = fields.Integer(
        string='Duration (Nights)',
        compute='_compute_duration', store=True,
    )

    # Guests
    adults = fields.Integer(string='Adults', default=1, required=True)
    children = fields.Integer(string='Children', default=0)

    # Pricing
    price_per_night = fields.Float(
        string='Price per Night',
        related='room_id.price_per_night',
        store=True, readonly=False,
    )
    total_room_charge = fields.Float(
        string='Total Room Charge',
        compute='_compute_total_room_charge', store=True,
    )
    discount = fields.Float(string='Discount (%)', default=0.0)

    # State
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('checkin', 'Checked In'),
        ('checkout', 'Checked Out'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True, required=True)

    # Related
    folio_id = fields.Many2one('hotel.folio', string='Folio', copy=False)
    service_line_ids = fields.One2many(
        'hotel.service.line', 'reservation_id', string='Services',
    )
    total_service_charge = fields.Float(
        string='Total Service Charge',
        compute='_compute_total_service_charge', store=True,
    )
    grand_total = fields.Float(
        string='Grand Total',
        compute='_compute_grand_total', store=True,
    )

    # Additional
    source = fields.Selection([
        ('walkin', 'Walk-in'),
        ('phone', 'Phone'),
        ('email', 'Email'),
        ('website', 'Website'),
        ('agent', 'Travel Agent'),
        ('other', 'Other'),
    ], string='Booking Source', default='walkin')
    special_requests = fields.Text(string='Special Requests')
    notes = fields.Text(string='Internal Notes')
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one(
        'res.currency', string='Currency',
        related='company_id.currency_id', store=True,
    )
    color = fields.Integer(string='Color')

    _sql_constraints = [
        ('unique_reservation_name', 'UNIQUE(name)',
         'Reservation number must be unique!'),
    ]

    # -------------------------------------------------------------------------
    # Compute Methods
    # -------------------------------------------------------------------------
    @api.depends('checkin_date', 'checkout_date')
    def _compute_duration(self):
        for rec in self:
            if rec.checkin_date and rec.checkout_date:
                delta = rec.checkout_date - rec.checkin_date
                rec.duration = max(delta.days, 1)
            else:
                rec.duration = 0

    @api.depends('price_per_night', 'duration', 'discount')
    def _compute_total_room_charge(self):
        for rec in self:
            subtotal = rec.price_per_night * rec.duration
            rec.total_room_charge = subtotal * (1 - rec.discount / 100)

    @api.depends('service_line_ids.subtotal')
    def _compute_total_service_charge(self):
        for rec in self:
            rec.total_service_charge = sum(
                rec.service_line_ids.mapped('subtotal')
            )

    @api.depends('total_room_charge', 'total_service_charge')
    def _compute_grand_total(self):
        for rec in self:
            rec.grand_total = rec.total_room_charge + rec.total_service_charge

    # -------------------------------------------------------------------------
    # Constraints
    # -------------------------------------------------------------------------
    @api.constrains('checkin_date', 'checkout_date')
    def _check_dates(self):
        for rec in self:
            if rec.checkin_date and rec.checkout_date:
                if rec.checkout_date <= rec.checkin_date:
                    raise ValidationError(
                        "Check-out date must be after check-in date."
                    )

    @api.constrains('adults')
    def _check_adults(self):
        for rec in self:
            if rec.adults < 1:
                raise ValidationError(
                    "Number of adults must be at least 1."
                )

    @api.constrains('room_id', 'checkin_date', 'checkout_date', 'state')
    def _check_room_availability(self):
        for rec in self:
            if rec.state in ('cancelled', 'checkout'):
                continue
            domain = [
                ('room_id', '=', rec.room_id.id),
                ('id', '!=', rec.id),
                ('state', 'not in', ['cancelled', 'checkout']),
                ('checkin_date', '<', rec.checkout_date),
                ('checkout_date', '>', rec.checkin_date),
            ]
            overlapping = self.search_count(domain)
            if overlapping:
                raise ValidationError(
                    f"Room {rec.room_id.name} is already booked for the "
                    f"selected dates. Please choose different dates or room."
                )

    # -------------------------------------------------------------------------
    # CRUD
    # -------------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'hotel.reservation'
                ) or 'New'
        return super().create(vals_list)

    # -------------------------------------------------------------------------
    # Actions / Workflow
    # -------------------------------------------------------------------------
    def action_confirm(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError("Only draft reservations can be confirmed.")
            rec.state = 'confirmed'

    def action_checkin(self):
        for rec in self:
            if rec.state != 'confirmed':
                raise UserError(
                    "Only confirmed reservations can be checked in."
                )
            rec.state = 'checkin'
            rec.room_id.state = 'occupied'
            # Create folio if not exists
            if not rec.folio_id:
                folio = self.env['hotel.folio'].create({
                    'reservation_id': rec.id,
                    'guest_id': rec.guest_id.id,
                    'room_id': rec.room_id.id,
                    'checkin_date': rec.checkin_date,
                    'checkout_date': rec.checkout_date,
                })
                rec.folio_id = folio

    def action_checkout(self):
        for rec in self:
            if rec.state != 'checkin':
                raise UserError(
                    "Only checked-in reservations can be checked out."
                )
            rec.state = 'checkout'
            rec.room_id.state = 'cleaning'
            # Update folio
            if rec.folio_id and rec.folio_id.state == 'draft':
                rec.folio_id.action_confirm()

    def action_cancel(self):
        for rec in self:
            if rec.state in ('checkout',):
                raise UserError("Cannot cancel a checked-out reservation.")
            if rec.state == 'checkin':
                rec.room_id.state = 'available'
            rec.state = 'cancelled'

    def action_draft(self):
        for rec in self:
            if rec.state != 'cancelled':
                raise UserError(
                    "Only cancelled reservations can be reset to draft."
                )
            rec.state = 'draft'

    def action_view_folio(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Folio',
            'res_model': 'hotel.folio',
            'view_mode': 'form',
            'res_id': self.folio_id.id,
        }

    @api.onchange('checkout_date')
    def _onchange_checkout_date(self):
        if not self.checkout_date and self.checkin_date:
            self.checkout_date = self.checkin_date + relativedelta(days=1)


class HotelServiceLine(models.Model):
    _name = 'hotel.service.line'
    _description = 'Reservation Service Line'
    _order = 'date desc'

    reservation_id = fields.Many2one(
        'hotel.reservation', string='Reservation',
        required=True, ondelete='cascade',
    )
    service_id = fields.Many2one(
        'hotel.service', string='Service', required=True,
    )
    date = fields.Date(
        string='Date', default=fields.Date.today, required=True,
    )
    quantity = fields.Float(string='Quantity', default=1.0, required=True)
    unit_price = fields.Float(string='Unit Price')
    subtotal = fields.Float(
        string='Subtotal', compute='_compute_subtotal', store=True,
    )
    notes = fields.Char(string='Notes')

    @api.depends('quantity', 'unit_price')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.unit_price

    @api.onchange('service_id')
    def _onchange_service_id(self):
        if self.service_id:
            self.unit_price = self.service_id.price
