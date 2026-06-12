{
    'name' : 'Hotel Management(ps)',
    'version' : '18.0.1.0.0',
    'category' : 'Service/Hotel',
    'installable' : True,
    'application ' : True,
    'auto_install' : False,
    'depends' : ['base','mail'],
    'data' : [
        'security/ir.model.access.csv',
        'views/hotel_room_view.xml',
        'views/hotel_menu.xml',
    ],
}