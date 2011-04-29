""" Defines available datatstore specimen/aliquot terms for vocabularies.
    These are used for import ONLY.
"""
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary

states_vocabulary = SimpleVocabulary(terms=[
    SimpleTerm(u"pending-draw", u"pending-draw", u"Pending Draw"),
    SimpleTerm(u"batched", u"batched", u"Batched"),
    SimpleTerm(u"postponed", u"postponed", u"Draw Postponed"),
    SimpleTerm(u"cancel-draw", u"cancel-draw", u"Draw Cancelled"),
    SimpleTerm(u"pending-aliquot", u"pending-aliquot", u"Pending Aliquot"),
    SimpleTerm(u"prepared-aliquot",
               u"prepared-aliquot",
               u"Prepared for Aliquot"),
    SimpleTerm(u"aliquoted", u"aliquoted", u"Aliquoted"),
    SimpleTerm(u"complete", u"complete", u"Complete"),
    SimpleTerm(u"rejected", u"rejected", u"Rejected"),
    ])

destination_vocabulary = SimpleVocabulary(terms=[
    SimpleTerm(u"Richman Lab", u"Richman Lab", u"Richman Lab"),
    SimpleTerm(u"UCSD Virology", u"UCSD Virology", u"UCSD Virology"),
    SimpleTerm(u"VA Immunogenetics",
               u"VA Immunogenetics",
               u"VA Immunogenetics"),
    SimpleTerm(u"Red Cross", u"Red Cross", u"Red Cross"),
    SimpleTerm(u"LabCorp/Serum Bank",
               u"LabCorp/Serum Bank",
               u"LabCorp/Serum Bank"),
    SimpleTerm(u"Blood Centers/Plasma Bank",
               u"Blood Centers/Plasma Bank",
               u"Blood Centers/Plasma Bank"),
    SimpleTerm(u"UCSD Micro", u"UCSD Micro", u"UCSD Micro"),
    SimpleTerm(u"Monogram", u"Monogram", u"Monogram"),
    SimpleTerm(u"ARUP", u"ARUP", u"ARUP"),
    SimpleTerm(u"UCSD", u"UCSD", u"UCSD"),
    SimpleTerm(u"Nurse", u"Nurse", u"Nurse"),
    SimpleTerm(u"HNRC", u"HNRC", u"HNRC"),
    ])

instructions_vocabulary = SimpleVocabulary(terms=[
    SimpleTerm(u"AEH Specimen Log", u"AEH Specimen Log", u"AEH Specimen Log"),
    SimpleTerm(u"Richman Lab", u"Richman Lab", u"Richman Lab"),
    SimpleTerm(u"AEH Specimen Bank",
               u"AEH Specimen Bank",
               u"AEH Specimen Bank"),
    SimpleTerm(u"Procedure Manual - Store at -70 C",
               u"Procedure Manual - Store at -70 C",
               u"Procedure Manual - Store at -70 C"),
    ])

tube_type_vocabulary = SimpleVocabulary(terms=[
    SimpleTerm(u"acdyellowtop", u"acdyellowtop", u"10 ml. ACD Yellow Tops"),
    SimpleTerm(u"10mlsst", u"10mlsst", u"10 ml. SST"),
    SimpleTerm(u"dacronswab", u"dacronswab", u"Dacron Swab/VTM"),
    SimpleTerm(u"gskit", u"gskit", u"Genital Secretion Kit"),
    SimpleTerm(u"csf", u"csf", u"16 ml. CSF"),
    SimpleTerm(u"rs-gut", u"rs-gut", u"1 ml. RS-GUT"),
    SimpleTerm(u"ti-gut", u"ti-gut", u"1 ml. TI-GUT"),
    ])

type_vocabulary = SimpleVocabulary(terms=[
    SimpleTerm(u"acd", u"acd", u"ACD"),
    SimpleTerm(u"genital-secretion",
               u"genital-secretion",
               u"Genital Secretion"),
    SimpleTerm(u"csf", u"csf", u"CSF"),
    SimpleTerm(u"gutbiopsy", u"gutbiopsy", u"Gut Biopsy"),
    SimpleTerm(u"urine", u"urine", u"Urine"),
    SimpleTerm(u"serum", u"serum", u"Serum"),
    SimpleTerm(u"swab", u"swab", u"Swab"),
    SimpleTerm(u"rs-gut", u"rs-gut", u"RS-GUT"),
    SimpleTerm(u"ti-gut", u"ti-gut", u"TI-GUT"),
    ])

AliquotStatusVocabulary = SimpleVocabulary(terms=[
    SimpleTerm(u"pending", u"pending", u"Pending Check In"),
    SimpleTerm(u"prepared", u"prepared", u"Prepared for Check In"),
    SimpleTerm(u"checked-in", u"checked-in", u"Checked In"),
    SimpleTerm(u"checked-out", u"checked-out", u"Checked Out"),
    SimpleTerm(u"hold", u"hold", u"On Hold"),
    SimpleTerm(u"unused", u"unused", u"Aliquot Not used"),

    ])

AliquotLocationVocabulary = SimpleVocabulary(terms=[
    SimpleTerm(u"richman lab", u"richman lab", u"Richman Lab"),
    SimpleTerm(u"avrc", u"avrc", u"AVRC"),
    ])

AliquotSentAnalysisVocabulary = SimpleVocabulary(terms=[
    SimpleTerm(u"yes", u"yes", u"Yes"),
    SimpleTerm(u"no", u"no", u"No"),
    SimpleTerm(u"missing", u"missing", u"Missing"),
    SimpleTerm(u"re-checked-in", u"re-checked-in", u"Re-checked-in"),
    SimpleTerm(u"hold removed", u"hold removed", u"On Hold Status Removed"),
    ])

AliquotTypeVocabulary = SimpleVocabulary(terms=[
    SimpleTerm(u"pbmc", u"pbmc", u"PBMC"),
    SimpleTerm(u"plasma", u"plasma", u"Plasma"),
    SimpleTerm(u"csf", u"csf", u"CSF"),
    SimpleTerm(u"csfpellet", u"csfpellet", u"CSF Pellet"),
    SimpleTerm(u"gscells", u"gscells", u"Genital Secretions Cells"),
    SimpleTerm(u"gsplasma", u"gsplasma", u"Genital Secretions Plasma"),
    SimpleTerm(u"gutbiopsy", u"gutbiopsy", u"Gut Biopsy"),
    SimpleTerm(u"urine", u"urine", u"Urine"),
    SimpleTerm(u"serum", u"serum", u"Serum"),
    SimpleTerm(u"swab", u"swab", u"Swab"),
    SimpleTerm(u"rs-gut", u"rs-gut", u"RS-GUT"),
    SimpleTerm(u"ti-gut", u"ti-gut", u"TI-GUT"),
    ])

AliquotSpecialInstructionVocabulary= SimpleVocabulary(terms=[
    SimpleTerm(u"na", u"na", u"None/NA"),
    SimpleTerm(u"hla", u"hla", u"HLA typing"),
    ])

datastore_import = {
    "specimen_state": states_vocabulary,
    "specimen_destination": destination_vocabulary,
    "specimen_instructions": instructions_vocabulary,
    "specimen_tube_type": tube_type_vocabulary,
    "specimen_type": type_vocabulary,
    "aliquot_state": AliquotStatusVocabulary,
    "aliquot_storage_site": AliquotLocationVocabulary,
    "aliquot_type": AliquotTypeVocabulary,
    "aliquot_special_instruction": AliquotSpecialInstructionVocabulary,
    "aliquot_sent_site": AliquotSentAnalysisVocabulary,
    }
