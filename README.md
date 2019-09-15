
# Shale Well Completion Optimization
-- a free web app for shale oil and gas drilling and well completion optimization for max production/profit margin

# functions:
  1. user management
  2. well data management
  3. well completion parameters vs. production prediction modeling
  4. modeling result chart displays

# structure:

```
── shaleoptim/
│   ├── __init__.py
│   ├── db.py             (data request)
│   ├── schema.sql        (database initiation)
│   ├── auth.py
│   ├── wells.py          (well data management and modeling)
│   ├── templates/
│   │   ├── base.html
│   │   ├── auth/
│   │   │   ├── login.html
│   │   │   └── register.html
│   │   └── welss/
│   │       ├── create.html
│   │       ├── index.html
│   │       └── update.html
│   └── static/
│       └── style.css
└── instance/     
    └── shale.sqlite  (database)     
```       
