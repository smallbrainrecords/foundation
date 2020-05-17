Frontend include 3 module based on system roles
- Admin module:
- Staff module:
- Patient module:
- Common/Shared module:
    - All directives (Have controller, template) will be deprecated and need to be migrate to component based
    - All component (Have controller, template)filter
    - All filters (Each filter is single file)
    - All services (Each service is single file)
Date format: MM/DD/YYYY for display
Date format for alternative inputs
Date format for data transmitting between client and server: ISO8601


TODO list
[ ] Unify how datepicker is initialized.
[ ] Single entry for interceptor
[ ] Unify document & attachment
[ ] Backend API document
[ ] https://trello.com/c/v1o5iEi1
- UX while change user's type but did not saved the change the hidden UI being showed. This behavior could be a vulnerable to change personal information if you have right to changing the user's type.
[ ] UX for navigation backward then forward
[ ] Labeled todo list UI & UX ->hold all
[ ] Unify all service to single modules
