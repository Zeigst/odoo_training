from odoo import models, fields, api


class StockQuantPeriod(models.Model):
    _name = 'stock.quant.period'
    _description = 'Stock Quant Period'

    product_id = fields.Many2one('product.product', string="Product", required=True)
    quantity = fields.Float(string="Quantity", required=True)
    stock_period_id = fields.Many2one('stock.period', string="Stock Period", required=True)
