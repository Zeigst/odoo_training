# -*- coding: utf-8 -*-
{
    "name": "Custom Inventory",
    "summary": "Custom Inventory",
    "description": """
        Custom Inventory
    """,
    "author": "MinhCH",
    "category": "Inventory",
    "version": "17.0.0.1.0",
    "depends": ["base", "stock"],
    "data": [
        "security/ir.model.access.csv",
        "views/stock_movement_report_wizard_view.xml",
        "views/stock_movement_report_view.xml",
        "views/menu_view.xml",
    ],
    "license": "LGPL-3"
}