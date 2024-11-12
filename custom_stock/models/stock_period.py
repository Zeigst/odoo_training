from odoo import models, fields, api


class StockPeriod(models.Model):
    _name = 'stock.period'
    _description = 'Stock Period'

    date = fields.Date(string="Date", required=True)
    location_id = fields.Many2one('stock.location', string="Location", required=True)
    stock_quant_period_ids = fields.One2many('stock.quant.period', 'stock_period_id', string="Products")

    @api.model
    def create(self, vals):
        location_id = vals.get('location_id')
        date = vals.get('date')

        stock_quant_period_ids = []
        products = self.env['product.product'].search([])
        for product in products:
            quants = self.env['stock.quant'].search([
                ('product_id', '=', product.id),
                ('location_id', '=', location_id),
                ('in_date', '<=', date)
            ], order='in_date desc', limit=1)
            quantity = sum(quant.quantity for quant in quants)

            stock_quant_period_ids.append((0, 0, {
                'product_id': product.id,
                'quantity': quantity
            }))

        stock_period = super(StockPeriod, self).create({
            'location_id': location_id,
            'date': date,
            'stock_quant_period_ids': stock_quant_period_ids
        })

        return stock_period
