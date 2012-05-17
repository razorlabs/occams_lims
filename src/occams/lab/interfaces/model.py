# import zope.interface
# import zope.schema
# from occams.datastore.interfaces import ICategory
# from occams.datastore.interfaces import IUser
# from occams.form.interfaces import IDataBaseItemContext
# from occams.datastore.interfaces import IReferenceable
# from occams.datastore.interfaces import IDescribeable
# from occams.datastore.interfaces import IModifiable

# from avrc.aeh.interfaces import IClinicalModel

# from hive.lab import MessageFactory as _

# class ILocation(IDescribeable, IReferenceable, IModifiable):
#     """
#     """
#     value = zope.schema.TextLine(
#         title=_(u"Location Value"),
#         description=_(u"Vocabulary value for this location"),
#         required=True
#         )

# class ISpecialInstruction(IDescribeable, IReferenceable, IModifiable):
#     """
#     """
#     value = zope.schema.TextLine(
#         title=_(u"Special Instruction Value"),
#         description=_(u"Vocabulary value for this special instruction"),
#         required=True
#         )


# class ISpecimenType(IDescribeable, IReferenceable, IClinicalModel, IModifiable):
#     """
#     """
#     tube_type = zope.schema.TextLine(
#         title=_(u"Type of tube"),
#         description=_(u"The Type of tube used for this specimen type"),
#         required=True
#         )

# class IAliquotType(IDescribeable, IReferenceable, IClinicalModel, IModifiable):
#     """
#     """
#     specimen_type = zope.schema.Object(
#         title=_(u"Type of specimen"),
#         description=_(u"The Type specimen from which this aliquot type is derived"),
#         required=True,
#         schema= ISpecimenType
#         )


# class ISpecimen(IReferenceable, IModifiable):
#     """
#     """

# class IAliquot(IReferenceable, IModifiable):
#     """
#     """

