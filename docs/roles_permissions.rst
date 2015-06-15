***********************
Roles and Permissions
***********************

Mission
#######
Manage specimens and aliquots.

Roles
################

==============   =================================================================================================
Name             Comment
==============   =================================================================================================
administrator    Complete access to all functionality of the application. Few people should have this level.
manager          Manages the content of the application
worker           Can view and process data
member           Limited view access
==============   =================================================================================================


Permissions
############

Lims
*******
``/lims``

==============  ====
Name            view
==============  ====
administrator   X
manager         X
worker          X
member          X
==============  ====


``/lims/{lab}/*``

==============  ====  ========
Name            view  process
==============  ====  ========
administrator   X     X
manager         X     X
worker          L     L
member          L
==============  ====  ========

