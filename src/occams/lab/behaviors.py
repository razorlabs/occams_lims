# """
# Data entry functionality
# """
# from zope.interface import implements


# from occams.lab import interfaces
# from rwproperty import getproperty, setproperty

# from zope.component import adapts

# from avrc.aeh.interfaces import IStudy
# from occams.lab import SCOPED_SESSION_KEY
# from z3c.saconfig import named_scoped_session
# from occams.lab import model
# from avrc.aeh.interfaces import IClinicalMarker
# from sqlalchemy.orm import object_session

# class AvailableSpecimen(object):
#     """
#     """
#     implements(interfaces.IAvailableSpecimen)
#     adapts(IStudy)

#     def __init__(self, context):
#         self.context = context
    
#     @getproperty
#     def related_specimen(self):
#         session = named_scoped_session(SCOPED_SESSION_KEY)
#         query = (
#             session.query(model.SpecimenType)
#             .join(model.SpecimenType.studies)
#             .filter(model.Study.zid == IClinicalMarker(self.context).zid)
#             )
#         return query.all()

#     @setproperty
#     def related_specimen(self, value):
#         if value is None:
#             value = ()
#         # modelObj = IClinicalMarker(self.context).modelObj()
#         # session = object_session(modelObj)
#         # modelObj.specimen_types = set(value)
#         # session.flush()