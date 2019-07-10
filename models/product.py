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


class ProductTemplate(models.Model):

    _inherit = "product.template"
#//Eredita product.template
#//Imposta il terzista e il tipo di spedizione componenti (automatico o manuale)

    ## lav_terz: terzisti in modalita NT
    ## spedisci_terz: terzisti in modalita JG
    terz_type = fields.Selection([('lav_terz','Lavorato dal terzista'),('spedisci_terz','Spedito al terzista')],
        string="Tipo gestione terzista",
        help=("Serve per impostare il tipo di lavorazione conto terzi: \n"
            "1) 'Lavorato dal terzista (NT)': il prodotto necessita di una distinta base "
                "che viene lavorata presso un terzista. \n"
                " Le materie prime vengono spedite manualmente dall'operatore "
                "direttamente sull'ordine di produzione di questo prodotto.\n"
            "2) 'Spedito al terzista' (JG): il sistema prepara un movimento di spedizione di questo prodotto verso il terzista "
                " appena viene concluso l'ordine di produzione di questo prodotto. \n"
                "Questo richiede che vengano impostati dei percorsi Routing "
                "per automatizzare la spedizione da e verso terzista e la lavorazione."
            )
    )
    stock_appr_terz_id = fields.Many2one("stock.location", "Luogo Terzista",
        help="Ubicazione materie prime dell'ordine di produzione.")
    stock_terz_id = fields.Many2one("stock.location", "Punto Spediz. Terzista",
        help="Ubicazione prodotti finiti dell'ordine di produzione.")
#    terz_id = fields.Many2one('res.partner', 'Nome Terzista',
#        help = ("Compilare con il nome del terzista presso il quale spedire il prodotto per lavorazione conto terzi. \n"
#            "Dovrebbe essere il fornitore presso il quale e' posizionato \n"
#            "il punto di stoccaggio scelto nel campo 'Luogo Terzista'")
#        )


    @api.onchange('terz_type', 'stock_appr_terz_id', 'stock_appr_terz_id')
    def app_stock_terz(self):
        ''' When the field related to the contractor's supply stock location is empty,
            it's filled like with the same value set on the contractor stock location
            field located on the manufactured product's form
        '''

        if self.terz_type == 'lav_terz':
            if self.stock_terz_id and not self.stock_appr_terz_id:
                return {'value': {'stock_appr_terz_id': self.stock_terz_id}}
            return {}
        else:
            return {'value': {'stock_appr_terz_id': False,
                              'stock_terz_id': False,
                              #'terz_id': False,
                              },
                    }


    @api.onchange('terz_type')
    def delete_stock(self):
        ''' If the contractor supply stock location is empty, it would be filled
            as the contractor stock location for manufactured products
        '''
        if self.terz_type != 'lav_terz':
            return {'value': {'stock_appr_terz_id': False,
                              'stock_terz_id':False,
                              },
                    }
        return {}
