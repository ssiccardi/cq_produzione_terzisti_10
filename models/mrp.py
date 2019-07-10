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
#from odoo.addons.procurement.models import procurement


class MrpProduction(models.Model):

    _inherit = "mrp.production"
#//Eredita mrp.production e aggiunge il legame agli eventuali movimenti al/dal terzista

    out_terz_move_ids = fields.One2many("stock.move", "out_terz_production_id",
            "Spedizione materie prime verso terzista", copy=True,
            help="Elenco dei movimenti di spedizione delle materie prime verso i terzisti.")
    in_terz_move_ids = fields.One2many("stock.move", "in_terz_production_id",
            "Ricezione materie prime da terzista", copy=True,
            help="Elenco dei movimenti di ricezione delle materie prime dai terzisti.")
    ## lav_terz: terzisti in modalita NxTu
    ## spedisci_terz: terzisti in modalita JuGr
    terz_type = fields.Selection([('lav_terz','Lavorato dal terzista'),('spedisci_terz','Spedito al terzista')],
        string="Tipo gestione terzista",
        help=("Serve per impostare il tipo di lavorazione conto terzi: \n"
            "1) 'Lavorato dal terzista': il prodotto necessita di una distinta base "
                "che viene lavorata presso un terzista. \n"
                " Le materie prime vengono spedite manualmente dall'operatore "
                "direttamente sull'ordine di produzione di questo prodotto.\n"
            "2) 'Spedito al terzista': il sistema prepara un movimento di spedizione di questo prodotto verso il terzista "
                " appena viene concluso l'ordine di produzione di questo prodotto. \n"
                "Questo richiede che vengano impostati dei percorsi Routing "
                "per automatizzare la spedizione da e verso terzista e la lavorazione."
            )
    )


#//Gestisce gli spostamenti dei prodotti al / dal terzista

    @api.onchange('product_id', 'picking_type_id', 'company_id')
    def onchange_product_id(self):
        ''' Addictional block of the onchange function triggered only on MRP orders
            of products managed by contractors:
            this method pools contractor's stock locations defined
            on the product template form and put them on the MRP order.
        '''

        res = super(MrpProduction, self).onchange_product_id()

        if self.product_id:
            #if self.product_id.lav_terz and self.product_id.stock_appr_terz_id:
            if self.product_id.terz_type and self.product_id.stock_appr_terz_id:
                if res.get('value', False):
                    res['value']['location_src_id'] = self.product_id.stock_appr_terz_id.id
                else:
                    res['value'] = {'location_src_id': self.product_id.stock_appr_terz_id.id}
            #if self.product_id.lav_terz and self.product_id.stock_terz_id:
            if self.product_id.terz_type and self.product_id.stock_terz_id:
                if res.get('value', False):
                    res['value']['location_dest_id'] = self.product_id.stock_terz_id.id
                else:
                    res['value'] = {'location_dest_id': self.product_id.stock_terz_id.id}
        return res



    @api.model
    def create(self, vals):
        ''' This part of create method should be invoked only when the product 
        on manufacturing has routes which include procurement rules with:
            1) 'procure_method' field set on 'make_to_order'
            2) 'action' field set on 'move'
        A typical example is the 'Make To Order' route, which holds
        some procurement rules named about 'WH Stock -> CustomersMTO'
        or something similar.
        '''

        StockMove = self.env['stock.move']

        Product = self.env['product.product']
        product_id = vals.get('product_id')
        product = Product.browse(product_id)
        if product.terz_type:
            vals['terz_type'] = product.terz_type

        this = super(MrpProduction, self).create(vals)
        

        #prodotto spedito al terzista per la sua lavorazione: riportola sua move ben visibile sul MO
        if this.product_id.terz_type == 'spedisci_terz':
            #product = this.product_id
            out_move_domain = [
                ('product_id','=',product.id),
                ('group_id','=',this.procurement_group_id.id),
                ('raw_material_production_id','=',False),
                ('production_id','=',False),
                ('procure_method','=','make_to_order'),
                ('rule_id','!=',False),
                #('picking_id','!=',False),
            ]
            out_moves = StockMove.search(out_move_domain)

            for move in out_moves:
                if move.picking_type_id.code == 'outgoing':
                    location = move.location_dest_id

                    if not location.partner_id:

                        next_production = move.move_dest_id.raw_material_production_id
                        ctx_lang = self._context.get('lang','it_IT')
                        next_bom_prod = next_production.bom_id.product_tmpl_id.with_context(lang=ctx_lang)
                        next_bom_name = next_bom_prod.name_get()[0][1]
                        if next_production.bom_id.code:
                            next_bom_name = next_bom_name + ' (' + next_production.bom_id.code + ') '

                        raise UserError( ("Compilare il campo 'Proprietario' nel punto di stoccaggio " +
                            "'" + location.complete_name +
                            "' verso cui spedire il prodotto '" + move.product_id.name + 
                            "' necessario per la distinta base '" + 
                            next_bom_name + "' da svolgere in conto terzi.")
                        )
                    move.write({'out_terz_production_id': this.id, 'partner_id': location.partner_id.id})

        else:
            found_shipped = False
            for move_raw in this.move_raw_ids:
                if move_raw.product_id.terz_type == 'spedisci_terz':
                    found_shipped = True
                    break

            if found_shipped:
                in_move_domain = [
                    ('product_id','=',product.id),
                    ('group_id','=',this.procurement_group_id.id),
                    ('raw_material_production_id','=',False),
                    ('production_id','=',False),
                    #('picking_id','!=',False),
                    #('rule_id','!=',False),
                    ('procure_method','=','make_to_order'),
                ]
                in_moves = StockMove.search(in_move_domain)

                for move in in_moves:
                    if move.picking_type_id.code == 'incoming':

                        location = move.location_id
                        if not location.partner_id:

                            ctx_lang = self._context.get('lang','it_IT')
                            bom_prod = this.bom_id.product_tmpl_id.with_context(lang=ctx_lang)
                            bom_name = bom_prod.name_get()[0][1]
                            if this.bom_id.code:
                                bom_name = bom_name + ' (' + this.bom_id.code + ') '

                            raise UserError( ("Compilare il campo 'Proprietario' nel punto di stoccaggio " +
                                "'" + location.complete_name +
                                "' da cui ricevere il prodotto '" + move.product_id.name + 
                                "' lavorato nella distinta base '" + 
                                bom_name + "' da svolgere in conto terzi.")
                            )
                        move.write({'in_terz_production_id': this.id, 'partner_id': location.partner_id.id,})

        return this


#//Controlla le giacenze dei componenti presso il terzista e propone la picking list dei materiali da inviare

    @api.multi
    def get_qty_move_da_fare_e_move_fatti(self, states):
        ''' This method gets an MRP order, checking its raw material stock moves and
        its contractor's raw material stock moves. It returns two dictionaries:
        @ raw material products quantity
        @ contractor's raw material products quantity
        '''
        ## Orderpoints are product reordiring rules
        Orderpoint = self.env['stock.warehouse.orderpoint']

        self.ensure_one() ## It has to be a single record
        ## Raw material stock moves, Raw material towards contractor stock moves
        moves, moves_done = self.move_raw_ids, self.out_terz_move_ids
        ## Destination of the contractor's raw material, which matches the MRP order source location
        loc_dest = self.location_src_id

        ## Control 1: checking through raw material stock moves, returning a dictionary
        ## key: product
        ##      - which doesn't require a contractor production
        ##      - which doesn't have any reordering rule for the MRP order source location
        ## value: raw material product quantity
        products = {}
        for move in moves:
            product_tmpl = move.product_id.product_tmpl_id
            orderpoints = Orderpoint.search([('product_id','=', move.product_id.id)])
            mov_autom = False
            for op in orderpoints:
                if op.location_id == loc_dest:
                    mov_autom = True
            # states = ('draft','waiting','confirmed')
            if (move.state in states and not product_tmpl.terz_type == 'lav_terz' and not mov_autom):
                if products.get(move.product_id):
                    products[move.product_id] += move.product_uom_qty
                else:
                    products[move.product_id] = move.product_uom_qty

        ## Control 2: checking through contractor's raw material stock moves, returning a dictionary
        ## key: product record
        ## value: contractor's raw material product quantity
        products2 = {}
        for move_done in moves_done:
           if products2.get(move_done.product_id):
              products2[move_done.product_id] += move_done.product_uom_qty
           else:
              products2[move_done.product_id] = move_done.product_uom_qty

        return products, products2


    @api.multi
    def action_controllo_spedisci_materie(self):
        ''' Checks for raw material required shipping to contractors
        and returns the shipping wizard popup.
        '''
        self.ensure_one() ## Ensuring the method takes one only record as input

        loc_mp = self.location_src_id
#        if not self:
#            raise UserError(_("Context error."))
        ## Control: requiring a manufacturing product with contractor's stock locations
        if not self.product_id.stock_appr_terz_id or not self.product_id.stock_terz_id:
            raise UserError(
                ("Il prodotto non è impostato per essere lavorato da un terzista! \n"
                "Controlla le sue impostazioni d'inventario.")
            )

        moves = self.move_raw_ids ## MRP order raw material stock moves
        states = ('draft','waiting','confirmed')

        ## Look for raw material stock moves requiring delivery
        MP_da_spedire = False
        for move in moves:
            if move.state in states:
                MP_da_spedire = True
                break
        if not MP_da_spedire:
            raise UserError("Tutte le materie prime sono disponibili.")

        ## Returnig two dictionaries:
        ##  products --> key: raw material product.product record
        ##               value: raw material product quantity
        ##  products2 --> key: contractor's raw material product.product record
        ##               value: contractor's raw material product quantity

        products, products2 = self.get_qty_move_da_fare_e_move_fatti(states)
        j=0
        ## Stops execution if the contractor's raw material stock moves table is already filled
        for i in products:
            if products2.get(i) and products[i] == products2[i]:
                j+=1
        if j == len(products):
            raise UserError("Tutte le materie prime sono già in fase di spedizione.")

        return {
                'type': 'ir.actions.act_window',
                'name': 'Spedizione materie prime',
                'res_model': 'cq.wizard.stock',
                'view_mode': 'form',
                'view_type': 'form',
                'target':'new',
                }



    @api.multi
    def write(self, vals):

        StockMove = self.env['stock.move']

        res = super(MrpProduction, self).write(vals)

        for production in self:
            if production.state in ('confirmed','planned','progress'):
                if vals.get('location_dest_id'):
                    for move_line in production.move_finished_ids:
                        move_line.sudo().write({'location_dest_id': vals.get('location_dest_id')})
                if production.state == 'confirmed':
                    if vals.get('location_src_id'):
                        for move_line in production.move_raw_ids:
                            if move_line.state in ('waiting', 'assigned'):
                                move_line.do_unreserve()
                            move_line.sudo().write({'location_id': vals.get('location_src_id')})

        ''' non si può cambiare brutalmente la quantità di movimenti non in stato bozza
            if production.state not in ('cancel','done'):
                for move in production.move_lines:
                    if move.state in ('waiting','confirmed'):

                        mrp_prod_prod_line_id = mrp_prod_prod_line_obj.search(cr,uid,[('production_id','=',move.raw_material_production_id.id),('product_id','=',move.product_id.id)])
                        if mrp_prod_prod_line_id:
                            if len(mrp_prod_prod_line_id)>1:
                            #se nei prodotti programmati ci sono su più righe prodotti uguali li raggruppa
                                for ids in mrp_prod_prod_line_id[1:]:
                                    mrp_prod_prod_line_obj.unlink(cr,uid,ids)
                                mrp_prod_prod_line_id=mrp_prod_prod_line_id[0]   
                            ## Il prodotto è già stato programmato: aggiorno la quantità nella tabella prodotti programmati
                            if self.pool.get('stock.move').search(cr,uid,[('raw_material_production_id','=',move.raw_material_production_id.id),('product_id','=',move.product_id.id),('id','!=',move.id)]):
                                mrp_prod_prod_line = mrp_prod_prod_line_obj.browse(cr,uid,mrp_prod_prod_line_id,context=context)
                                mrp_prod_prod_line.product_qty = sum(all_move.product_qty for all_move in production.move_lines
                                    if (all_move.raw_material_production_id.id==move.raw_material_production_id.id and all_move.product_id.id==move.product_id.id))
                            else:
                                ## Sto modificando la quantità del prodotto prima dell'elaborazione al suo primo inserimento
                                mrp_prod_prod_line_obj.write(cr,uid,mrp_prod_prod_line_id,{'product_qty': move.product_qty},context=context)
                        else:
                            values={}
                            values['product_id'] = move.product_id.id
                            values['product_qty'] = move.product_qty
                            values['product_uom'] = move.product_uom.id
                            values['product_uos_qty'] = move.product_uos_qty
                            values['product_uos'] = move.product_uos.id
                            values['name'] = move.product_id.name
                            values['production_id'] = move.raw_material_production_id.id
                            mrp_prod_prod_line_obj.create(cr,uid,values,context=context)
                        if move.name != production.name:
                            move.name = production.name
                        if not move.origin or move.origin != production.name:
                            move.origin = production.name
                        if any(route.name == 'Make To Order' for route in move.product_id.route_ids):
                            move.procure_method = 'make_to_order'
                        else:
                            move.procure_method = 'make_to_stock'
        '''
        return res
