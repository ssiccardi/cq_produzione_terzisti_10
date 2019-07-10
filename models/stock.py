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


class StockMove(models.Model):

    _inherit = "stock.move"
#//Eredita stock.move e aggiunge link a eventuale ordine di produzione presso un terzista

    ## Check here for how to implement one2many-field's domain
    ## https://docs.google.com/document/d/11mDHCckHLTmmTEPcPCA-6sE_c-OpI4_mV7-IQgRB7Pc/edit#    

    out_terz_production_id = fields.Many2one("mrp.production",
        string="Ordine di produzione legato alla spedizione verso terzista",
        help=("Ordine di produzione per cui questo movimento rappresenta la spedizione \n"
            "di materie prime verso il terzista.")
    )
    in_terz_production_id = fields.Many2one("mrp.production",
        string="Ordine di produzione legato alla ricezione dal terzista",
        help=("Ordine di produzione per cui questo movimento rappresenta la ricezione \n"
            "del prodotto lavorato dal terzista.")
    )


    #~ @api.model
    #~ def create(self, vals):
        #~ ''' This part of create method should be invoked only when the product 
        #~ on manufacturing has routes which include procurement rules with:
            #~ 1) 'procure_method' field set on 'make_to_order'
            #~ 2) 'action' field set on 'move'
        #~ A typical example is the 'Make To Order' route, which holds
        #~ some procurement rules named about 'WH Stock -> CustomersMTO'
        #~ or something similar.
        #~ '''
#~ 
        #~ this = super(StockMove, self).create(vals)
        #~ #if this.raw_material_production_id:
#~ 
        #~ #if this.raw_material_production_mp and this.procure_method == 'make_to_order':
        #~ #if (this.raw_material_production_mp and
        #~ #    this.rule_id.procure_method == 'make_to_order' and
        #~ #    this.rule_id.action == 'move'):
        #~ if (this.out_terz_production_id and
            #~ this.product_id.terz_type == 'spedisci_terz'
        #~ ):
            #~ production = this.out_terz_production_id
            #~ next_production = False
            #~ for move_finished in production.move_finished_ids:
                #~ next_production = move_finished.move_dest_id.raw_material_production_id
                #~ if next_production:
                    #~ break
            #~ if not next_production:
                #~ next_production = production
#~ 
            #~ product = this.product_id
            #~ location = this.location_dest_id
            #~ if production.procurement_group_id != this.group_id:
                #~ return this
#~ 
            #~ print 'A5'
            #~ if not location.partner_id:
                #~ raise UserError( ("Compilare il campo 'Proprietario' nel punto di stoccaggio " +
                    #~ "'" + location.complete_name +
                    #~ "' verso cui spedire il prodotto '" + product.name + 
                    #~ "' necessario per l'ordine di produzione " + 
                    #~ next_production.name + " in conto terzi.")
                #~ )
            #~ print 'A6'
#~ 
        #~ elif (this.in_terz_production_id):
            #~ production = this.in_terz_production_id
            #~ product = this.product_id
            #~ location = this.location_id
            #~ if production.procurement_group_id != this.group_id:
                #~ return this
#~ 
            #~ print 'A7'
            #~ if not location.partner_id:
                #~ raise UserError( ("Compilare il campo 'Proprietario' nel punto di stoccaggio " +
                    #~ "'" + location.complete_name +
                    #~ "' da cui ricevere il prodotto '" + product.name + 
                    #~ "' necessario per l'ordine di produzione " + 
                    #~ production.name + " in conto terzi.")
                #~ )
            #~ print 'A8'
#~ 
        #~ else:
            #~ return this
#~ 
        #~ ## Checking that all the product fields required by
        #~ ## the contractor's shipping might be filled
#~ 
        #~ #if this.partner_id != product.stock_appr_terz_id.partner_id:
        #~ #    this.write({'partner_id': product.stock_appr_terz_id.partner_id.id,})
        #~ if not this.partner_id or this.partner_id != location.partner_id:
            #~ this.write({'partner_id': location.partner_id.id,})
#~ 
        #~ #if this.picking_id.partner_id != product.stock_appr_terz_id.partner_id:
        #~ #    this.picking_id.write({'partner_id': product.stock_appr_terz_id.partner_id.id,})
        #~ if not this.picking_id.partner_id or this.picking_id.partner_id != location.partner_id:
            #~ this.picking_id.write({'partner_id': location.partner_id.id,})
        #~ return this


class PackOperation(models.Model):

    _inherit = "stock.pack.operation"

#//Eredita stock.pack.operation
#//Metodo per compilazione automatica delle quantita e lotti nelle stock.pack.operation

    @api.multi
    def auto_assign_qty_lot(self):
        ''' This method makes the pack operation qty_done field complete (i.e. like the forecasted one).
        Two possible ways for that:
            1) pack requiring lots assignment (lots_visible true):
                it simulates the user task over each pack operation lot through
                the 'action_add_quantity' method.
                'action_add_quantity' automatically fills the pack operation qty_done field
                NB: each pack operation lot is already linked to a specific lot,
                previously chosen by the user or by the system
            2) pack not requiring lots
        '''
        for op in self:
            if op.lots_visible:
                for op_lot in op.pack_lot_ids:
                    remaining_qty = op_lot.qty_todo - op_lot.qty
                    op_lot.action_add_quantity(remaining_qty)
            else:
                op.write({'qty_done': op.product_qty})
        return
