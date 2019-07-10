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


class ProcurementOrder(models.Model):

    _inherit = 'procurement.order'
#//Eredita procurement.order per usare come punti di arrivo/partenza quelli del terzista se definiti


    #@api.multi
    def _prepare_mo_vals(self, bom):
        ''' Replace the procurement order stock locations with those defined on the product
        '''
        res = super(ProcurementOrder, self)._prepare_mo_vals(bom = bom)
        product_tmpl = self.product_id.product_tmpl_id
        #if product_tmpl.stock_appr_terz_id and product_tmpl.lav_terz:
        if product_tmpl.stock_appr_terz_id and product_tmpl.terz_type:
            location_src_id = product_tmpl.stock_appr_terz_id.id
            res['location_src_id'] = location_src_id
        #if product_tmpl.stock_terz_id and product_tmpl.lav_terz:
        if product_tmpl.stock_terz_id and product_tmpl.terz_type:
            location_dest_id = product_tmpl.stock_terz_id.id
            res['location_dest_id'] = location_dest_id
        return res
