# -*- coding: utf-8 -*-
#from openerp.exceptions import ValidationError
import openerp
from openerp.osv import fields, osv
from openerp import tools
from openerp.tools.translate import _
from openerp.tools import html2plaintext
from openerp.exceptions import ValidationError
from openerp import SUPERUSER_ID
import datetime 
import re
import urllib2
import json
import base64
from operator import itemgetter
import subprocess
import sys
reload(sys) 
sys.setdefaultencoding('utf-8') 

class maw_city(osv.osv):
    _name ='maw.city'
    
    _columns = {
      'name': fields.char('City', size=100),
 }

class maw_district(osv.osv):
    _name ='maw.district'
    
    _columns = {
      'name': fields.char('District', size=100),
      'city_id': fields.many2one('maw.city','City'),
      'user_ids': fields.many2many('res.users', 'user_operations_rel', 'operation_id', 'user_id', 'Customer Service Officers'),
 }
    
class maw_country(osv.osv):
    _name ='maw.country'
    
    _columns = {
      'name': fields.char('Name', size=50),
      'mob_code': fields.char('Mobile Code', size=10),
      'iso_code': fields.char('ISO Code', size=10),
      'active':fields.boolean('Active?')
 }    
    
    
class maw_complaint_type(osv.osv):
    _name ='maw.complaint_type'
    
    _columns = {
                
      'name': fields.char('Complaint Type', size=100),
      'description': fields.text('Description'),
    
 }
    
class maw_notification(osv.osv):
    _name ='maw.notification'
    
    _columns = {
      'name': fields.char('Name', size=100),
      'trigger': fields.selection([('close', "Close"),('confirm', "Confirm")], 'Trigger'),
      'claimcateg': fields.selection([('claim', "Complaint"),('question', "Question"),('comment', "Comment"),], 'Support Type'),
      'recipient':fields.selection([('customer', "Customer"),('coo', "COO")], 'Recipient'),
      'msg_eng': fields.text('Message in English'),
      'msg_ar': fields.text('Message in Arabic'),
 }        
    

class maw_claim(osv.osv):
    """ maw claim
    """
    _name = "maw.claim"
    _description = "Claim"
    _order = "date desc"
    _inherit = ['mail.thread']
    
    _columns = {
        'name': fields.char('Subject',copy=False),
        
        'create_date_n': fields.datetime('Creation Date',copy=False),
        
        'mobile': fields.char('Mobile', required=True),
        'customer_email': fields.char('Email', size=128, help="Customer Email" ),      
        'user_id': fields.many2one('res.users', 'Assigned To'),
        #'cso_group_id':fields.function(_get_cso_group,type='integer',String="CSO Group ID"),
        
        'customer_first_name': fields.char('First Name', required=True),
        'customer_second_name': fields.char('Last Name', required=True),
        'partner_id':fields.many2one('res.partner', "Customer"),
        
        'claimcateg': fields.selection([('claim', "Complaint"),('question', "Question"),('comment', "Comment"),], 'Support Type'),     
        
        'complaint_type': fields.many2one('maw.complaint_type', 'Complaint Type'),
        
        'priority': fields.selection([('0','Low'), ('1','Normal'), ('2','High')], 'Priority'),
       
        'city_id': fields.many2one('maw.city','City of occurrence '),
        'location':fields.char("Location",size=250),
        'district': fields.many2one('maw.district' ,'Operations' ),

        'date': fields.datetime('Occurrence Date', select=True ),
        'assigned_date': fields.datetime('Assigned Date',copy=False),
        'first_assigned_date': fields.datetime('First Assigned Date',copy=False),
        'solved_date': fields.datetime('Solved Date',copy=False),
        'date_closed': fields.datetime('Closed Date',copy=False),
        
        'country_key': fields.many2one('maw.country', 'Country'),
        
        'description': fields.text('Customer Concern',track_visibility='onchange'),
        'service_emp_comment': fields.text('Comment',copy=False),
        
        'attachment': fields.binary(string='Attachment',copy=False),
        'attachment_fname': fields.char('Attachment', copy=False),
        
        'attachment2': fields.binary(string='Additional file ',copy=False),
        'attachment2_fname': fields.char('Additional file',copy=False),
        
        'delay_open_notified':fields.boolean('Opened Delay Notified?',copy=False),
        'delay_assigned_notified':fields.boolean('Assigned Delay Notified?',copy=False),
        'delay_solved_notified':fields.boolean('Solved Delay Notified?',copy=False),
        
        'number': fields.char('Complaint ID', size=64, select=True,copy=False),
        
        'state': fields.selection([
         ('new', "New"),
         ('opened', "Opened"),
         ('assigned', "Assigned"),
        
         ('solved', "Solved"),
         ('closed', "Closed"),
         
         
    ], 'Status',track_visibility='onchange',copy=False)
                
    }
    

    _defaults = {
        'user_id': lambda s, cr, uid, c: uid or SUPERUSER_ID,
        'date': datetime.datetime.now(),
        'create_date_n': datetime.datetime.now(),
        'state':'new',
        'claimcateg': 'comment',
        'country_key':194,
        'delay_open_notified':False,
        'delay_assigned_notified':False,
        'delay_solved_notified':False,
    }
    
    def onchange_city(self, cr, uid, ids, city_id,context=None):
        
        return {'value': {'district':False}}

    def create(self, cr,uid,vals,context):
        return super(maw_claim, self).create(cr,uid,vals,context)
    
#     def unlink(self, cr, uid, ids, context=None):
#         claim_obj = self.pool['maw.claim']
#         for item in self.browse(cr, uid, ids, context=context):
#             if item.state != 'new':
#                 raise osv.except_osv(
#                     _('Invalid Action!'),
#                     _('In order to delete a support, It should be in New state.')
#                 )
#             claim_obj.unlink(cr, uid, [line.id for line in item.line_ids], context=context)
#         return super(maw_claim, self).unlink(cr, uid, ids, context=context)
    
    def action_confirm(self, cr, uid, ids, context=None):
        for claim in self.browse(cr, uid, ids, context=context):        
            if claim.claimcateg =='claim':              
                self.write(cr, uid, ids, {'state': 'opened'})
                claim.number = self.pool.get('ir.sequence').get(cr, uid, 'maw.claim')
                msg_ids = self.pool.get('maw.notification').search(cr,uid,[('trigger','=','confirm'),('claimcateg','=','claim')])
                if msg_ids:
                    msg_eng_draft = self.pool.get('maw.notification').browse(cr,uid,msg_ids[0]).msg_eng
                    msg_eng = msg_eng_draft % claim.number
                    msg_ar_draft = self.pool.get('maw.notification').browse(cr,uid,msg_ids[0]).msg_ar
                    msg_ar = msg_ar_draft % claim.number
                    if claim.customer_email:

                        msg = """ <div style="font-family: 'Lucica Grande', Ubuntu, Arial, Verdana, sans-serif font-size: 12px color: rgb(34, 34, 34) background-color: #FFF ">
 
                            <p>%s</p>
     
                            <p>%s</p>
 
                            </div>""" % (msg_eng,msg_ar)
                            
                        subject = "موقف - Mawgif" 
                        return self.send_email(cr, uid, ids,subject,claim.user_id.email, claim.customer_email,msg, context)
                    else:
                        combined_msg ="\n".join([msg_eng,msg_ar])
                        self.sendSms(cr, uid,ids, claim.mobile, combined_msg)
                
            elif claim.claimcateg =='question':
                self.write(cr, uid, ids, {'state': 'opened'})
                msg_ids = self.pool.get('maw.notification').search(cr,uid,[('trigger','=','confirm'),('claimcateg','=','question')])
                if msg_ids:
                    msg_eng = self.pool.get('maw.notification').browse(cr,uid,msg_ids[0]).msg_eng
                    msg_ar = self.pool.get('maw.notification').browse(cr,uid,msg_ids[0]).msg_ar
                    if claim.customer_email:
                        msg = """ <div style="font-family: 'Lucica Grande', Ubuntu, Arial, Verdana, sans-serif font-size: 12px color: rgb(34, 34, 34) background-color: #FFF ">
 
                            <p>%s</p>
     
                            <p>%s</p>
 
                            </div>""" % (msg_eng,msg_ar) 
                        subject = "موقف - Mawgif" 
                        return self.send_email(cr, uid, ids,subject,claim.user_id.email, claim.customer_email,msg, context)
                    else:
                        combined_msg ="\n".join([msg_eng,msg_ar])
                        self.sendSms(cr, uid, ids,claim.mobile, combined_msg)
                
            else:
                self.write(cr, uid, ids, {'state': 'opened'})
        return True
    
    
    def action_assign(self, cr, uid, ids, context=None):
        today = fields.datetime.now()
        for claim in self.browse(cr, uid, ids, context=context):        
            if not claim.first_assigned_date:              
                self.write(cr, uid, ids, {'state': 'assigned' , 'assigned_date': today , 'first_assigned_date': today})
            else: 
                self.write(cr, uid, ids, {'state': 'assigned' , 'assigned_date': today}) 
        return True
    
    def action_re_assign(self, cr, uid, ids, context=None):
        today = fields.datetime.now()
        self.write(cr, uid, ids, {'state': 'assigned' , 'assigned_date': today,'delay_assigned_notified':False})
        return True 
    
    def action_solve(self, cr, uid, ids, context=None):
        today = fields.datetime.now()
        self.write(cr, uid, ids, {'state': 'solved' , 'solved_date': today,'delay_solved_notified':False})
        return True
    
    def action_close(self, cr, uid, ids, context=None):
        today = fields.datetime.now()
        for claim in self.browse(cr, uid, ids, context=context): 
            if not claim.service_emp_comment: 
                raise osv.except_osv(_('Error!'),_("Please enter some comment before closing."))
            if claim.claimcateg =='claim':              
                self.write(cr, uid, ids,{'state': 'closed', 'date_closed': today})
                msg_ids = self.pool.get('maw.notification').search(cr,uid,[('trigger','=','close'),('claimcateg','=','claim')])
                if msg_ids:
                    msg_eng_draft = self.pool.get('maw.notification').browse(cr,uid,msg_ids[0]).msg_eng
                    msg_eng = msg_eng_draft % claim.number
                    msg_ar_draft = self.pool.get('maw.notification').browse(cr,uid,msg_ids[0]).msg_ar
                    msg_ar = msg_ar_draft % claim.number
                    if claim.customer_email:

                        msg = """ <div style="font-family: 'Lucica Grande', Ubuntu, Arial, Verdana, sans-serif font-size: 12px color: rgb(34, 34, 34) background-color: #FFF ">
 
                            <p>%s</p>
     
                            <p>%s</p>
 
                            </div>""" % (msg_eng,msg_ar) 
                        subject = "موقف - Mawgif"  
                        return self.send_email(cr, uid, ids,subject,claim.user_id.email, claim.customer_email,msg, context)
                    else:
                        combined_msg ="\n".join([msg_eng,msg_ar])
                        self.sendSms(cr, uid, ids,claim.mobile, combined_msg)
                
            elif claim.claimcateg =='question':
                self.write(cr, uid, ids,{'state': 'closed', 'date_closed': today})
                msg_ids = self.pool.get('maw.notification').search(cr,uid,[('trigger','=','close'),('claimcateg','=','question')])
                if msg_ids:
                    msg_eng = self.pool.get('maw.notification').browse(cr,uid,msg_ids[0]).msg_eng
                    msg_ar = self.pool.get('maw.notification').browse(cr,uid,msg_ids[0]).msg_ar
                    if claim.customer_email:
                        msg = """ <div style="font-family: 'Lucica Grande', Ubuntu, Arial, Verdana, sans-serif font-size: 12px color: rgb(34, 34, 34) background-color: #FFF ">
 
                            <p>%s</p>
     
                            <p>%s</p>
 
                            </div>""" % (msg_eng,msg_ar) 
                        subject = "موقف - Mawgif" 
                        return self.send_email(cr, uid, ids,subject,claim.user_id.email, claim.customer_email,msg, context)
                    else:
                        combined_msg ="\n".join([msg_eng,msg_ar])
                        self.sendSms(cr, uid, ids,claim.mobile, combined_msg)
            elif claim.claimcateg =='comment':
                self.write(cr, uid, ids,{'state': 'closed', 'date_closed': today})
                msg_ids = self.pool.get('maw.notification').search(cr,uid,[('trigger','=','close'),('claimcateg','=','comment')])
                if msg_ids:
                    msg_eng = self.pool.get('maw.notification').browse(cr,uid,msg_ids[0]).msg_eng
                    msg_ar = self.pool.get('maw.notification').browse(cr,uid,msg_ids[0]).msg_ar
                    if claim.customer_email:
                        msg = """ <div style="font-family: 'Lucica Grande', Ubuntu, Arial, Verdana, sans-serif font-size: 12px color: rgb(34, 34, 34) background-color: #FFF ">
 
                            <p>%s</p>
     
                            <p>%s</p>
 
                            </div>""" % (msg_eng,msg_ar) 
                        subject = "موقف - Mawgif" 
                        return self.send_email(cr, uid, ids,subject,claim.user_id.email, claim.customer_email,msg, context)
                    else:
                        combined_msg ="\n".join([msg_eng,msg_ar])
                        self.sendSms(cr, uid,ids, claim.mobile, combined_msg)
                
                ir_model_data = self.pool.get('ir.model.data')
                coo_group_id = ir_model_data.get_object_reference(cr, uid, 'mawgif_support', 'group_manager')[1]
                cr.execute('SELECT DISTINCT uid '\
                    'FROM res_groups_users_rel '\
                    'WHERE gid = %s ' % coo_group_id)
                res = [id[0] for id in cr.fetchall()]
                if res:
                    email_ids = []
                    for userid in self.pool.get('res.users').browse(cr,uid,res):
                        email_ids.append(userid.partner_id.email)
                    if email_ids:
                        msg = """ <div style="font-family: 'Lucica Grande', Ubuntu, Arial, Verdana, sans-serif font-size: 12px color: rgb(34, 34, 34) background-color: #FFF ">
 
                            <p>%s</p>
     
 
                            </div>""" % (claim.description) 
                        subject = "موقف - Mawgif" 
                        return self.send_email(cr, uid, ids,subject,claim.user_id.email, ','.join(email_ids),msg, context)
            else:
                self.write(cr, uid, ids,{'state': 'closed', 'date_closed': today})
        return True
        
    
    # added at 7/1/2016 5 pm for data validation 
    def _check_mail(self, cr, uid, ids, context=None):
        
        for claim in self.browse(cr, uid, ids, context):
            if claim.customer_email:
                try:
                    if not re.match("[^@]+@[^@]+\.[^@]+",claim.customer_email):
                        return False
                    else:
                        return True
                except IndexError:
                    return False
            else:
                return True
 

    def _check_mobile(self, cr, uid, ids, context=None):
        
        
        #first_char = claim.mobile[:1]
        for claim in self.browse(cr, uid, ids, context):
            if claim.mobile.isdigit() and claim.mobile[:1] <> '0':
                #if re.match("/^[0-9]{10,14}$/", claim.mobile) != None:
                return True
            else :
                return False
    
    _constraints = [(_check_mobile, 'not valid mobile',  ['mobile']),
                (_check_mail, 'not valid mail',  ['customer_email'])
                ]
           
    
    def action_contact_customer(self, cr, uid, ids, context=None):
        '''
        This function opens a window to compose an email
        '''
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        ir_model_data = self.pool.get('ir.model.data')
        try:
            template_id = ir_model_data.get_object_reference(cr, uid, 'mawgif_support', 'email_template_contact_customer')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False 
        ctx = dict()
        ctx.update({
            'default_model': 'maw.claim',
            'default_res_id': ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
        })
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }
        
    def send_email(self, cr, uid, ids,subject,email_from,email_to, msg, context=None):
        email_ids = []
        vals = {'state': 'outgoing',
                         'subject': subject,
                         'body_html': msg,
                         'email_to': email_to,
                         'email_from': email_from,
                 }
        email_ids.append(self.pool.get('mail.mail').create(cr, uid, vals, context=context))
        if email_ids:
            self.pool.get('mail.mail').send(cr, uid, email_ids, context=context)
            
    def sendSms(self,cr,uid,ids,mobile,msg):
#         msg = 'س'
        #encoded_msg = "".join([c.encode("hex").zfill(4) for c in msg])
        country_code = '966'
        claim_id = self.pool.get('maw.claim').browse(cr, uid, ids)
        if claim_id:
            country_code = claim_id.country_key.mob_code
            
        reload(sys) 
        sys.setdefaultencoding('utf-8') 
        
        sms_footer = "\n\nفريق موقف" 
        msg = msg + sms_footer

        encoded_msg = self.convertToUnicode(msg)
        #encoded_msg = "062A064500200641062A062D002006270644064506390627064506440629002006310642064500200023002000310035002D0030003000300031002000200633064806410020064A062A0645002006270644062A06480627063506440020064506390643002006420631064A06280627"
        print encoded_msg
        reload(sys) 
        sys.setdefaultencoding('ascii')
        url = "http://www.mobily.ws/api/msgSend.php?mobile=966565924302&password=mawgif0909&numbers="+country_code+ mobile +"&sender=Mawgif&msg="+encoded_msg+"&applicationType=24"
        req = urllib2.Request(url)
        response = json.loads(urllib2.urlopen(req).read())
        print response
        if response != 1:
            print "Error"
        else:
            print "Message sent successfully"
            
    # -------------------------------------------------------
    # Mail gateway
    # -------------------------------------------------------
    # ----
    def message_new(self, cr, uid, msg, custom_values=None, context=None):
        """ Overrides mail_thread message_new that is called by the mailgateway
            through message_process.
            This override updates the document according to the email.
        """
        if custom_values is None:
            custom_values = {}
        desc = html2plaintext(msg.get('body')) if msg.get('body') else ''
        defaults = {
            #'name': msg.get('subject') or _("No Subject"),
            'description': desc,
            'customer_email': msg.get('from'),
            #'email_cc': msg.get('cc'),
            #'partner_id': msg.get('author_id', False),
        }
        #if msg.get('priority'):
        #    defaults['priority'] = msg.get('priority')
        defaults.update(custom_values)
        return super(maw_claim, self).message_new(cr, uid, msg, custom_values=defaults, context=context)
    
    def send_delay_notifications(self, cr, uid, ids=False, context=None):
        self.get_delayed_work_items_in_open_state(cr, uid, ids, context)
        self.get_delayed_work_items_in_assigned_state(cr, uid, ids,context)
        self.get_delayed_work_items_in_solved_state(cr, uid, ids, context)

    
    def get_delayed_work_items_in_open_state(self, cr, uid, ids, context=None):
            
        str_sql_select_all_delayed_wi =  "select customer_first_name, claimcateg, state ,id, user_id "
        str_sql_select_all_delayed_wi += "from  maw_claim c "
        str_sql_select_all_delayed_wi += "where  (current_date -  c.create_date_n   > '2 day'::interval) and c.state ='opened' and delay_open_notified = false"
        cr.execute(str_sql_select_all_delayed_wi)
        all_delayed_wi = cr.fetchall()          
        if len(all_delayed_wi) > 0:                    
            for row_workitem in all_delayed_wi:  
                claim = self.browse(cr, uid, row_workitem[3], context=context)                                                             
                ir_model_data = self.pool.get('ir.model.data')
                coo_group_id = ir_model_data.get_object_reference(cr, uid, 'mawgif_support', 'group_manager')[1]
                cr.execute('SELECT DISTINCT uid '\
                    'FROM res_groups_users_rel '\
                    'WHERE gid = %s ' % coo_group_id)
                res = [id[0] for id in cr.fetchall()]
                if res:
                    email_ids = []
                    responsible = self.pool.get('res.users').browse(cr,uid,row_workitem[4])
                    for userid in self.pool.get('res.users').browse(cr,uid,res):
                        email_ids.append(userid.partner_id.email)
                    if email_ids:
                        msg = """ <div style="font-family: 'Lucica Grande', Ubuntu, Arial, Verdana, sans-serif font-size: 12px color: rgb(34, 34, 34) background-color: #FFF ">
 
                            <p>Responsible : %s</p>
                            <p><a href="%s">Click to View</a></p>
     
 
                            </div>""" % (responsible.partner_id.name,self.construct_claim_url(row_workitem[3])) 
                        claim.delay_open_notified = True
                        subject = "Support Ticket - Delay On Open"
                        return self.send_email(cr, uid, ids,subject,claim.user_id.email, ','.join(email_ids),msg, context)
        return True
    


    def get_delayed_work_items_in_assigned_state(self, cr, uid, ids, context=None):
        
        str_sql_select_all_delayed_wi =  "select customer_first_name, claimcateg, state ,id,user_id "
        str_sql_select_all_delayed_wi += "from  maw_claim c "
        str_sql_select_all_delayed_wi += "where  c.state ='assigned' and "
        str_sql_select_all_delayed_wi += "       ((current_date - c.first_assigned_date )  > '3 day'::interval) and delay_assigned_notified = false"
        cr.execute(str_sql_select_all_delayed_wi)
        all_delayed_wi = cr.fetchall()          
        if len(all_delayed_wi) > 0:                    
            for row_workitem in all_delayed_wi:                                                          
                claim = self.browse(cr, uid, row_workitem[3], context=context)                                                             
                ir_model_data = self.pool.get('ir.model.data')
                coo_group_id = ir_model_data.get_object_reference(cr, uid, 'mawgif_support', 'group_manager')[1]
                cr.execute('SELECT DISTINCT uid '\
                    'FROM res_groups_users_rel '\
                    'WHERE gid = %s ' % coo_group_id)
                res = [id[0] for id in cr.fetchall()]
                if res:
                    email_ids = []
                    responsible = self.pool.get('res.users').browse(cr,uid,row_workitem[4])
                    for userid in self.pool.get('res.users').browse(cr,uid,res):
                        email_ids.append(userid.partner_id.email)
                    if email_ids:
                        msg = """ <div style="font-family: 'Lucica Grande', Ubuntu, Arial, Verdana, sans-serif font-size: 12px color: rgb(34, 34, 34) background-color: #FFF ">
 
                            <p>Responsible : %s</p>
                            <p><a href="%s">Click to View</a></p>
     
 
                            </div>""" % (responsible.partner_id.name,self.construct_claim_url(row_workitem[3])) 
                        claim.delay_assigned_notified = True
                        subject = "Support Ticket - Delay On Assigned"
                        return self.send_email(cr, uid, ids,subject,claim.user_id.email, ','.join(email_ids),msg, context)
        return True
    
    
    def get_delayed_work_items_in_solved_state(self, cr, uid, ids, context=None):
        
        str_sql_select_all_delayed_wi_in_solved =  "select customer_first_name, claimcateg, state ,id,user_id "
        str_sql_select_all_delayed_wi_in_solved += "from  maw_claim c "
        str_sql_select_all_delayed_wi_in_solved += "where  ( current_date - c.solved_date  > '1 day'::interval) and c.state ='solved' and delay_solved_notified = false"
        cr.execute(str_sql_select_all_delayed_wi_in_solved)
        all_delayed_wi_in_solved = cr.fetchall()          
        if len(all_delayed_wi_in_solved) > 0:                    
            for row_workitem in all_delayed_wi_in_solved:                                                          
                claim = self.browse(cr, uid, row_workitem[3], context=context)                                                             
                ir_model_data = self.pool.get('ir.model.data')
                coo_group_id = ir_model_data.get_object_reference(cr, uid, 'mawgif_support', 'group_manager')[1]
                cr.execute('SELECT DISTINCT uid '\
                    'FROM res_groups_users_rel '\
                    'WHERE gid = %s ' % coo_group_id)
                res = [id[0] for id in cr.fetchall()]
                if res:
                    email_ids = []
                    responsible = self.pool.get('res.users').browse(cr,uid,row_workitem[4])
                    for userid in self.pool.get('res.users').browse(cr,uid,res):
                        email_ids.append(userid.partner_id.email)
                    if email_ids:
                        msg = """ <div style="font-family: 'Lucica Grande', Ubuntu, Arial, Verdana, sans-serif font-size: 12px color: rgb(34, 34, 34) background-color: #FFF ">
 
                            <p>Responsible : %s</p>
                            <p><a href="%s">Click to View</a></p>
     
 
                            </div>""" % (responsible.partner_id.name,self.construct_claim_url(row_workitem[3])) 
                        claim.delay_solved_notified = True
                        subject = "Support Ticket - Delay On Solved"
                        return self.send_email(cr, uid, ids,subject,claim.user_id.email, ','.join(email_ids),msg, context)
        return True
    
    def construct_claim_url(self,cid):
        web_base_url = "http://localhost:8069/web?#id=%s&view_type=form&model=maw.claim"
        if cid:
            return web_base_url % cid
        
    
    def encode_msg(self,cr,uid,msg):        # open process
        #path = "D:/mobily1.php"
        script_response = False
        msg = "\"" + msg +  "\"" 
        path = self.pool['ir.config_parameter'].get_param(cr, uid, 'mobilyws') or ''
        if path and msg:
            proc = subprocess.Popen("php %s %s" % (path,msg), shell=True, stdout=subprocess.PIPE)
            script_response = proc.stdout.read()
        return script_response
    
    def convertToUnicode(self,message):
        unicodeArray = {}
        chrArray = ["،"]
        unicodeArray[0] = "060C"
        chrArray.append("؛")
        unicodeArray[1] = "061B"
        chrArray.append("؟")
        unicodeArray[2] = "061F"
        chrArray.append("ء")
        unicodeArray[3] = "0621"
        chrArray.append("آ")
        unicodeArray[4] = "0622"
        chrArray.append("أ")
        unicodeArray[5] = "0623"
        chrArray.append("ؤ")
        unicodeArray[6] = "0624"
        chrArray.append("إ")
        unicodeArray[7] = "0625"
        chrArray.append("ئ")
        unicodeArray[8] = "0626"
        chrArray.append("ا")
        unicodeArray[9] = "0627"
        chrArray.append("ب")
        unicodeArray[10] = "0628"
        chrArray.append("ة")
        unicodeArray[11] = "0629"
        chrArray.append("ت")
        unicodeArray[12] = "062A"
        chrArray.append("ث")
        unicodeArray[13] = "062B"
        chrArray.append("ج")
        unicodeArray[14] = "062C"
        chrArray.append("ح")
        unicodeArray[15] = "062D"
        chrArray.append("خ")
        unicodeArray[16] = "062E"
        chrArray.append("د")
        unicodeArray[17] = "062F"
        chrArray.append("ذ")
        unicodeArray[18] = "0630"
        chrArray.append("ر")
        unicodeArray[19] = "0631"
        chrArray.append("ز")
        unicodeArray[20] = "0632"
        chrArray.append("س")
        unicodeArray[21] = "0633"
        chrArray.append("ش")
        unicodeArray[22] = "0634"
        chrArray.append("ص")
        unicodeArray[23] = "0635"
        chrArray.append("ض")
        unicodeArray[24] = "0636"
        chrArray.append("ط")
        unicodeArray[25] = "0637"
        chrArray.append("ظ")
        unicodeArray[26] = "0638"
        chrArray.append("ع")
        unicodeArray[27] = "0639"
        chrArray.append("غ")
        unicodeArray[28] = "063A"
        chrArray.append("ف")
        unicodeArray[29] = "0641"
        chrArray.append("ق")
        unicodeArray[30] = "0642"
        chrArray.append("ك")
        unicodeArray[31] = "0643"
        chrArray.append("ل")
        unicodeArray[32] = "0644"
        chrArray.append("م")
        unicodeArray[33] = "0645"
        chrArray.append("ن")
        unicodeArray[34] = "0646"
        chrArray.append("ه")
        unicodeArray[35] = "0647"
        chrArray.append("و")
        unicodeArray[36] = "0648"
        chrArray.append("ى")
        unicodeArray[37] = "0649"
        chrArray.append("ي")
        unicodeArray[38] = "064A"
        chrArray.append("ـ")
        unicodeArray[39] = "0640"
        chrArray.append("ً")
        unicodeArray[40] = "064B"
        chrArray.append("ٌ")
        unicodeArray[41] = "064C"
        chrArray.append("ٍ")
        unicodeArray[42] = "064D"
        chrArray.append("َ")
        unicodeArray[43] = "064E"
        chrArray.append("ُ")
        unicodeArray[44] = "064F"
        chrArray.append("ِ")
        unicodeArray[45] = "0650"
        chrArray.append("ّ")
        unicodeArray[46] = "0651"
        chrArray.append("ْ")
        unicodeArray[47] = "0652"
        chrArray.append("!")
        unicodeArray[48] = "0021"
        chrArray.append('"')
        unicodeArray[49] = "0022"
        chrArray.append("#")
        unicodeArray[50] = "0023"
        chrArray.append("$")
        unicodeArray[51] = "0024"
        chrArray.append("%")
        unicodeArray[52] = "0025"
        chrArray.append("&")
        unicodeArray[53] = "0026"
        chrArray.append("'")
        unicodeArray[54] = "0027"
        chrArray.append("(")
        unicodeArray[55] = "0028"
        chrArray.append(")")
        unicodeArray[56] = "0029"
        chrArray.append("*")
        unicodeArray[57] = "002A"
        chrArray.append("+")
        unicodeArray[58] = "002B"
        chrArray.append(",")
        unicodeArray[59] = "002C"
        chrArray.append("-")
        unicodeArray[60] = "002D"
        chrArray.append(".")
        unicodeArray[61] = "002E"
        chrArray.append("/")
        unicodeArray[62] = "002F"
        chrArray.append("0")
        unicodeArray[63] = "0030"
        chrArray.append("1")
        unicodeArray[64] = "0031"
        chrArray.append("2")
        unicodeArray[65] = "0032"
        chrArray.append("3")
        unicodeArray[66] = "0033"
        chrArray.append("4")
        unicodeArray[67] = "0034"
        chrArray.append("5")
        unicodeArray[68] = "0035"
        chrArray.append("6")
        unicodeArray[69] = "0036"
        chrArray.append("7")
        unicodeArray[70] = "0037"
        chrArray.append("8")
        unicodeArray[71] = "0038"
        chrArray.append("9")
        unicodeArray[72] = "0039"
        chrArray.append(":")
        unicodeArray[73] = "003A"
        chrArray.append(";")
        unicodeArray[74] = "003B"
        chrArray.append("<")
        unicodeArray[75] = "003C"
        chrArray.append("=")
        unicodeArray[76] = "003D"
        chrArray.append(">")
        unicodeArray[77] = "003E"
        chrArray.append("?")
        unicodeArray[78] = "003F"
        chrArray.append("@")
        unicodeArray[79] = "0040"
        chrArray.append("A")
        unicodeArray[80] = "0041"
        chrArray.append("B")
        unicodeArray[81] = "0042"
        chrArray.append("C")
        unicodeArray[82] = "0043"
        chrArray.append("D")
        unicodeArray[83] = "0044"
        chrArray.append("E")
        unicodeArray[84] = "0045"
        chrArray.append("F")
        unicodeArray[85] = "0046"
        chrArray.append("G")
        unicodeArray[86] = "0047"
        chrArray.append("H")
        unicodeArray[87] = "0048"
        chrArray.append("I")
        unicodeArray[88] = "0049"
        chrArray.append("J")
        unicodeArray[89] = "004A"
        chrArray.append("K")
        unicodeArray[90] = "004B"
        chrArray.append("L")
        unicodeArray[91] = "004C"
        chrArray.append("M")
        unicodeArray[92] = "004D"
        chrArray.append("N")
        unicodeArray[93] = "004E"
        chrArray.append("O")
        unicodeArray[94] = "004F"
        chrArray.append("P")
        unicodeArray[95] = "0050"
        chrArray.append("Q")
        unicodeArray[96] = "0051"
        chrArray.append("R")
        unicodeArray[97] = "0052"
        chrArray.append("S")
        unicodeArray[98] = "0053"
        chrArray.append("T")
        unicodeArray[99] = "0054"
        chrArray.append("U")
        unicodeArray[100] = "0055"
        chrArray.append("V")
        unicodeArray[101] = "0056"
        chrArray.append("W")
        unicodeArray[102] = "0057"
        chrArray.append("X")
        unicodeArray[103] = "0058"
        chrArray.append("Y")
        unicodeArray[104] = "0059"
        chrArray.append("Z")
        unicodeArray[105] = "005A"
        chrArray.append("[")
        unicodeArray[106] = "005B"
        char="\ "
        chrArray.append(char.strip())
        unicodeArray[107] = "005C"
        chrArray.append("]")
        unicodeArray[108] = "005D"
        chrArray.append("^")
        unicodeArray[109] = "005E"
        chrArray.append("_")
        unicodeArray[110] = "005F"
        chrArray.append("`")
        unicodeArray[111] = "0060"
        chrArray.append("a")
        unicodeArray[112] = "0061"
        chrArray.append("b")
        unicodeArray[113] = "0062"
        chrArray.append("c")
        unicodeArray[114] = "0063"
        chrArray.append("d")
        unicodeArray[115] = "0064"
        chrArray.append("e")
        unicodeArray[116] = "0065"
        chrArray.append("f")
        unicodeArray[117] = "0066"
        chrArray.append("g")
        unicodeArray[118] = "0067"
        chrArray.append("h")
        unicodeArray[119] = "0068"
        chrArray.append("i")
        unicodeArray[120] = "0069"
        chrArray.append("j")
        unicodeArray[121] = "006A"
        chrArray.append("k")
        unicodeArray[122] = "006B"
        chrArray.append("l")
        unicodeArray[123] = "006C"
        chrArray.append("m")
        unicodeArray[124] = "006D"
        chrArray.append("n")
        unicodeArray[125] = "006E"
        chrArray.append("o")
        unicodeArray[126] = "006F"
        chrArray.append("p")
        unicodeArray[127] = "0070"
        chrArray.append("q")
        unicodeArray[128] = "0071"
        chrArray.append("r")
        unicodeArray[129] = "0072"
        chrArray.append("s")
        unicodeArray[130] = "0073"
        chrArray.append("t")
        unicodeArray[131] = "0074"
        chrArray.append("u")
        unicodeArray[132] = "0075"
        chrArray.append("v")
        unicodeArray[133] = "0076"
        chrArray.append("w")
        unicodeArray[134] = "0077"
        chrArray.append("x")
        unicodeArray[135] = "0078"
        chrArray.append("y")
        unicodeArray[136] = "0079"
        chrArray.append("z")
        unicodeArray[137] = "007A"
        chrArray.append("{")
        unicodeArray[138] = "007B"
        chrArray.append("|")
        unicodeArray[139] = "007C"
        chrArray.append("}")
        unicodeArray[140] = "007D"
        chrArray.append("~")
        unicodeArray[141] = "007E"
        chrArray.append("©")
        unicodeArray[142] = "00A9"
        chrArray.append("®")
        unicodeArray[143] = "00AE"
        chrArray.append("÷")
        unicodeArray[144] = "00F7"
        chrArray.append("×")
        unicodeArray[145] = "00F7"
        chrArray.append("§")
        unicodeArray[146] = "00A7"
        chrArray.append(" ")
        unicodeArray[147] = "0020"
        chrArray.append("\n")
        unicodeArray[148] = "000D"
        chrArray.append("\r")
        unicodeArray[149] = "000A"

        strResult = ""

        for i in range(len(message)):
                        mbstr = self.mb_substr(message,i,1,'UTF-8')
                        if mbstr in chrArray:
                                        strResult += unicodeArray[chrArray.index(self.mb_substr(message,i,1,'UTF-8'))]

        return strResult


    def mb_substr(self,s,start,length,encoding) :
        u_s = s.decode(encoding)
        return (u_s[start:(start+length)] if length else u_s[start:]).encode(encoding)
    
    


    
