# -*- coding: utf-8 -*-
#/#############################################################################
#
#    Span Tree
#    Copyright (C) 2004-TODAY DrishtiTech(<http://www.drishtitech.com/>).
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
#/#############################################################################

import base64
from openerp import models, fields, api, _
from openerp.osv.orm import except_orm
from datetime import datetime,timedelta
from dateutil.relativedelta import relativedelta
import time
import calendar

class claim_report_print_wiz(models.TransientModel):
    _name = 'claim.report.print.wiz'
    
    @api.model
    def _default_user_id(self): 
        return self._uid

    report_id = fields.Selection([('daily','Daily Report'),('monthly','Monthly Report'),('on_demand','On demand Report')], default='daily', string='Report Type')
    user_id = fields.Many2one("res.users", string="User")
    filter = fields.Selection([('filter_date', 'Date'), ('filter_period', 'Month')], "Filter by")
    month = fields.Selection([('01', 'Jan'), ('02', 'Feb'), ('03', 'Mar'),('04', 'Apr'),('05', 'May'),('06', 'Jun'),
                              ('07', 'July'), ('08', 'Aug'),('09', 'Sep'),('10', 'Oct'),('11', 'Nov'),('12', 'Dec')
                              ], "Month")
    date_from = fields.Date("Start Date")
    date_to = fields.Date("End Date")
    
    def onchange_filter(self, cr, uid, ids, filter='filter_period', context=None):
        res = {'value': {}}
        if filter == 'filter_date':
            res['value'] = {'month': False, 'date_from': time.strftime('%Y-01-01'), 'date_to': time.strftime('%Y-%m-%d')}
        if filter == 'filter_period':
            month = time.strftime('%m')
            date_from = time.strftime('%Y-'+ month +'-01')
            date_to = self.mkLastOfMonth(cr, uid, ids, date_from, context)
            res['value'] = {'month': month, 'date_from': date_from, 'date_to': date_to}
        return res
    
    def onchange_month(self, cr, uid, ids, month, context=None):
        res = {'value': {}}
        if not month:
            month = time.strftime('%m')
            
        date_from = time.strftime('%Y-'+ month +'-01')
        date_to = self.mkLastOfMonth(cr, uid, ids, date_from, context)
        res['value'] = {'date_from': date_from, 'date_to': date_to}
        return res
    
    def mkLastOfMonth(self, cr, uid, ids, dtDateTime, context=None):
        date = datetime.date(datetime.strptime(dtDateTime, '%Y-%m-%d'))
        first_day = date.replace(day = 1)
        last_day = date.replace(day = calendar.monthrange(date.year, date.month)[1])
        return last_day
    
        #subtract from nextMonth and return
        
    def get_yesterday(self, cr, uid, context=None):
        return (datetime.now()-timedelta(1)).strftime('%Y-%m-%d')

    @api.multi
    def print_report(self):
        report_name = False
        data = None
        if self.report_id == 'daily':
            report_name = 'mawgif_support.report_daily_claim'
        elif self.report_id == 'monthly':
            report_name = 'mawgif_support.report_monthly_claim'
        elif self.report_id == 'on_demand':
            report_name = 'mawgif_support.report_ondemand_claim'
        report = self.pool['report'].get_action(self._cr, self._uid, [], report_name, data,self._context)
        return report

    
    def get_datas_daily(self, data):
        support = {'claim':'Complaint','comment':'Comment','question':'Question'}
        res_dict = {}
        prev_res_dict = {}
        total_opened = 0
        total_assigned = 0
        total_solved = 0
        
        total_complaint_ontime_today = 0
        total_comment_ontime_today = 0
        total_question_ontime_today = 0
        
        total_complaint_late_today = 0
        total_comment_late_today = 0
        total_question_late_today = 0
        
        total_complaint_closed_today = 0
        total_comment_closed_today = 0
        total_question_closed_today = 0
        
        total_ontime_previous = 0
        total_late_previous = 0
        total_closed_previous = 0
        
        total_complaint_percent_today = 0.0
        total_comment_percent_today = 0.0
        total_question_percent_today = 0.0
        
        total_percent_previous = 0.0
        
        
        days_list = ['Today','All Previous']
        days = {'Today':"""  
            (c.create_date_n > TIMESTAMP 'yesterday' and c.create_date_n < TIMESTAMP 'today') or (c.assigned_date > TIMESTAMP 'yesterday' and c.assigned_date < TIMESTAMP 'today') or 
         
            (c.solved_date > TIMESTAMP 'yesterday' and c.solved_date < TIMESTAMP 'today') """,
            
            'All Previous':"""  (c.create_date_n < TIMESTAMP 'yesterday') or (c.assigned_date < TIMESTAMP 'yesterday') or
         
            (c.solved_date < TIMESTAMP 'yesterday') """}
        days_closed = {
                       'Today' : """ (c.state='closed') and (c.date_closed > TIMESTAMP 'yesterday' and c.date_closed < TIMESTAMP 'today') and ( c.date_closed - c.create_date_n %s '6 day'::interval) """,
                       'All Previous': """ (c.state='closed') and (c.date_closed < TIMESTAMP 'yesterday') and (c.date_closed - c.create_date_n  %s '6 day'::interval) """
                       
                       }
        
        select = "select "
        claim_column = " c.claimcateg as claimcateg, "
        state_column = " c.state as state, "
        count_column = " count(*) as nbr  from  maw_claim c " 
        where = """ where %s  """
        group_by_categ_state = " group by c.claimcateg, c.state "
        group_by_state = " group by c.state "
        group_by_categ = " group by c.claimcateg "
        
        for key in days_list:
            if key =='Today':
                ##### For all states except Close state
                query = select + claim_column + state_column + count_column + where + group_by_categ_state
                query = query % (days[key]) 
                self.env.cr.execute(query) 
                records = self.env.cr.fetchall()
                for record in records:
                    if res_dict.get(support.get(record[0],False),False):
                        inner_dict = res_dict[support.get(record[0],False)]
                        inner_dict[record[1]]=record[2]
                    
                        res_dict[support.get(record[0],False)]= inner_dict
                    else:
                        res_dict[support.get(record[0],False)]= {"level":1,record[1]:record[2]}
                        
                    if record[1]=='opened':
                        total_opened += record[2]
                    if record[1]=='assigned': 
                        total_assigned += record[2]
                    if record[1]=='solved': 
                        total_solved += record[2]
                        
                ##### For close state on time
                query = select + claim_column + state_column + count_column + where + group_by_categ_state
                query = query % (days_closed[key]  % ("<"))
                self.env.cr.execute(query) 
                records = self.env.cr.fetchall()
                for record in records:
                    if res_dict.get(support.get(record[0],False),False):
                        inner_dict = res_dict[support.get(record[0],False)]
                        inner_dict['ontime']=record[2]
                    
                        res_dict[support.get(record[0],False)]= inner_dict
                    else:
                        res_dict[support.get(record[0],False)]= {"level":1,'ontime':record[2]}
                    
                    if record[0]=='comment':
                        total_comment_ontime_today += record[2]
                    if record[0]=='question': 
                        total_question_ontime_today += record[2]
                    if record[0]=='claim': 
                        total_complaint_ontime_today += record[2]
                        
                ##### For close state late
                query = select + claim_column + state_column + count_column + where + group_by_categ_state
                query = query % (days_closed[key]  % (">"))
                self.env.cr.execute(query) 
                records = self.env.cr.fetchall()
                for record in records:
                    if res_dict.get(support.get(record[0],False),False):
                        inner_dict = res_dict[support.get(record[0],False)]
                        inner_dict['late']=record[2]
                    
                        res_dict[support.get(record[0],False)]= inner_dict
                    else:
                        res_dict[support.get(record[0],False)]= {"level":1,'late':record[2]}
                        
                    if record[0]=='comment':
                        total_comment_late_today += record[2]
                    if record[0]=='question': 
                        total_question_late_today += record[2]
                    if record[0]=='claim': 
                        total_complaint_late_today += record[2]
                        
                #### For Close Total = (late + ontime)
                if res_dict.get('Comment',False):
                    inner_dict = res_dict['Comment']
                    total_comment_closed_today = total_comment_late_today + total_comment_ontime_today 
                    #### For % On time
                    total_comment_percent_today = (float(total_comment_ontime_today)/float(total_comment_closed_today))*100.0 if total_comment_ontime_today else 0.0
                    inner_dict['total']= total_comment_closed_today
                    inner_dict['percent'] = round(total_comment_percent_today,2)
                    res_dict['Comment']= inner_dict
                    
                if res_dict.get('Question',False):
                    inner_dict = res_dict['Question']
                    total_question_closed_today = total_question_late_today + total_question_ontime_today
                    inner_dict['total']= total_question_closed_today
                    #### For % On time
                    total_question_percent_today = (float(total_question_ontime_today)/float(total_question_closed_today))*100.0 if total_question_closed_today else 0.0
                    inner_dict['percent'] = round(total_question_percent_today,2)
                    res_dict['Question']= inner_dict
                    
                if res_dict.get('Complaint',False):
                    inner_dict = res_dict['Complaint']
                    total_complaint_closed_today = total_complaint_late_today + total_complaint_ontime_today
                    inner_dict['total']= total_complaint_closed_today
                    #### For % On time
                    total_complaint_percent_today = (float(total_complaint_ontime_today)/float(total_complaint_closed_today))*100.0 if total_complaint_closed_today else 0.0
                    inner_dict['percent']= round(total_complaint_percent_today,2)
                    res_dict['Complaint']= inner_dict
                    
                        
                ##### for % on Time
                
                
                        
            else:
                ##### All Previous ############
                ##### For all states except Close state
                query = select + state_column + count_column + where + group_by_state
                query = query % (days[key]) 
                self.env.cr.execute(query) 
                records = self.env.cr.fetchall()
                for record in records:
                    if prev_res_dict.get(key,False):
                        inner_dict = prev_res_dict[key]
                        inner_dict[record[0]]=record[1]
                    
                        prev_res_dict[key]= inner_dict
                    else:
                        prev_res_dict[key]= {"level":0,record[0]:record[1]}
                    
                    if record[0]=='opened':
                        total_opened += record[1]
                    if record[0]=='assigned': 
                        total_assigned += record[1]
                    if record[0]=='solved': 
                        total_solved += record[1]
                    
                    
                ##### For close state on time    
                query = select + state_column + count_column + where + group_by_state
                query = query % (days_closed[key]  % ("<"))
                self.env.cr.execute(query) 
                records = self.env.cr.fetchall()
                for record in records:
                    if prev_res_dict.get(key,False):
                        inner_dict = prev_res_dict[key]
                        inner_dict['ontime']= record[1]
                        prev_res_dict[key]= inner_dict
                    else:
                        prev_res_dict[key]= {"level":0,"ontime":record[1]}
                    total_ontime_previous += record[1]
                    
                
                ##### For close state late
                
                query = select + state_column + count_column + where + group_by_state
                query = query % (days_closed[key]  % (">"))
                self.env.cr.execute(query) 
                records = self.env.cr.fetchall()
                for record in records:
                    if prev_res_dict.get(key,False):
                        inner_dict = prev_res_dict[key]
                        inner_dict['late']= record[1]
                        prev_res_dict[key]= inner_dict
                    else:
                        prev_res_dict[key]= {"level":0,"late":record[1]}
                    total_late_previous += record[1]
                    
                    
                #### For Close Total = (late + ontime)
                total_closed_previous = total_ontime_previous + total_late_previous
                total_percent_previous = (float(total_ontime_previous)/float(total_closed_previous))*100.0 if total_closed_previous else 0.0
                if prev_res_dict.get(key,False):
                    inner_dict = prev_res_dict[key]
                    inner_dict['total']= total_closed_previous
                    #### For % On time
                    inner_dict['percent']= round(total_percent_previous,2)
                    prev_res_dict[key]= inner_dict
                else:
                    prev_res_dict[key]= {"level":0,"total":total_closed_previous,'percent':total_percent_previous}
                
        data_list = res_dict.items()
        final_list = [("Today",{"level":0,"header":True})] + data_list + prev_res_dict.items()
        
        total_ontime = total_ontime_previous + total_comment_ontime_today + total_complaint_ontime_today + total_question_ontime_today
        total_late = total_late_previous + total_comment_late_today + total_complaint_late_today + total_question_late_today
        total_closed = total_closed_previous + total_comment_closed_today + total_complaint_closed_today + total_question_closed_today
        total_percent = (total_percent_previous + total_comment_percent_today + total_complaint_percent_today + total_question_percent_today)/4.0
        
        total_row = ('Total', {'opened':total_opened,'assigned':total_assigned,'solved':total_solved,'ontime':total_ontime,
                         'late' : total_late,'total':total_closed,'bold':1
                               
                    })
        final_list.append(total_row)
        
#         data_list = [  (u'Today',{u'level':0,u'header':True}),
#                       (u'comment', {u'opened': 1L,u'level':1}),
#                       (u'All Previous', {u'opened': 9L, u'closed': 1L,u'level':0})
#                     ]
            
        return final_list
    
    
    def get_datas_monthly_old(self, data):
        data_list = []
        res_dict = {}
        support = {'claim':'Complaint','comment':'Comment','question':'Question'}
        total_opened = 0
        total_assigned = 0
        total_solved = 0
        total_opened_avg = 0.0
        total_assigned_avg = 0.0
        total_solved_avg = 0.0
        total_avg_time = 0.0
        total_items = 0
        
        ###total calculation by claimcateg and state
        self.env.cr.execute("""select c.claimcateg as claimcateg, c.state as state, count(*) as nbr,
        avg(extract('epoch' from (c.first_assigned_date-c.create_date_n))/(3600)) as  open_average_time,
        avg(extract('epoch' from (c.solved_date - c.first_assigned_date))/(3600)) as  assigned_average_time,
        avg(extract('epoch' from (c.date_closed - c.solved_date))/(3600)) as  solved_average_time,
        avg(extract('epoch' from (c.date_closed - c.create_date_n))/(3600)) as  open_comment_question
          
        from maw_claim c 
        
        group by c.claimcateg, c.state"""  )
        records = self.env.cr.fetchall()
        
        for record in records:
            if res_dict.get(support.get(record[0],False),False):
                inner_dict = res_dict[support.get(record[0],False)]
                inner_dict[record[1]]=record[2]
                inner_dict['open_average_time']+=round(record[3] or 0.0,2)
                inner_dict['assigned_average_time']+=round(record[4] or 0.0,2) 
                inner_dict['solved_average_time']+=round(record[5] or 0.0,2) 
                total_opened_avg += round(record[3] or 0.0,2)
                total_assigned_avg += round(record[4] or 0.0,2) 
                total_solved_avg += round(record[5] or 0.0,2) 
                
                res_dict[support.get(record[0],False)]= inner_dict
                if record[1]=='opened':
                    total_opened += record[2]
                if record[1]=='assigned': 
                    total_assigned += record[2]
                if record[1]=='solved': 
                    total_solved += record[2]
            else:
                res_dict[support.get(record[0],False)]= {record[1]:record[2],"open_average_time":round(record[3] or 0.0,2),'assigned_average_time':round(record[4] or 0.0,2) ,'solved_average_time':round(record[5] or 0.0,2) }
                total_opened_avg += round(record[3] or 0.0,2)
                total_assigned_avg += round(record[4] or 0.0,2) 
                total_solved_avg += round(record[5] or 0.0,2) 
                if record[1]=='opened':
                    total_opened += record[2]
                if record[1]=='assigned': 
                    total_assigned += record[2]
                if record[1]=='solved': 
                    total_solved += record[2]
        
        
        ###total calculation by claimcateg
        
        self.env.cr.execute("""select c.claimcateg as claimcateg, count(*), 
        avg(extract('epoch' from (c.first_assigned_date-c.create_date_n))/(3600)) as  open_average_time,
        avg(extract('epoch' from (c.solved_date - c.first_assigned_date))/(3600)) as  assigned_average_time,
        avg(extract('epoch' from (c.date_closed - c.solved_date))/(3600)) as  solved_average_time 
        from maw_claim c where c.state not in ('new','closed') group by c.claimcateg
        """)   
        total_records = self.env.cr.fetchall()
        
        for record in total_records:
            if res_dict.get(support.get(record[0],False),False):
                inner_dict = res_dict[support.get(record[0],False)]
                inner_dict['total']=record[1]
                inner_dict['total_average_time']=round(record[2] or 0.0,2) + round(record[3] or 0.0,2) + round(record[4] or 0.0,2)
                total_avg_time += inner_dict['total_average_time']
                total_items += inner_dict['total']
                res_dict[support.get(record[0],False)]= inner_dict
            else:
                res_dict[support.get(record[0],False)]= {'total':record[1]}
                
        data_list= res_dict.items()
        
        total_complaints = total_opened + total_assigned + total_solved
        total_time = total_assigned_avg + total_opened_avg + total_solved_avg
        total_row = ('Total/Average', {'opened':total_opened,'assigned':total_assigned,'solved':total_solved,'total':total_items,
                         'open_average_time' : round(total_opened_avg,2),'assigned_average_time':round(total_assigned_avg,2),'solved_average_time':round(total_solved_avg,2),
                         'total_average_time':  (total_avg_time/3) 
                               
                    })
        data_list.append(total_row)
        return data_list
    
    def get_datas_monthly(self, data):
        date_from = data.date_from
        date_to = data.date_to
        data_list = []
        res_dict = {}
        support = {'claim':'Complaint','comment':'Comment','question':'Question'}
        total_opened = 0
        total_assigned = 0
        total_solved = 0
        total_opened_avg = 0.0
        total_assigned_avg = 0.0
        total_solved_avg = 0.0
        total_avg_time = 0.0
        total_items = 0
        
        ###total calculation by claimcateg and state
        self.env.cr.execute("""select c.claimcateg as claimcateg, c.state as state, count(*) as nbr,
        case when avg(c1.open_average_time) is null then avg(c2.open_average_time) else avg(c1.open_average_time) end,
        avg(c1.assigned_average_time),
        avg(c1.solved_average_time),
        
        COALESCE(case when avg(c1.open_average_time) is null then avg(c2.open_average_time) else avg(c1.open_average_time) end,0)+COALESCE(avg(c1.assigned_average_time),0)+COALESCE(avg(c1.solved_average_time),0) as sumavg
        
        from maw_claim c 

        left outer join (select id, CASE WHEN (create_date_n >= '%s' AND create_date_n <= '%s') is TRUE THEN extract('epoch' from (first_assigned_date-create_date_n))/3600/24 ELSE 0 END as open_average_time, 
        CASE WHEN (first_assigned_date >= '%s' AND first_assigned_date <= '%s') is TRUE THEN extract('epoch' from (solved_date - first_assigned_date))/3600/24 ELSE 0 END as assigned_average_time,
        CASE WHEN (solved_date >= '%s' AND solved_date <= '%s') is TRUE THEN extract('epoch' from (date_closed - solved_date))/3600/24 ELSE 0 END  as solved_average_time
    
        from maw_claim where claimcateg='claim' group by id) as c1 on c1.id=c.id

        left join (select id, CASE WHEN (create_date_n >= '%s' AND create_date_n <= '%s') is TRUE THEN extract('epoch' from (date_closed-create_date_n))/3600/24 ELSE 0 END as  open_average_time
    
        from maw_claim where claimcateg='comment' or claimcateg='question' group by id) as c2 on c2.id=c.id
        
        where (create_date_n >= '%s' AND create_date_n <= '%s') OR (first_assigned_date >= '%s' AND first_assigned_date <= '%s')
                                OR (solved_date >= '%s' AND solved_date <= '%s') OR (date_closed >= '%s' AND date_closed <= '%s')
        
        group by c.state, c.claimcateg
        """ % (date_from,date_to,date_from,date_to,date_from,date_to,date_from,date_to,date_from,date_to,date_from,date_to,date_from,date_to,date_from,date_to)   )
        records = self.env.cr.fetchall()
        
        for record in records:
            if res_dict.get(support.get(record[0],False),False):
                inner_dict = res_dict[support.get(record[0],False)]
                inner_dict[record[1]]=record[2]
                inner_dict['total']+= record[2] if record[1] not in ['closed','new'] else 0
                inner_dict['open_average_time']+=round(record[3] or 0.0,4)
                inner_dict['assigned_average_time']+=round(record[4] or 0.0,4) 
                inner_dict['solved_average_time']+=round(record[5] or 0.0,4) 
                inner_dict['total_average_time']+=round(record[6] or 0.0,4) 
                total_opened_avg += round(record[3] or 0.0,4)
                total_assigned_avg += round(record[4] or 0.0,4) 
                total_solved_avg += round(record[5] or 0.0,4)
                total_avg_time += round(record[6] or 0.0,4) 
                if record[1] not in ['closed','new']:
                    total_items += record[2]
                
                res_dict[support.get(record[0],False)]= inner_dict
                if record[1]=='opened':
                    total_opened += record[2]
                if record[1]=='assigned': 
                    total_assigned += record[2]
                if record[1]=='solved': 
                    total_solved += record[2]
            else:
                res_dict[support.get(record[0],False)]= {record[1]:record[2],"open_average_time":round(record[3] or 0.0,4),"total":record[2] if record[1] not in ['closed','new'] else 0,
                                                         'assigned_average_time':round(record[4] or 0.0,4) ,'solved_average_time':round(record[5] or 0.0,4),
                                                         'total_average_time':round(record[6] or 0.0,4)
                                                          }
                total_opened_avg += round(record[3] or 0.0,4)
                total_assigned_avg += round(record[4] or 0.0,4) 
                total_solved_avg += round(record[5] or 0.0,4) 
                
                total_avg_time += round(record[6],2) 
                if record[1] not in ['closed','new']:
                    total_items += record[2] 
                
                if record[1]=='opened':
                    total_opened += record[2]
                if record[1]=='assigned': 
                    total_assigned += record[2]
                if record[1]=='solved': 
                    total_solved += record[2]
        
        data_list= res_dict.items()
        
        total_row = ('Total/Average', {'opened':total_opened,'assigned':total_assigned,'solved':total_solved,'total':total_items,
                         'open_average_time' : round(total_opened_avg,2),'assigned_average_time':round(total_assigned_avg,2),'solved_average_time':round(total_solved_avg,2),
                         'total_average_time':  (round(total_avg_time/3,2)) ,'bold':1
                               
                    })
        data_list.append(total_row)
        return data_list
    
    def get_datas_ondemand(self, data):
        data_list = []
        days_list = ['7-10','11-15','16-30','31-60','61+']
        days = {'7-10':(6,10),'11-15':(10,15),'16-30':(15,30),'31-60':(30,60),'61+':(60,60)}
        select = "select "
        claim_column = " c.claimcateg as claimcateg, "
        count_column = " count(*) as nbr  from  maw_claim c " 
        where_between = """ where c.state %s 'closed' and c.state <> 'new' and ((current_date -  c.create_date_n   > '%s day'::interval)) and 
                         
                         ((current_date -  c.create_date_n   <= '%s day'::interval)) """
        where_above = " where c.state %s 'closed' and c.state <> 'new' and ((current_date -  c.create_date_n   > '%s day'::interval)) "
        group_by = " group by c.claimcateg "
        
        for key in days_list:
            not_closed_query = ""
            closed_query = ""
            value = days[key]
            if value[0]!=value[1]:
                query = select + count_column + where_between 
                not_closed_query = query % ('<>', str(value[0]) , str(value[1]) )
                
                query = select + claim_column +  count_column + where_between + group_by
                closed_query = query % ('=', str(value[0]) , str(value[1]) )
            else:
                query = select + count_column + where_above 
                not_closed_query = query % ('<>', str(value[0]) )
                
                query = select + claim_column + count_column + where_above + group_by
                closed_query = query % ('=', str(value[0]) )
            
            #fetch items that are closed
            self.env.cr.execute(closed_query) 
            records = self.env.cr.fetchall()
            vals = {}
            if records:
                vals = dict(records)
                vals['total'] = sum(vals.values())
            
            #fetch items that are not closed    
            self.env.cr.execute(not_closed_query) 
            records = self.env.cr.fetchall()
            if records:
                vals['not_closed'] = records[0][0]
                
            data_list.append([key,vals])
        
        vals = {}
        
        total_closed_query = "select  c.claimcateg as claimcateg,  count(*) as nbr  from  maw_claim c  where c.state = 'closed' and c.state <> 'new' and ((current_date -  c.create_date_n   > '6 day'::interval)) group by c.claimcateg"
        self.env.cr.execute(total_closed_query) 
        records = self.env.cr.fetchall()
        if records:
            vals = dict(records)
            vals['total'] = sum(vals.values())
        
        total_not_closed_query = "select  count(*) as nbr  from  maw_claim c  where c.state <> 'closed' and c.state <> 'new' and ((current_date -  c.create_date_n   > '6 day'::interval))"
        self.env.cr.execute(total_not_closed_query) 
        records = self.env.cr.fetchall()
        if records:
            vals['not_closed'] = records[0][0]
        #to make this row bold in report
        vals['bold'] = 1
            
        data_list.append(['Total',vals])
            
        return data_list


