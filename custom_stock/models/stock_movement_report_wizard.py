from odoo import models, fields, api
import xlsxwriter
import base64
from io import BytesIO

class StockMovementReportWizard(models.TransientModel):
    _name = 'stock.movement.report.wizard'
    _description = 'Stock Movement Report Wizard'

    warehouse_id = fields.Many2one('stock.warehouse', string="Warehouse", required=True)
    start_date = fields.Date(string="From Date", required=True)
    end_date = fields.Date(string="To Date", required=True)

    def action_generate_report(self):
        self.ensure_one()

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
                'product': product,
                'start_qty': start_qty,
                'start_value': start_value,
                'received_qty': received_qty,
                'received_value': received_value,
                'delivered_qty': delivered_qty,
                'delivered_value': delivered_value,
                'end_qty': end_qty,
                'end_value': end_value,
            })

        return self._action_export_xlsx(products=report_data)

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


    def _action_export_xlsx(self, products):
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Stock Movement Report')

        worksheet.set_column("A:K", 20)

        # FORMAT ====================
        title_format = workbook.add_format()
        title_format.set_bold()
        title_format.set_font_name('Times New Roman')
        title_format.set_font_size(15)
        title_format.set_align('vcenter')

        heading_format = workbook.add_format()
        heading_format.set_bold()
        heading_format.set_font_name('Times New Roman')
        heading_format.set_font_size(15)
        heading_format.set_align('vcenter')
        heading_format.set_align('center')
        heading_format.set_border(1)

        heading_format_number = workbook.add_format()
        heading_format_number.set_bold()
        heading_format_number.set_font_name('Times New Roman')
        heading_format_number.set_font_size(15)
        heading_format_number.set_align('vcenter')
        heading_format_number.set_align('right')
        heading_format_number.set_border(1)

        normal_format = workbook.add_format()
        normal_format.set_font_name('Times New Roman')
        normal_format.set_font_size(10)
        normal_format.set_align('vcenter')
        normal_format.set_border(1)

        normal_format_number = workbook.add_format()
        normal_format_number.set_font_name('Times New Roman')
        normal_format_number.set_font_size(10)
        normal_format_number.set_align('vcenter')
        normal_format_number.set_align('right')
        normal_format_number.set_border(1)
        # ===========================

        worksheet.write(0, 0, f"Company: {self.env.company.name}", title_format)
        worksheet.write(3, 0, f"{self.warehouse_id.name} Stock Movement Report", title_format)
        worksheet.write(4, 0, f"From {self.start_date} to {self.end_date}", title_format)

        worksheet.merge_range(6, 0, 7, 0, 'No.', heading_format)
        worksheet.merge_range(6, 1, 7, 1, 'Product', heading_format)
        worksheet.merge_range(6, 2, 7, 2, 'UoM', heading_format)
        worksheet.merge_range(6, 3, 6, 4, "Starting Stock", heading_format)
        worksheet.merge_range(6, 5, 6, 6, "Received", heading_format)
        worksheet.merge_range(6, 7, 6, 8, "Removed", heading_format)
        worksheet.merge_range(6, 9, 6, 10, "Final Stock", heading_format)


        lst_char = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        for n_col in range(3):
            for n_row in range(7, 11):
                worksheet.write(n_row, n_col, '', heading_format)
        i = 3
        while i <= 10:
            if i%2 == 0:
                worksheet.write(7, i, 'Value', heading_format)
            else:
                worksheet.write(7, i, 'Quantity', heading_format)
            if i <= 8:
                worksheet.write(8, i, f"({i-2})", heading_format)
            else:
                worksheet.write(8, i, f"({i-2})=({i-8})+({i-6})-({i-4})", heading_format)
            worksheet.write_formula(9, i, f"{{=SUM({lst_char[i]}11:{lst_char[i]}1048576)}}", heading_format_number)
            i += 1

        row = 10
        for n, record in enumerate(products):
            worksheet.write(row, 0, n+1, normal_format_number)
            worksheet.write(row, 1, record["product"].display_name, normal_format)
            worksheet.write(row, 2, record["product"].uom_id.name, normal_format)
            worksheet.write(row, 3, record["start_qty"], normal_format_number)
            worksheet.write(row, 4, record["start_value"], normal_format_number)
            worksheet.write(row, 5, record["received_qty"], normal_format_number)
            worksheet.write(row, 6, record["received_value"], normal_format_number)
            worksheet.write(row, 7, record["delivered_qty"], normal_format_number)
            worksheet.write(row, 8, record["delivered_value"], normal_format_number)
            worksheet.write(row, 9, record["end_qty"], normal_format_number)
            worksheet.write(row, 10, record["end_value"], normal_format_number)
            row += 1

        workbook.close()
        output.seek(0)

        export_data = output.read()
        output.close()

        export_file = base64.b64encode(export_data)
        attachment_id = self.env['ir.attachment'].create({
            'name': 'Stock_Movement_Report.xlsx',
            'type': 'binary',
            'datas': export_file,
            'store_fname': 'Stock_Movement_Report.xlsx',
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment_id.id}?download=true',
            'target': 'self',
        }

