# -*- coding: utf-8 -*-
# © 2011 Pexego Sistemas Informáticos (<http://www.pexego.es>)
# © 2015 Avanzosc (<http://www.avanzosc.es>)
# © 2015 Pedro M. Baeza (<http://www.serviciosbaeza.com>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp.osv import fields, osv
from openerp import tools
from openerp.tools.translate import _


class res_users(osv.osv):
    _inherit = "res.users"
    
    def _get_cso_group(self, cr, uid, ids, name, arg, context=None):
        res = {}
        all_groups=self.pool.get('res.groups')
        g_ids = all_groups.search(cr,uid,[('name','=','Customer Service Officer')])
        if g_ids:
            for record in self.browse(cr, uid, ids, context=context):
                if g_ids[0] in record.groups_id.ids:
                    res[record.id] = True
        return res

    def _get_manager_group(self, cr, uid, ids, name, arg, context=None):
        res = {}
        all_groups=self.pool.get('res.groups')
        manager_ids = all_groups.search(cr,uid,[('name','=','Operation Manager')])
        if manager_ids:
            for record in self.browse(cr, uid, ids, context=context):
                if manager_ids[0] in record.groups_id.ids:
                    res[record.id] = True
        return res
    
    _columns = {
      'cso' : fields.function(_get_cso_group,type='boolean',String="CSO Group ID",store=True),
      'manager_group_id':fields.function(_get_manager_group,type='boolean',String="Operation Manager Group ID",store=True),
      'district_ids': fields.many2many('maw.district', 'user_operations_rel', 'user_id','operation_id', 'Customer Service Officers'),
    }
