# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError


class HotelFolio(models.Model):
    _name = 'hotel.folio'
    _description = 'Hotel Folio'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'

    name = fields.Char(
        string='Folio No.', required=True, readonly=True,
        default='New', copy=False, tracking=True,
    )
    reservation_id = fields.Many2one(
        'hotel.reservation', string='Reservation',
        required=True, tracking=True,
    )
    guest_id = fields.Many2one(
        'hotel.guest', string='Guest', required=True, tracking=True,
    )
    partner_id = fields.Many2one(
        'res.partner', string='Invoice Contact',
        related='guest_id.partner_id', store=True,
    )
    room_id = fields.Many2one(
        'hotel.room', string='Room', required=True,
    )
    room_type_id = fields.Many2one(
        'hotel.room.type', string='Room Type',
        related='room_id.room_type_id', store=True,
    )

    # Dates
    checkin_date = fields.Datetime(string='Check-in Date')
    checkout_date = fields.Datetime(string='Check-out Date')
    duration = fields.Integer(
        string='Duration (Nights)',
        related='reservation_id.duration', store=True,
    )

    # Charges
    room_charge = fields.Float(
        string='Room Charge',
        related='reservation_id.total_room_charge', store=True,
    )
    service_charge = fields.Float(
        string='Service Charge',
        related='reservation_id.total_service_charge', store=True,
    )
    tax_amount = fields.Float(
        string='Tax Amount',
        compute='_compute_tax_amount', store=True,
    )
    tax_rate = fields.Float(string='Tax Rate (%)', default=5.0)
    total_amount = fields.Float(
        string='Total Amount',
        compute='_compute_total_amount', store=True,
    )
    paid_amount = fields.Float(string='Paid Amount', default=0.0, tracking=True)
    balance = fields.Float(
        string='Balance',
        compute='_compute_balance', store=True,
    )

    # State
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True, required=True)

    # Invoice
    invoice_id = fields.Many2one('account.move', string='Invoice', copy=False)
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('card', 'Credit/Debit Card'),
        ('bank', 'Bank Transfer'),
        ('online', 'Online Payment'),
        ('other', 'Other'),
    ], string='Payment Method')

    notes = fields.Text(string='Notes')
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one(
        'res.currency', string='Currency',
        related='company_id.currency_id', store=True,
    )

    # -------------------------------------------------------------------------
    # Compute
    # -------------------------------------------------------------------------
    @api.depends('room_charge', 'service_charge', 'tax_rate')
    def _compute_tax_amount(self):
        for folio in self:
            folio.tax_amount = (
                (folio.room_charge + folio.service_charge) * folio.tax_rate / 100
            )

    @api.depends('room_charge', 'service_charge', 'tax_amount')
    def _compute_total_amount(self):
        for folio in self:
            folio.total_amount = (
                folio.room_charge + folio.service_charge + folio.tax_amount
            )

    @api.depends('total_amount', 'paid_amount')
    def _compute_balance(self):
        for folio in self:
            folio.balance = folio.total_amount - folio.paid_amount

    # -------------------------------------------------------------------------
    # CRUD
    # -------------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'hotel.folio'
                ) or 'New'
        return super().create(vals_list)

    # -------------------------------------------------------------------------
    # Actions
    # -------------------------------------------------------------------------
    def action_confirm(self):
        for folio in self:
            if folio.state != 'draft':
                raise UserError("Only draft folios can be confirmed.")
            folio.state = 'confirmed'

    def action_pay(self):
        for folio in self:
            if folio.state not in ('confirmed', 'draft'):
                raise UserError("Cannot process payment for this folio.")
            folio.paid_amount = folio.total_amount
            folio.state = 'paid'

    def action_cancel(self):
        for folio in self:
            if folio.state == 'paid':
                raise UserError("Cannot cancel a paid folio.")
            folio.state = 'cancelled'

    def action_create_invoice(self):
        """Create an account.move (invoice) from the folio."""
        self.ensure_one()
        if self.invoice_id:
            raise UserError("Invoice already created for this folio.")

        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [
                (0, 0, {
                    'name': f"Room Charge - {self.room_id.name} "
                            f"({self.duration} nights)",
                    'quantity': self.duration,
                    'price_unit': self.reservation_id.price_per_night,
                }),
            ],
        }
        # Add service lines
        for sline in self.reservation_id.service_line_ids:
            invoice_vals['invoice_line_ids'].append(
                (0, 0, {
                    'name': sline.service_id.name,
                    'quantity': sline.quantity,
                    'price_unit': sline.unit_price,
                })
            )

        invoice = self.env['account.move'].create(invoice_vals)
        self.invoice_id = invoice
        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoice',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': invoice.id,
        }

    def action_view_invoice(self):
        self.ensure_one()
        if not self.invoice_id:
            raise UserError("No invoice found for this folio.")
        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoice',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': self.invoice_id.id,
        }
