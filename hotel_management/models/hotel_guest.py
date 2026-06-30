# -*- coding: utf-8 -*-
from odoo import models, fields, api


class HotelGuest(models.Model):
    _name = 'hotel.guest'
    _description = 'Hotel Guest'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'
    _rec_name = 'display_name'

    name = fields.Char(string='Guest Name', required=True, tracking=True)
    display_name = fields.Char(
        string='Display Name', compute='_compute_display_name', store=True,
    )
    partner_id = fields.Many2one('res.partner', string='Related Contact')
    guest_type = fields.Selection([
        ('individual', 'Individual'),
        ('company', 'Company'),
    ], string='Guest Type', default='individual', required=True)
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ], string='Gender')
    date_of_birth = fields.Date(string='Date of Birth')
    id_type = fields.Selection([
        ('passport', 'Passport'),
        ('nrc', 'NRC / National ID'),
        ('driving_license', 'Driving License'),
        ('other', 'Other'),
    ], string='ID Type', default='passport')
    id_number = fields.Char(string='ID Number', tracking=True)
    nationality = fields.Many2one('res.country', string='Nationality')

    # Contact Info
    email = fields.Char(string='Email')
    phone = fields.Char(string='Phone', tracking=True)
    mobile = fields.Char(string='Mobile')
    street = fields.Char(string='Street')
    street2 = fields.Char(string='Street2')
    city = fields.Char(string='City')
    state_id = fields.Many2one('res.country.state', string='State')
    zip = fields.Char(string='ZIP')
    country_id = fields.Many2one('res.country', string='Country')

    # History
    reservation_ids = fields.One2many(
        'hotel.reservation', 'guest_id', string='Reservations',
    )
    reservation_count = fields.Integer(
        string='Reservation Count',
        compute='_compute_reservation_count',
    )
    total_spent = fields.Float(
        string='Total Spent',
        compute='_compute_total_spent',
    )
    vip = fields.Boolean(string='VIP Guest', default=False, tracking=True)
    notes = fields.Text(string='Internal Notes')
    image = fields.Binary(string='Photo', attachment=True)
    active = fields.Boolean(string='Active', default=True)

    @api.depends('name', 'phone')
    def _compute_display_name(self):
        for guest in self:
            if guest.phone:
                guest.display_name = f"{guest.name} ({guest.phone})"
            else:
                guest.display_name = guest.name

    @api.depends('reservation_ids')
    def _compute_reservation_count(self):
        for guest in self:
            guest.reservation_count = len(guest.reservation_ids)

    @api.depends('reservation_ids.folio_id.total_amount')
    def _compute_total_spent(self):
        for guest in self:
            guest.total_spent = sum(
                guest.reservation_ids.mapped('folio_id.total_amount')
            )

    @api.model
    def create(self, vals):
        """Auto-create related partner if not provided."""
        guest = super().create(vals)
        if not guest.partner_id:
            partner = self.env['res.partner'].create({
                'name': guest.name,
                'email': guest.email,
                'phone': guest.phone,
                'mobile': guest.mobile,
                'street': guest.street,
                'street2': guest.street2,
                'city': guest.city,
                'state_id': guest.state_id.id if guest.state_id else False,
                'zip': guest.zip,
                'country_id': guest.country_id.id if guest.country_id else False,
            })
            guest.partner_id = partner
        return guest
