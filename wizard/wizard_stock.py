# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2017 CQ creativiquadrati snc
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError


class cq_wizard_stock(models.TransientModel):

    _name = "cq.wizard.stock"
    _description = "Wizard for MRP order raw material contractors' delivery"

    stock_start_id = fields.Many2one("stock.location", "Ubicazione materie prime")
    dest_id = fields.Many2one("stock.location", "Destinazione materie prime")


    @api.multi
    def get_production_location(self):
        ''' Get source and destination location from the MRP order picking type
        returning them into a dictionary.
        '''
        MrpProduction = self.env['mrp.production']
        Warehouse = self.env['stock.warehouse']

        self.ensure_one() ## It has to be a single record

        production = MrpProduction.browse(self._context.get('active_id', []))
        if production.picking_type_id:
            if production.picking_type_id.default_location_src_id:
                location_id = production.picking_type_id.default_location_src_id.id
            else:
                customerloc, location_id = Warehouse._get_partner_locations()

            if production.picking_type_id.default_location_dest_id:
                location_dest_id = production.picking_type_id.default_location_dest_id.id
            else:
                location_dest_id, supplierloc = Warehouse._get_partner_locations()

            return {'location_id': location_id, 'location_dest_id': location_dest_id}


    @api.multi
    def delivery_product(self):
        ''' Creates the contractor's raw material stock picking.'''

        MrpProduction = self.env['mrp.production']
        StockMove = self.env['stock.move']
        Picking = self.env['stock.picking']
        Location = self.env['stock.location']
        PickingType = self.env['stock.picking.type']
        ModelData = self.env['ir.model.data']

        self.ensure_one() ## It has to be a single record

        production = MrpProduction.browse(self._context.get('active_id', []))

        location = self.stock_start_id ## Contractor's raw material soruce location
        loc_mp = production.location_src_id  ## Contractor's raw material final location

        moves = production.move_raw_ids
        states = ('draft','waiting','confirmed')

        products, products2 = production.get_qty_move_da_fare_e_move_fatti(states)

        picking_types = PickingType.search([
            ('default_location_src_id','=',location.id),
            ('default_location_dest_id','=',loc_mp.id)
        ])


        ## QUESTO E' IL VECCHIO MODO
        #if picking_types:
        #    vals['picking_type_id'] = picking_types._ids[0]
        if not picking_types:
            picking_types = PickingType.search([('code','=','outgoing')])  ## 'internal' or 'outgoing' move?

        # https://stackoverflow.com/questions/36199868/store-value-onchange-new-api-odoo-openerp

        ## Contractor's raw material stock picking values
        # NB: location_id and location_dest_id are required in Odoo10. In order to fill them,
        #    here it's replicated the default assignment schema used in the stock.picking fields
        #    declaration, i.e. using default_location_src_id and default_location_dest_id

        #location_dict = production.get_production_location()
        #location_id, location_dest_id = location_dict.get('location_id', []), location_dict.get('location_dest_id', [])

        vals = {
            'picking_type_id': picking_types._ids[0],
            'location_id': location.id,
            'location_dest_id': loc_mp.id,

            #'location_id': PickingType.browse(self._context.get('default_picking_type_id')).default_location_src_id,
            #'location_dest_id': PickingType.browse(self._context.get('default_picking_type_id')).default_location_dest_id,
        }

        if production.name:
            vals['origin'] = production.name
        if loc_mp.partner_id:
            vals['partner_id'] = loc_mp.partner_id.id

        picking = Picking.create(vals)


        for product_shipping in products:
            ## Control: check for remainders not yet shipped, which would be included
            ## into the new picking
            if products2.get(product_shipping):
                qty = products[product_shipping] - products2[product_shipping]
            else:
                qty = products[product_shipping]

            ## Create a stock.move for each remainder product that hasn't yet shipped to the contractor
            if qty > 0:
                matched_move = False
                for move in moves:
                    if move.product_id == product_shipping:
                        matched_move = True
                        break
                if matched_move:
                    product_ctx = move.product_id.with_context( lang='it_IT' )
                    prodname = product_ctx.name_get()[0][1]
                    prodcode = move.product_id.default_code and move.product_id.default_code or ''

                    values = {}
                    values['product_id'] = move.product_id.id
                    values['product_uom_qty'] = qty
                    values['product_uom'] = move.product_uom.id
                    if prodcode:
                        values['name'] = '[' + move.product_id.default_code + '] ' + prodname
                    else:
                        values['name'] = prodname
                    values['origin'] = move.origin
                    values['procure_method'] = move.procure_method
                    values['location_id'] = location.id
                    values['location_dest_id'] = loc_mp.id
                    values['picking_id'] = picking.id
                    values['price_unit'] = move.price_unit
                    if vals.get('picking_type_id'):
                        values['picking_type_id'] = vals['picking_type_id']
                    if vals.get('partner_id'):
                        values['partner_id'] = vals['partner_id']
                    values['product_packaging'] = move.product_packaging
                    values['out_terz_production_id'] = production.id
                    StockMove.create(values)
        view_id = ModelData.get_object_reference('stock', 'view_picking_form')[1]

        return {
                'type': 'ir.actions.act_window',
                'name': 'Ordine di spedizione',
                'res_model': 'stock.picking',
                'view_mode': 'form',
                'view_type': 'form',
                'view_id': view_id,
                'res_id': picking.id,
                }


    @api.model
    def default_get(self, fields):

        MrpProduction = self.env['mrp.production']
        Location = self.env['stock.location']
        ModelData = self.env['ir.model.data']

        production = MrpProduction.browse(self._context.get('active_id', []))

        if not production:
            raise UserError("Non e' stato possibile identificare l'ordine di produzione collegato a questa azione.")

        product_tmpl = production.product_id.product_tmpl_id

        ## _get_domain_locations:
        ## This is a product.product method, defined in /addons/stock/models/product.py
        ## Parses the context and returns a list of location_ids based on it.
        ## It will return all stock locations records when no parameters are given.
        ## Possible parameters are shop, warehouse, location, force_company, compute_child

        ## Default source stock location:
        ## 1) Looking for the stock.location record ID with default name 'WH/Stock'
        ## 2) Otherwise (multicompnay setup or unavailable "stock_location_stock" record),
        ##      get the first result of product.product's _get_domain_locations method
        wh_stock_exists = False
        wh_stock_location_id = ModelData.get_object_reference('stock', 'stock_location_stock')
        if wh_stock_location_id:
            wh_stock_location_id = wh_stock_location_id[1]
            wh_stock_location = Location.browse(wh_stock_location_id)
            wh_stock_exists = True

        if not wh_stock_exists:
            domain_quant_loc, domain_move_in_loc, domain_move_out_loc = product_tmpl.product_variant_ids._get_domain_locations()
            wh_stock_location_id = domain_quant_loc
            wh_stock_location = Location.search(wh_stock_location_id, limit=1)

        vals = {'dest_id': production.location_src_id.id}
        if wh_stock_location.usage == 'internal':
            vals['stock_start_id'] = wh_stock_location.id
        return vals
