# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

from osv import fields, osv
import addons

class res_partner_contact(osv.osv):
    """ Partner Contact """

    _name = "res.partner.contact"
    _description = "Contact"

    def _main_job(self, cr, uid, ids, fields, arg, context=None):
        """
            @param self: The object pointer
            @param cr: the current row, from the database cursor,
            @param uid: the current user’s ID for security checks,
            @param ids: List of partner contact’s IDs
            @fields: Get Fields
            @param context: A standard dictionary for contextual values
            @param arg: list of tuples of form [(‘name_of_the_field’, ‘operator’, value), ...]. """
        res = dict.fromkeys(ids, False)

        res_partner_job_obj = self.pool.get('res.partner.job')
        all_job_ids = res_partner_job_obj.search(cr, uid, [])
        all_job_names = dict(zip(all_job_ids, res_partner_job_obj.name_get(cr, uid, all_job_ids, context=context)))

        for contact in self.browse(cr, uid, ids, context=context):
            if contact.job_ids:
                res[contact.id] = all_job_names.get(contact.job_ids[0].id, False)

        return res

    _columns = {
        'name': fields.char('Last Name', size=64, required=True),
        'first_name': fields.char('First Name', size=64),
        'mobile': fields.char('Mobile', size=64),
        'title': fields.many2one('res.partner.title','Title'),
        'website': fields.char('Website', size=120),
        'lang_id': fields.many2one('res.lang', 'Language'),
        'job_ids': fields.one2many('res.partner.job', 'contact_id', 'Functions and Addresses'),
        'country_id': fields.many2one('res.country','Nationality'),
        'birthdate': fields.date('Birth Date'),
        'active': fields.boolean('Active', help="If the active field is set to False,\
                 it will allow you to hide the partner contact without removing it."),
        'partner_id': fields.related('job_ids', 'address_id', 'partner_id', type='many2one',\
                         relation='res.partner', string='Main Employer'),
        'function': fields.related('job_ids', 'function', type='char', \
                                 string='Main Function'),
        'job_id': fields.function(_main_job, type='many2one',\
                                 relation='res.partner.job', string='Main Job'),
        'email': fields.char('E-Mail', size=240),
        'comment': fields.text('Notes', translate=True),
        'photo': fields.binary('Photo'),

    }

    def _get_photo(self, cr, uid, context=None):
        photo_path = addons.get_module_resource('base_contact', 'images', 'photo.png')
        return open(photo_path, 'rb').read().encode('base64')

    _defaults = {
        'photo' : _get_photo,
        'active' : lambda *a: True,
    }

    _order = "name,first_name"

    def name_get(self, cr, user, ids, context=None):

        """ will return name and first_name.......
            @param self: The object pointer
            @param cr: the current row, from the database cursor,
            @param user: the current user’s ID for security checks,
            @param ids: List of create menu’s IDs
            @return: name and first_name
            @param context: A standard dictionary for contextual values
        """

        if not len(ids):
            return []
        res = []
        for contact in self.browse(cr, user, ids, context=context):
            _contact = ""
            if contact.title:
                _contact += "%s "%(contact.title.name)
            _contact += contact.name or ""
            if contact.name and contact.first_name:
                _contact += " "
            _contact += contact.first_name or ""
            res.append((contact.id, _contact))
        return res
    
    def name_search(self, cr, uid, name='', args=None, operator='ilike', context=None, limit=None):
        if not args:
            args = []
        if context is None:
            context = {}
        if name:
            ids = self.search(cr, uid, ['|',('name', operator, name),('first_name', operator, name)] + args, limit=limit, context=context)
        else:
            ids = self.search(cr, uid, args, limit=limit, context=context)
        return self.name_get(cr, uid, ids, context=context)
    
res_partner_contact()


class res_partner_address(osv.osv):

    #overriding of the name_get defined in base in order to remove the old contact name
    def name_get(self, cr, user, ids, context=None):
        """
            @param self: The object pointer
            @param cr: the current row, from the database cursor,
            @param user: the current user,
            @param ids: List of partner address’s IDs
            @param context: A standard dictionary for contextual values
        """

        if not len(ids):
            return []
        res = []
        if context is None: 
            context = {}
        for r in self.read(cr, user, ids, ['zip', 'city', 'partner_id', 'street']):
            if context.get('contact_display', 'contact')=='partner' and r['partner_id']:
                res.append((r['id'], r['partner_id'][1]))
            else:
                addr = str('')
                addr += "%s %s %s" % (r.get('street', '') or '', r.get('zip', '') \
                                    or '', r.get('city', '') or '')
                res.append((r['id'], addr.strip() or '/'))
        return res

    def name_search(self, cr, user, name, args=None, operator='ilike', context=None, limit=100):
        if not args:
            args=[]
        ids = self.search(cr, user, [('name',operator,name)] + args, limit=limit, context=context)
        jobs = self.pool.get('res.partner.job')
        if name:
            job_ids = jobs.search(cr, user, [('contact_id', operator, name)] + args, limit=limit, context=context)
            for job in jobs.browse(cr, user, job_ids):
                ids += [job.address_id.id]
        return self.name_get(cr, user, ids, context)

    _name = 'res.partner.address'
    _inherit = 'res.partner.address'
    _description ='Partner Address'

    _columns = {
        'job_id': fields.related('job_ids','contact_id','job_id',type='many2one',\
                         relation='res.partner.job', string='Main Job'),
        'job_ids': fields.one2many('res.partner.job', 'address_id', 'Contacts'),
    }
res_partner_address()

class res_partner_location(osv.osv):
    _name = 'res.partner.location'
    _inherit = 'res.partner.address'
    _table = 'res_partner_address'

res_partner_location()

class res_partner_address(osv.osv):
    _name = 'res.partner.address'
    _inherits = { 'res.partner.location' : 'address_id' }
    _table = 'res_partner_job'

    _columns = {
        'address_id' : fields.many2one('res.partner.location', 'Location'),
        'contact_id' : fields.many2one('res.partner.contact', 'Contact'),
        'contact_firstname' : fields.related('contact_id', 'first_name', type='char', size=64, string='FirstName'),
        'contact_name' : fields.related('contact_id', 'name', type='char', size='64', string="LastName"),
        'function': fields.char('Partner Function', size=64, help="Function of this contact with this partner"),
        'date_start': fields.date('Date Start',help="Start date of job(Joining Date)"),
        'date_stop': fields.date('Date Stop', help="Last date of job"),
        'state': fields.selection([('past', 'Past'),('current', 'Current')], \
                                  'State', required=True, help="Status of Address"),
    }

    _description ='Contact Partner Function'

    _defaults = {
        'state': 'current',
    }

    def name_get(self, cr, uid, ids, context=None):
        """
            @param self: The object pointer
            @param cr: the current row, from the database cursor,
            @param user: the current user,
            @param ids: List of partner address’s IDs
            @param context: A standard dictionary for contextual values
        """
        if context is None:
            context = {}

        if not ids:
            return []
        res = []

        jobs = self.browse(cr, uid, ids, context=context)

        contact_ids = [rec.contact_id.id for rec in jobs if rec.contact_id]
        contact_names = dict(self.pool.get('res.partner.contact').name_get(cr, uid, contact_ids, context=context))

        for r in jobs:
            function_name = r.function
            funct = function_name and (", " + function_name) or ""
            res.append((r.id, contact_names.get(r.contact_id.id, '') + funct))

        return res

    def onchange_name(self, cr, uid, ids, address_id='', name='', context=None):    
        return {'value': {'address_id': address_id}, 'domain':{'partner_id':'name'}}     
    
    def onchange_partner(self, cr, uid, _, partner_id, context=None):
        """
            @param self: The object pointer
            @param cr: the current row, from the database cursor,
            @param uid: the current user,
            @param _: List of IDs,
            @partner_id : ID of the Partner selected,
            @param context: A standard dictionary for contextual values
        """
        return {'value': {'address_id': False}}

    def onchange_address(self, cr, uid, _, address_id, context=None):
        """
            @@param self: The object pointer
            @param cr: the current row, from the database cursor,
            @param uid: the current user,
            @param _: List of IDs,
            @address_id : ID of the Address selected,
            @param context: A standard dictionary for contextual values
        """
        partner_id = False
        if address_id:
            address = self.pool.get('res.partner.address')\
                        .browse(cr, uid, address_id, context=context)
            partner_id = address.partner_id.id
        return {'value': {'name': partner_id}}
res_partner_address()

class res_partner_job(osv.osv):
    _name = 'res.partner.job'
    _inherit = 'res.partner.address'

res_partner_job()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
