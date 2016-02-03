# -*- coding: utf-8 -*-

{
    "name": "mawgif_support",
    "version": "1.0",
    "author": "fore-vision -- Almusbah group",
    "category" : "Project Management",
    "images": [],
    "depends": ["base_setup",
                "mail",
                "email_template",
                "website"             
                ],
    "complexity": "easy",
    "description": """
Module to manage mawgif customer claims
""",
    "data":[
                  'security/maw_security.xml',
                  'security/ir.model.access.csv',
                  "view/a_basic_menues.xml",
                  "wizard/claim_report_print_wiz_view.xml",
                  "report/report_monthly_claim.xml",
                  "report/report_ondemand_claim.xml",
                  "report/report_daily_claim.xml",
                  "mawgif_report.xml",
                  "view/country.xml",
                  "data/country_data.xml",
                  "view/mawgif_claim.xml",
                  "data/cron_data.xml",
                  "view/city.xml",
                  "view/district.xml",
                  'view/complaint_type.xml',
                  'view/notification.xml',
                  'data/notificaiton_data.xml',
                  "data/complaint_type_data.xml",
                  "data/email_template.xml",
                  'view/maw_claim_sequence.xml',
                  'data/website_mawgif_data.xml',
                  'view/website_mawgif.xml',
                  ],
    "test": [],
    "auto_install": False,
    "installable": True,

}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
