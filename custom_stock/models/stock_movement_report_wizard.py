from odoo import models, fields, api

class StockMovementReportWizard(models.TransientModel):
    _name = 'stock.movement.report.wizard'
    _description = 'Stock Movement Report Wizard'

    warehouse_id = fields.Many2one('stock.warehouse', string="Warehouse", required=True)
    start_date = fields.Date(string="From Date", required=True)
    end_date = fields.Date(string="To Date", required=True)

    def action_generate_report(self):
        self.ensure_one()
        StockMovementReport = self.env['stock.movement.report']
        StockMovementReport.search([]).unlink()

        locations = self.warehouse_id.view_location_id.child_ids
        products = self.env['product.product'].search([])
        
        report_data = []
        for product in products:
            start_qty, start_value = self._get_beginning_balance(product, locations, self.start_date)
            received_qty, received_value = self._get_movement_data(product, locations, self.start_date, self.end_date, 'in')
            delivered_qty, delivered_value = self._get_movement_data(product, locations, self.start_date, self.end_date, 'out')
            end_qty = start_qty + received_qty - delivered_qty
            end_value = start_value + received_value - delivered_value

            report_data.append({
                'warehouse_id': self.warehouse_id.id,
                'start_date': self.start_date,
                'end_date': self.end_date,
                'product_id': product.id,
                'uom_id': product.uom_id.id,
                'start_qty': start_qty,
                'start_value': start_value,
                'received_qty': received_qty,
                'received_value': received_value,
                'delivered_qty': delivered_qty,
                'delivered_value': delivered_value,
                'end_qty': end_qty,
                'end_value': end_value,
            })

        for data in report_data:
            StockMovementReport.create(data)

        return {
            'type': 'ir.actions.act_window',
            'name': 'Stock Movement Report',
            'view_mode': 'tree',
            'res_model': 'stock.movement.report',
            'target': 'main',
        }

    def _get_beginning_balance(self, product, locations, start_date):
        quants = self.env['stock.quant'].search([
            ('product_id', '=', product.id),
            ('location_id', 'in', locations.ids),
            ('in_date', '<=', start_date)
        ], order='in_date desc', limit=1)

        start_qty = sum(quant.quantity for quant in quants)
        start_value = sum(quant.quantity * quant.product_id.standard_price for quant in quants)
        return start_qty, start_value

    def _get_movement_data(self, product, locations, start_date, end_date, move_type):
        domain = [
            ('product_id', '=', product.id),
            ('state', '=', 'done'),
            ('date', '>=', start_date),
            ('date', '<=', end_date),
            ('location_dest_id' if move_type == 'in' else 'location_id', 'in', locations.ids)
        ]
        moves = self.env['stock.move'].read_group(
            domain,
            ['product_uom_qty'],
            []
        )
        qty = sum(move['product_uom_qty'] for move in moves)
        value = sum(move['product_uom_qty'] * product.standard_price for move in moves)

        return qty, value
