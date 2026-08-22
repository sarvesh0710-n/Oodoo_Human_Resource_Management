{
    'name': 'Dayflow HRMS',
    'version': '17.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Human Resource Management System for Dayflow',
    'description': """
        Dayflow HRMS digitizes employee onboarding, profile management,
        attendance, leave management, and payroll visibility.
    """,
    'author': 'Dayflow Team',
    'depends': [
        'base',
        'hr',
        'hr_attendance',
        'hr_holidays',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
