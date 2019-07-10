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
{
    'name': 'Produzione Terzisti rel.10',
    'version': '0.1',
    'category': 'Generic Modules/Others',
#    'description': """
#Produzione Terzisti
#===================================================
#Gestione della produzione conto terzi rel.10
#""",
    'author': 'Stefano Siccardi @ Creativi Quadrati',
    'website': 'http://www.creativiquadrati.it',
    'license': 'AGPL-3',
    'depends': ['cq_mrp_production_10'],
    'data': [
        'views/product_view.xml',
        'views/mrp_view.xml',
        'views/stock_view.xml',
        'wizard/wizard_stock_view.xml',
        'wizard/multi_transfer_view.xml',
    ],
    'active': False,
    'installable': True
}
