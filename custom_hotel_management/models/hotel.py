from odoo import api,fields,models
from odoo.exceptions import ValidationError
from datetime import date

class HotelRoom(models.Model):
    _name = 'hotel.room'
    _description = 'Hotel Room'
    _inherit = ['mail.thread','mail.activity.mixin']
    _order = 'name asc'

    name = fields.Char(string='Room Number',tracking=True)
    room_type = fields.Selection([
        ('single','Single'),
        ('double','Double'),
        ('suite','Suite'),
        ('deluxe','Deluxe')
    ],string='Room Type',tracking=True,default='single')
    floor = fields.Integer(string='Floor',default=1)
    capacity = fields.Integer(string='Capacity',default=1)
    price_per_night = fields.Float(string='Price Per Night',tracking=True)
    amenities = fields.Text(string='Amenities')
    state = fields.Selection([
        ('available','Available'),
        ('occupied','Occupied'),
        ('maintenance','Maintenance')
    ],string='Maintenance',defautl='available',tracking=True)
    booking_ids = fields.One2many('hotel.booking','room_id',string='Booking')
    booking_count = fields.Integer(string='Booking Count',compute = '_compute_booking_count')
    active = fields.Boolean(string='Active',default=True)
    image = fields.Image(string='Image',max_width=1024,max_height=1024)

    _sql_constraints = [
        ('unique_name','UNIQUE(name)','Room number must be unique'),
        ('price_pos','CHECK(price >= 0)','Price must be greater than zero'),
        ('capacity_pos','CHECK(capacity >= 0)','Capacity must be greater than zero')
    ]

    @api.depends('booking_ids')
    def _compute_booking_count(self):
        for rec in self:
            rec.booking_count = len(rec.booking_ids)

    def action_available(self):
        self.write({'state':'available'})

    def action_maintenance(self):
        self.write({'state':'maintenance'})

    def action_view_booking(self):
        self.ensure_one()
        return {
            'type':'ir.actions.act_window',
            'name':'Bookings',
            'res_model':'hotel.booking',
            'view_mode':'list,form',
            'domain':[('room_id','=',self.id)],
            'context':{'default_room_id':self.id},
        }