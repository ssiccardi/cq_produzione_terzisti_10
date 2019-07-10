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


class CQMultiTransfer(models.TransientModel):

    _name = "cq.multi.transfer"
    _description = "Wizard for transfer multiple pickings at once"

#//Aggiunge punto menu "Movimenti verso Terzisti" e un'azione per trasferimento multiplo dei picking

    @api.multi
    def _get_picking_ids(self):
        return self.env['stock.picking'].browse(self.env.context['active_ids'])

    picking_ids = fields.Many2many(
        comodel_name="stock.picking",
        string="Movimenti da trasferire",
        relation="stock_picking_multi_transfer_rel",
        column1="wizard_id", column2="picking_id", copy=True,
        default=_get_picking_ids
        #help=("Elenco dei soli lotti/SN effettivamente disponibili per questo SN, ovvero: \n"
        #    "1) componente con quantita sufficiente per produrre ALMENO un SN \n"
        #    "2) disponibilita al punto 1 nel punto di stoccaggio previsto dall'ordine di "
        #    " di produzione collegato al SN da produrre \n"
        #    "3) i quanti disponibili si intendono non ancora riservati per altri movimenti"
        #)
    )


    @api.multi
    def do_multi_transfer(self):
        ''' Transfer multiple pickings at once.
        "States" are the picking states which cause the 'do_new_transfer'
        (Validate Transfer) button to be visible (look at 'view_picking_form' view form).
        So here we want to replicate this behaviour enabling the method
        only when all the pickings are in those states
        '''
        Picking = self.env['stock.picking']
        states = ['draft', 'partially_available', 'assigned']

        self.ensure_one()
        for picking in self.picking_ids:
            if picking.state not in states:
                raise UserError(
                    ("E' possibile trasferire solamente movimenti nei seguenti stati: \n"
                    "Bozza \n Parzialmente Disponibile \n Disponibile \n")
                )
            ## Assigning lots and quantities on pack operations and pack operation lots
            picking.pack_operation_product_ids.auto_assign_qty_lot()

        self.picking_ids.do_new_transfer()
        return
