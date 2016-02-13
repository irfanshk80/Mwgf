# -*- coding: utf-8 -*-
import base64
import pytz

import werkzeug
import werkzeug.urls

from openerp import http, SUPERUSER_ID
from openerp.http import request
from openerp.tools.translate import _
from openerp.tools import detect_server_timezone
from datetime import datetime, timedelta


class support(http.Controller):

    def generate_google_map_url(self, street, city, city_zip, country_name):
        url = "http://maps.googleapis.com/maps/api/staticmap?center=%s&sensor=false&zoom=8&size=298x298" % werkzeug.url_quote_plus(
            '%s, %s %s, %s' % (street, city, city_zip, country_name)
        )
        return url
    
    @http.route('/page/support', type='http', auth="public", website=True)
    def default_support(self, **kwargs):
        values = {}
        cr, context = request.cr, request.context
        orm_city = request.registry['maw.city']
        district_orm = request.registry['maw.district']
        country_orm = request.registry['maw.country']

        city_ids = orm_city.search(cr, SUPERUSER_ID, [], context=context)
        cities = orm_city.browse(cr, SUPERUSER_ID, city_ids, context)
        district_ids = district_orm.search(cr, SUPERUSER_ID, [], context=context)
        districts = district_orm.browse(cr, SUPERUSER_ID, district_ids, context)
        country_ids = country_orm.search(cr, SUPERUSER_ID, [], context=context)
        countries = country_orm.browse(cr, SUPERUSER_ID, country_ids, context)

        
        for field in ['mobile', 'customer_first_name', 'customer_second_name' ,'description','customer_email'] :
            if kwargs.get(field):
                values[field] = kwargs.pop(field)
        values.update(kwargs=kwargs.items())
        values.update({'cities':cities,'districts':districts,'countries':countries})
        
        return request.website.render("mawgif_support.mawgif_support", values)

    def create_support_ticket(self, request, values, kwargs):
        """ Allow to be overrided """
        cr, context = request.cr, request.context
        claim_id =  request.registry['maw.claim'].create(cr, SUPERUSER_ID, values, context=dict(context, mail_create_nosubscribe=True))
        request.registry['maw.claim'].action_confirm(cr,SUPERUSER_ID,claim_id)
        return claim_id

    def preRenderThanks(self, values, kwargs):
        """ Allow to be overrided """
        company = request.website.company_id
        return {
            'google_map_url': self.generate_google_map_url(company.street, company.city, company.zip, company.country_id and company.country_id.name_get()[0][1] or ''),
            '_values': values,
            '_kwargs': kwargs,
        }

    def get_support_response(self, values, kwargs):
        values = self.preRenderThanks(values, kwargs)
        return request.website.render(kwargs.get("view_callback", "mawgif_support.mawgif_thanks"), values)

    @http.route(['/mawgif/get_state'], type='json', auth="public", methods=['POST'], website=True)
    def get_state(self, request, city_id, **kw):
        dist_list = []
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        dist_id = request.registry['maw.district'].search(cr,SUPERUSER_ID,[('city_id','=',int(city_id))])
        dists = pool['maw.district'].browse(cr, uid, dist_id, context=context)
        ret = "<select id='dist' class='form-control' name='district' > "
        for dist in dists:
            ret += "<option value='"+ str(dist['id']) +"'>" + dist['name'] + "</option>"
            # dist_list = dist['name']
        ret += "</select>"
        return ret

    @http.route(['/mawgif/support'], type='http', auth="public", website=True)
    def support(self, **kwargs):
        def dict_to_str(title, dictvar):
            ret = "\n\n%s" % title
            for field in dictvar:
                ret += "\n%s" % field
            return ret

        _TECHNICAL = ['show_info', 'view_from', 'view_callback']  # Only use for behavior, don't stock it
        _BLACKLIST = ['id', 'create_uid', 'create_date', 'write_uid', 'write_date', 'user_id', 'active']  # Allow in description
        _REQUIRED = ['mobile', 'customer_first_name', 'customer_second_name' ,'description']  # Could be improved including required from model

        post_file = []  # List of file to add to ir_attachment once we have the ID
        post_description = []  # Info to add after the message
        # Values field is initialized with defaults
        creator_type = False
        creator_id = False
        if not request.env.user.active:
            creator_type = 'customer'
            creator_id = False
        else:
            if request.env.user.cso:
                creator_type = 'customer_service_officer'
                creator_id = request.env.user.id
            else:
                creator_type = 'call_center_agent'
                creator_id = request.env.user.id
        values = {
                    'state':'new',
                    'claimcateg': 'comment',
                    'country_key':194,
                    'delay_open_notified':False,
                    'delay_assigned_notified':False,
                    'delay_solved_notified':False,
                    'source_type':'web',
                    'creator_type':creator_type,
                    'created_by':creator_id
                  }


        for field_name, field_value in kwargs.items():
            if hasattr(field_value, 'filename'):
                if field_name=="attachment":
                    values[field_name] = base64.encodestring(field_value.read())
                    values["attachment_fname"]= field_value.filename
                elif field_name=="attachment2":
                    values[field_name] = base64.encodestring(field_value.read())
                    values["attachment2_fname"]= field_value.filename
            elif field_name in request.registry['maw.claim']._fields and field_name not in _BLACKLIST:
                if field_name=="date":
                    try:
                        sys_tz = detect_server_timezone()
                        utc_tz = pytz.timezone(sys_tz)
                        ar_timezone = pytz.timezone('Asia/Riyadh')
                        fmt = '%Y-%m-%dT%H:%M'
                        naive = datetime.strptime(field_value, fmt)
                        #utc_dt = utc_tz.localize(naive, is_dst=None)
                        local_dt = ar_timezone.localize(naive, is_dst=None)
                        utc_dt = local_dt.astimezone (utc_tz)
                        if utc_dt:
                            values[field_name]=str(utc_dt)
                        else:
                            values[field_name] = field_value
                    except Exception as e:
                        #values.pop(field_name)
                        print e
                else:
                    values[field_name] = field_value
            elif field_name not in _TECHNICAL:  # allow to add some free fields or blacklisted field like ID
                post_description.append("%s: %s" % (field_name, field_value))

        if "name" not in kwargs and values.get("customer_first_name"):  # if kwarg.name is empty, it's an error, we cannot copy the contact_name
            values["name"] = values.get("customer_first_name")
        # fields validation : Check that required field from model crm_lead exists
        error = set(field for field in _REQUIRED if not values.get(field))

        if error:
            values = dict(values, error=error, kwargs=kwargs.items())
            return request.website.render(kwargs.get("view_from", "mawgif_support.mawgif_support"), values)

        # description is required, so it is always already initialized
        if post_description:
            values['description'] += dict_to_str(_("Custom Fields: "), post_description)

        if kwargs.get("show_info"):
            post_description = []
            environ = request.httprequest.headers.environ
            post_description.append("%s: %s" % ("IP", environ.get("REMOTE_ADDR")))
            post_description.append("%s: %s" % ("USER_AGENT", environ.get("HTTP_USER_AGENT")))
            post_description.append("%s: %s" % ("ACCEPT_LANGUAGE", environ.get("HTTP_ACCEPT_LANGUAGE")))
            post_description.append("%s: %s" % ("REFERER", environ.get("HTTP_REFERER")))
            values['description'] += dict_to_str(_("Environ Fields: "), post_description)
            
        claim_id = self.create_support_ticket(request, dict(values), kwargs)
        values.update(claim_id=claim_id)

        return self.get_support_response(values, kwargs)
