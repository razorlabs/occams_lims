from datetime import datetime

import sqlalchemy as sa

from zope.component import queryUtility
from zope.component import getUtility
from zope.app.intid.interfaces import IIntIds

from z3c.relationfield import RelationValue

from Products.CMFCore.utils import getToolByName

from plone.dexterity.utils import addContentToContainer
from plone.dexterity.utils import createContent

from avrc.aeh import Logger as default_logger
from avrc.data.store.interfaces import IDatastore

from zope.schema import Float 

############################################################################################
# 1) Make sure that blueprint zid has been added as a column to specimen 
# 2) First we need to create a Default Research Lab
# 3) Then we need to iterate through each study and cycle and find all the specimen
# 4) For each specimen, either create a new Specimen and Aliquot Blueprint or retrieve the id of the one that is already created 
# 5) Once that is finished, we need to add the specimen that we retrieved to the related_specimen of the study and/or cycle
############################################################################################


def import_(context, logger=default_logger):
    """ Applies form changes
        No current way to modify fields, so we'll have to do this manually.
    """
    logger.info(u'Upgrading Datastores')

    datastore = queryUtility(IDatastore, u'fia', context) 

    # 1) Make sure that blueprint zid has been added as a column to specimen 
    addBlueprintColumn(context, datastore)

    # 2) First we need to create a Default Research Lab
    research_lab = addDefaultResearchLab(context)


    # 3) Create Default Specimen 
    bp_ids = createDefaultSpecimenBlueprints(research_lab)

    # 4) Collect Specimen
    collectSpecimen(context, bp_ids)

    logger.info(u'Upgrade complete')


def addBlueprintColumn(context, datastore):#{{{

    engine = datastore.getScopedSession().bind
    metadata = sa.MetaData(bind=engine)
    metadata.reflect(only=['specimen'])
    columns = metadata.tables['specimen'].columns

    if 'blueprint_zid' not in columns:
        sa.DDL('ALTER TABLE "specimen" ADD "blueprint_zid" int').execute(engine)
#}}}

def addDefaultResearchLab(context):#{{{
    """ 
    No current way to modify fields, so we'll have to do this manually.
    """

    catalog = getToolByName(context, 'portal_catalog')
    institutes = catalog(portal_type='avrc.aeh.institute')

    #Just choose the first institute. There should only be one, right?
    institute = institutes[0].getObject()
    #Create a new research lab.
    research_lab = createContent('hive.lab.researchlab', title="Default Lab", page_height=11.,page_width=8.5,top_margin=0.25,
                                 side_margin=0.78,vert_pitch=0.625,horz_pitch=1.41,label_height=0.50,label_width=1.28,
                                 label_round=0.1,no_across=5,no_down=17)

    #Add the research lab to the institute
    addContentToContainer(institute, research_lab, checkConstraints=False)
    research_lab = institute[research_lab.getId()]

    #Go ahead and return the research lab for future use
    return research_lab

#}}}

def createDefaultSpecimenBlueprints(research_lab):#{{{
    #Here we go through each of the interface templates, and do each one


    #These can simply be called default specimen types

    #Default Types and Aliquot
    #ACD
    acd = createContent('hive.lab.specimenblueprint', title=(u'Default ACD'), type=u'acd',default_tubes=3,tube_type=u'acdyellowtop')

    acd_aliquot_plasma = createContent('hive.lab.aliquotblueprint', title=(u'Default ACD Plasma Aliquot'), aliquot_type=u'plasma',volume=1.0)
    acd_aliquot_pbmc5  = createContent('hive.lab.aliquotblueprint', title=(u'Default ACD PBMC 5 Aliquot'), aliquot_type=u'pbmc',volume=5.0)
    acd_aliquot_pbmc10 = createContent('hive.lab.aliquotblueprint', title=(u'Default ACD PBMC 10 Aliquot'), aliquot_type=u'pbmc',volume=10.0)


    #Add Aliquot to Specimen
    addContentToContainer(research_lab, acd, checkConstraints=False)
    acd = research_lab[acd.getId()]

    addContentToContainer(acd, acd_aliquot_plasma, checkConstraints=False) 
    addContentToContainer(acd, acd_aliquot_pbmc5, checkConstraints=False) 
    addContentToContainer(acd, acd_aliquot_pbmc10, checkConstraints=False) 


    #Genital Secretion
    genitals = createContent('hive.lab.specimenblueprint', title=(u'Default Genital Secretion'), type=u"genital-secretion",tube_type=u'gskit')
    genitals_aliquot_gscells = createContent('hive.lab.aliquotblueprint', title=(u'Default Genital Secretion GS Cells Aliquot'), aliquot_type=u'gscells', cell_amount=1.0)
    genitals_aliquot_gsplasma = createContent('hive.lab.aliquotblueprint', title=(u'Default Genital Secretion GS Plasma Aliquot'), aliquot_type=u'gsplasma',volume=1.0)

    #Add Aliquot to Specimen
    addContentToContainer(research_lab, genitals, checkConstraints=False)
    genitals = research_lab[genitals.getId()]
    
    addContentToContainer(genitals, genitals_aliquot_gscells, checkConstraints=False) 
    addContentToContainer(genitals, genitals_aliquot_gsplasma, checkConstraints=False) 


    #CSF
    csf = createContent('hive.lab.specimenblueprint', title=(u'Default CSF'), type=u"csf",default_tubes=2,tube_type=u'csf')

    csf_aliquot = createContent('hive.lab.aliquotblueprint', title=(u'Default CSF Aliquot'), aliquot_type=u'csf')
    
    csf_aliquot_pellet = createContent('hive.lab.aliquotblueprint', title=(u'Default CSF Pellet Aliquot'), aliquot_type=u'csfpellet')

    #Add Aliquot to Specimen
    addContentToContainer(research_lab, csf, checkConstraints=False)
    csf = research_lab[csf.getId()]

    addContentToContainer(csf, csf_aliquot, checkConstraints=False) 
    addContentToContainer(csf, csf_aliquot_pellet, checkConstraints=False) 

    #Serum
    serum = createContent('hive.lab.specimenblueprint', title=(u'Default Serum'), type=u"serum",default_tubes=1,tube_type=u'10mlsst')
    serum_aliquot = createContent('hive.lab.aliquotblueprint', title=(u'Default Serum Aliquot'), aliquot_type=u'serum',volume=1.0)

    #Add Aliquot to Specimen
    addContentToContainer(research_lab, serum, checkConstraints=False)
    serum = research_lab[serum.getId()]
    addContentToContainer(serum, serum_aliquot, checkConstraints=False) 

    #Swab
    swab = createContent('hive.lab.specimenblueprint', title=(u'Default Swab'), type=u"swab",default_tubes=1,tube_type=u'dacronswab')
    swab_aliquot = createContent('hive.lab.aliquotblueprint', title=(u'Default Swab Aliquot'), aliquot_type=u'swab')

    #Add Aliquot to Specimen
    addContentToContainer(research_lab, swab, checkConstraints=False)
    swab = research_lab[swab.getId()]
    addContentToContainer(swab, swab_aliquot, checkConstraints=False) 

    #RS-GUT
    rs_gut  = createContent('hive.lab.specimenblueprint', title=(u'Default RS-Gut'), type=u"rs-gut",default_tubes=1,tube_type=u"rs-gut")
    rs_gut_aliquot = createContent('hive.lab.aliquotblueprint', title=(u'Default RS-Gut Aliquot'), aliquot_type=u'rs-gut')

    #Add Aliquot to Specimen
    addContentToContainer(research_lab, rs_gut, checkConstraints=False)
    rs_gut = research_lab[rs_gut.getId()]
    addContentToContainer(rs_gut, rs_gut_aliquot, checkConstraints=Falset) 

    #TI-GUT
    ti_gut  = createContent('hive.lab.specimenblueprint', title=(u'Default TI-Gut'), type=u"ti-gut" ,default_tubes=1,tube_type=u"ti-gut")
    ti_gut_aliquot = createContent('hive.lab.aliquotblueprint', title=(u'Default TI-Gut Aliquot'), aliquot_type=u'ti-gut')

    #Add Aliquot to Specimen
    addContentToContainer(research_lab, ti_gut, checkConstraints=False)
    ti_gut = research_lab[ti_gut.getId()]
    addContentToContainer(ti_gut, ti_gut_aliquot, checkConstraints=False) 


    #Return the ids
    intids = getUtility(IIntIds)
    bp_ids = { u"AnalSwab": [u"anal", intids.getId(swab)],
               u"ACD": [u"acd", intids.getId(acd)],
               u"CSF":[u"csf", intids.getId(csf)],
               u"Serum": [u"serum", intids.getId(serum)],
               u"GenitalSecretions": [u"genital-secretion", intids.getId(genitals)],
               u"RSGut":[u"rs-gut", intids.getId(rs_gut)],
               u"TIGut": [u"ti-gut", intids.getId(ti_gut)],
              }

    return bp_ids

#}}}

def collectSpecimen(context, bp_ids):#{{{
    #""" 
    #No current way to modify fields, so we'll have to do this manually.
    #"""

    #Grab the Default Blueprints:
    catalog = getToolByName(context, 'portal_catalog')
    bp_brains = catalog(portal_type='hive.lab.specimenblueprint')
   
    #Iterate through all the studies and cycles 

    #We have to move both the available_specimen and required_specimen to related_specimen
    #If there is not a matching specimen blueprint, then create one. 
 
    catalog = getToolByName(context, 'portal_catalog')
    brains = catalog(portal_type='avrc.aeh.study')

    for brain in brains:
        study = brain.getObject()
        if study.available_specimen:
            for specimen in study.available_specimen:
                #Find the related blueprint specimen
                #We should make sure this is saved
                if specimen.__name__ in bp_ids.keys():
                    study.related_specimen.append(RelationValue(bp_ids[specimen.__name__][1]))
                    study.reindexObject()
                else:
                    print specimen.__name__
                    print "there was a problem, lacked a default specimen"


    catalog = getToolByName(context, 'portal_catalog')
    brains = catalog(portal_type='avrc.aeh.cycle')
    for brain in brains:
        cycle = brain.getObject()
        if cycle.required_specimen:
            for specimen in cycle.required_specimen:
                #Find the related blueprint specimen
                #We should make sure this is saved
                if specimen.__name__ in bp_ids.keys():
                    cycle.related_specimen.append(RelationValue(bp_ids[specimen.__name__][1]))
                    cycle.reindexObject()
                else:
                    print specimen.__name__
                    print "there was a problem, lacked a default specimen"
##}}}
