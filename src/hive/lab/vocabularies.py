from plone.formwidget.contenttree import ObjPathSourceBinder
from zope.schema.interfaces import IContextSourceBinder
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary

from plone.memoize.instance import memoize

from five import grok

class SpecimenVocabulary(object):
    """
    Context source binder to provide a vocabulary of users in a given group.
    """
    grok.implements(IContextSourceBinder)

    def __init__(self):
        self.property = 'related_specimen'
        self.study = None

#    @memoize
    def getTerms(self, context=None):
        if context.portal_type == 'avrc.aeh.study':
            self.study = context
        elif context.portal_type == 'avrc.aeh.cycle' \
                and getattr(context, "__parent__", None):
            self.study = context.__parent__

        childlist = getattr(self.study, self.property, [])

        terms = []
        for specimen_type in childlist:
            specimen_blueprint = specimen_type.to_object
            terms.append(SimpleTerm(
               title=specimen_blueprint.title,
               token=specimen_type.to_path,
               value=specimen_type))

        return terms

    def __call__(self, context):

        return SimpleVocabulary(terms=self.getTerms(context))


class SpecimenVisitVocabulary(object):
    """
    Context source binder to provide a vocabulary of users in a given group.
    """
    grok.implements(IContextSourceBinder)
    
    def __init__(self):
        self.property = 'related_specimen'
        self.study = None
        
    def cycleVocabulary(self):
        context = self.context.aq_inner
        cycles = context.getCycles()
        termlist=[]
        intids = component.getUtility(IIntIds)
        for cycle in cycles:
            int
            studytitle = cycle.aq_parent.Title()
            cycletitle = '%s, %s' % (studytitle, cycle.Title())
            protocol_zid = intids.getId(cycle)
            termlist.append(SimpleTerm(
                                       title=cycletitle,
                                       token='%s' % protocol_zid,
                                       value=protocol_zid))
        return SimpleVocabulary(terms=termlist)


AliquotStatusVocabulary = SimpleVocabulary(terms=[
                SimpleTerm("checked in", "checked in", u"Aliquot Checked In"),
                SimpleTerm("checked out", "checked out", u"Aliquot Checked Out"),
                SimpleTerm("hold", "hold", u"Aliquot On Hold"),
                ])

AliquotLocationVocabulary = SimpleVocabulary(terms=[
                SimpleTerm("richman lab", "richman lab", u"Richman Lab"),
                SimpleTerm("avrc", "avrc", u"AVRC"),
                ])

AliquotSentAnalysisVocabulary = SimpleVocabulary(terms=[
                SimpleTerm("yes", "yes", u"Yes"),
                SimpleTerm("no", "no", u"No"),
                SimpleTerm("missing", "missing", u"Missing"),
                SimpleTerm("re-checked-in", "re-checked-in", u"Re-checked-in"),
                SimpleTerm("hold removed", "hold removed", u"On Hold Status Removed"),
                ])

AliquotTypeVocabulary = SimpleVocabulary(terms=[
                SimpleTerm("pbmc", "pbmc", u"PBMC"),
                SimpleTerm("plasma", "plasma", u"Plasma"),
                SimpleTerm("semen", "semen", u"Semen"),
                SimpleTerm("serum", "serum", u"Serum"),
                SimpleTerm("swab", "swab", u"Swab"),
                SimpleTerm("csf", "csf", u"CSF"),
                SimpleTerm("genital cells", "genital cells", u"Genital Cells"),
                SimpleTerm("genital plasma", "genital plasma", u"Genital Plasma"),

                ])
        
        
SpecimenDestinationVocabulary = SimpleVocabulary(terms=[
                SimpleTerm("Richman Lab", "Richman Lab", u"Richman Lab"),
                SimpleTerm("UCSD Virology", "UCSD Virology", u"UCSD Virology"),
                SimpleTerm("VA Immunogenetics", "VA Immunogenetics", u"VA Immunogenetics"),
                SimpleTerm("Red Cross", "Red Cross", u"Red Cross"),
                SimpleTerm("LabCorp/Serum Bank", "LabCorp/Serum Bank", u"LabCorp/Serum Bank"),
                SimpleTerm("Blood Centers/Plasma Bank", "Blood Centers/Plasma Bank", u"Blood Centers/Plasma Bank"),
                SimpleTerm("UCSD Micro", "UCSD Micro", u"UCSD Micro"),
                SimpleTerm("Monogram", "Monogram", u"Monogram"),
                SimpleTerm("ARUP", "ARUP", u"ARUP"),
                SimpleTerm("UCSD", "UCSD", u"UCSD"),
                SimpleTerm("Nurse", "Nurse", u"Nurse"),
                SimpleTerm("HNRC", "HNRC", u"HNRC"),
                ])

SpecimenInstructionsVocabulary = SimpleVocabulary(terms=[
                SimpleTerm("AEH Specimen Log", "AEH Specimen Log", u"AEH Specimen Log"),
                SimpleTerm("Richman Lab", "Richman Lab", u"Richman Lab"),
                SimpleTerm("AEH Specimen Bank", "AEH Specimen Bank", u"AEH Specimen Bank"),
                SimpleTerm("Procedure Manual - Store at -70 C", "Procedure Manual - Store at -70 C", u"Procedure Manual - Store at -70 C"),
                ])
                
TubeTypeVocabulary = SimpleVocabulary(terms=[         ##For specimens
                SimpleTerm("3 X 10 ml. ACD Yellow Tops", "3 X 10 ml. ACD Yellow Tops", u"3 X 10 ml. ACD Yellow Tops"),
                SimpleTerm("10 ml. SST", "10 ml. SST", u"10 ml. SST"),
                SimpleTerm("5 ml. Lavender Top", "5 ml. Lavender Top", u"5 ml. Lavender Top"),
                SimpleTerm("2 X 5 ml. PPT Tube", "2 X 5 ml. PPT Tube", u"2 X 5 ml. PPT Tube"),
                SimpleTerm("7 ml. SST/2 X 1.8 ml. cryovials", "7 ml. SST/2 X 1.8 ml. cryovials", u"7 ml. SST/2 X 1.8 ml. cryovials"),
                SimpleTerm("7 ml. ACD Yellow Top/1.8 ml. cryovial", "7 ml. ACD Yellow Top/1.8 ml. cryovial", u"7 ml. ACD Yellow Top/1.8 ml. cryovial"),
                SimpleTerm("10 ml. Red Top", "10 ml. Red Top", u"10 ml. Red Top"),
                SimpleTerm("2.0 ml. ACD plasma; with Detuned Plasma", "2.0 ml. ACD plasma; with Detuned Plasma", u"2.0 ml. ACD plasma; with Detuned Plasma"),
                SimpleTerm("Blue Top Collection Swab/Specimen Collection Kit", "Blue Top Collection Swab/Specimen Collection Kit", u"Blue Top Collection Swab/Specimen Collection Kit"),
                SimpleTerm("6 ml. Red Top", "6 ml. Red Top", u"6 ml. Red Top"),
                SimpleTerm("5 ml. SST/3.6 ml. cryovial", "5 ml. SST/3.6 ml. cryovial", u"5 ml. SST/3.6 ml. cryovial"),
                SimpleTerm("Urine Specimen Container", "Urine Specimen Container", u"Urine Specimen Container"),
                SimpleTerm("Genital Secretion Kit", "Genital Secretion Kit", u"Genital Secretion Kit"),
                SimpleTerm("2-16 ml. CSF", "2-16 ml. CSF", u"2-16 ml. CSF")
                ])
        