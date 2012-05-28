#overhaul

# Assumptions

from sqlalchemy.ext.sqlsoup import SqlSoup
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import create_engine
from occams.datastore import model as dsmodel
from occams.lab import model
from avrc.aeh import model as cmodel
from sqlalchemy import func
from sqlalchemy import String
from sqlalchemy import Date
from sqlalchemy.sql.expression import case
from sqlalchemy.sql.expression import cast
from sqlalchemy.sql.expression import null
from sqlalchemy.sql.expression import literal_column
from sqlalchemy.orm import aliased
from sqlalchemy import distinct 
from sqlalchemy import func

global Session
Session = scoped_session(
    sessionmaker(
        class_=dsmodel.DataStoreSession,
        user=(lambda : "bitcore@ucsd.edu") # can be called by a library
        ))

global old_model

# global entity_state # Filled during Session creation and so on

def main():
    """Handle argv, specialize globals, launch job."""
    import sys
    usage = """overhaul.py OLDCONNECT NEWCONNECT"""
    configureGlobalSession(sys.argv[1], sys.argv[2])
    addUser("bitcore@ucsd.edu")
    updateUsers()
    moveInSpecialInstruction()
    moveInLocation()
    moveInSpecimenState()
    moveInAliquotState()
    moveInSpecimenType()
    moveInAliquotType()
    moveInSpecimen()
    moveInAliquot()
    resetId(model.SpecialInstruction, sys.argv[2])
    resetId(model.Location, sys.argv[2])
    resetId(model.SpecimenState, sys.argv[2])
    resetId(model.AliquotState, sys.argv[2])
    resetId(model.SpecimenType, sys.argv[2])
    resetId(model.AliquotType, sys.argv[2])
    resetId(model.Specimen, sys.argv[2])
    resetId(model.Aliquot, sys.argv[2])


    Session.commit()
    # moveIn

    print "Yay!"

def resetId(modelType, connectstring):
    """
    """
    global Session
    new_engine = create_engine(connectstring)
    maximum = Session.query(modelType.id).order_by(modelType.id.desc()).first()
    if maximum:
        Session.execute("SELECT setval('%s_id_seq', %s);" % (modelType.__tablename__, maximum.id), bind=new_engine)


def updateUsers():
    spec=old_model.entity("specimen")
    aliq = old_model.entity("aliquot")
    ali_h= old_model.entity("aliquot_history")
    userset = set()
    for entry in (spec.c.create_name, spec.c.modify_name, aliq.c.create_name, aliq.c.modify_name, ali_h.c.create_name):
        query = Session.query(distinct(entry))
        for (user,) in iter(query):
            if user is not None:
                userset.add(user)
    for user in userset:
        addUser(user)
    Session.flush()

def moveInVocabulary(name, modelKlass):
    global Session
    global old_model

    vocab = aliased(old_model.entity('specimen_aliquot_term'))

    query = (
        Session.query(vocab)
        .filter(vocab.vocabulary_name == name)
        .filter(vocab.is_active==True)
        )

    for term in iter(query):
        if Session.query(modelKlass).filter(modelKlass.name==term.value).count()<=0:
            vocab_term = modelKlass(
                id = term.id,
                name= term.value,
                title = term.title,
                create_date  = term.create_date,
                modify_date = term.modify_date
                )
            print vocab_term.title
            Session.add(vocab_term)
            Session.flush()


def moveInSpecialInstruction():
    moveInVocabulary( 'aliquot_special_instruction', model.SpecialInstruction)

def moveInLocation():
    moveInVocabulary( 'specimen_destination', model.Location)
    moveInVocabulary( 'aliquot_storage_site', model.Location)

def moveInSpecimenState():
    moveInVocabulary( 'specimen_state', model.SpecimenState)

def moveInAliquotState():
    moveInVocabulary('aliquot_state', model.AliquotState)

def moveInSpecimenType():
    global Session
    global old_model
    spec=aliased(old_model.entity("specimen"))
    vocab = aliased(old_model.entity('specimen_aliquot_term'))
    tube_type  = aliased(old_model.entity('specimen_aliquot_term'))

    subquery = (
        Session.query(spec.type_id.label('type_id'), tube_type.title.label('tube_type'), spec.destination_id.label('destination_id'))
        .join(tube_type, (tube_type.id == spec.tupe_type_id))
        .group_by(spec.type_id, tube_type.title, spec.destination_id)
        ).subquery("specstats")

    query= (
        Session.query(vocab,  subquery.c.tube_type,   subquery.c.destination_id)
            .outerjoin(subquery, (subquery.c.type_id == vocab.id))
            .filter(vocab.vocabulary_name == 'specimen_type')
        )
    for term, tube_type, destination_id in iter(query):
        spec_type= model.SpecimenType(
            id  = term.id,
            name  = term.value,
            title = term.title,
            tube_type = tube_type,
            location_id = destination_id,
            create_date  = term.create_date,
            modify_date = term.modify_date
            )
        Session.add(spec_type)
    Session.flush()

def moveInAliquotType():
    global Session
    global old_model
    spec=aliased(old_model.entity("specimen"))
    aliq = aliased(old_model.entity("aliquot"))
    vocab = aliased(old_model.entity('specimen_aliquot_term'))

    subquery = (
        Session.query(func.max(aliq.specimen_id).label('ex_specimen'), aliq.type_id.label('type_id'))
        .group_by(aliq.type_id)
        ).subquery("aliq_types")

    query= (
        Session.query(vocab, spec.type_id.label('spec_id'))
            .select_from(vocab)
            .outerjoin(subquery, (subquery.c.type_id == vocab.id))
            .join(spec, (subquery.c.ex_specimen == spec.id))
            .filter(vocab.vocabulary_name == 'aliquot_type')
        )

    for term, spec_id in iter(query):
        aliquot_type= model.AliquotType(
            id  = term.id,
            name  = term.value,
            title = term.title,
            specimen_type_id = spec_id,
            location_id = 56,
            create_date  = term.create_date,
            modify_date = term.modify_date
            )
        Session.add(aliquot_type)
        Session.flush()


def moveInSpecimen():
    global Session
    global old_model
    spec=aliased(old_model.entity("specimen"))
    # aliq = aliased(old_model.entity("aliquot"))
    # ali_h= aliased(old_model.entity("aliquot_history"))
    # vocab = aliased(old_model.entity('specimen_aliquot_term'))
    # vocab_alias  = aliased(old_model.entity('specimen_aliquot_term'))
    # state = aliased(old_model.entity('specimen_aliquot_term'))
    # location = aliased(old_model.entity('specimen_aliquot_term'))

    query = (
        Session.query(spec).filter(spec.is_active==True).order_by(spec.id)
        )
    for entry in iter(query):
        if Session.query(cmodel.Patient).filter(cmodel.Patient.id == entry.subject_id).count()>0:
        # create_user = entry.create_name is not None and entry.create_name or 'bitcore@ucsd.edu'
        # create_user = Session.query(dsmodel.User).filter(key=create_user).one()
        # modify_user = entry.modify_name is not None and entry.modify_name or \
        #                       entry.create_name is not None and entry.create_name or 'bitcore@ucsd.edu'
        # modify_user = Session.query(dsmodel.User).filter(key=modify_user).one()


        # location_id = Session.query(model.Location.id).filter(model.Location.value==location).one()
            specimen = model.Specimen(
                id = entry.id,
                specimen_type_id = entry.type_id,
                patient_id = entry.subject_id,
                cycle_id = entry.protocol_id,
                state_id = entry.state_id,
                collect_date = entry.collect_date,
                collect_time = entry.collect_time,
                location_id = entry.destination_id,
                tubes = entry.tubes,
                notes = entry.notes,
                study_cycle_label = entry.study_cycle_label,
                # create_user_id = create_user.id,
                create_date = entry.create_date,
                # modify_user_id = modify_user.id,
                modify_date = entry.modify_date
                )
            Session.add(specimen)
            print specimen.id
            Session.flush()

def moveInAliquot():
    global Session
    global old_model
    # spec=old_model.entity("specimen")
    aliq = old_model.entity("aliquot")
    # ali_h= old_model.entity("aliquot_history")
    # vocab = old_model.entity('specimen_aliquot_term')
    # vocab_alias  = old_model.entity('specimen_aliquot_term')
    # state = old_model.entity('specimen_aliquot_term')
    # location = old_model.entity('specimen_aliquot_term')

    query = (
        Session.query(aliq)
        .filter(aliq.is_active==True)
        .order_by(aliq.id)
        )

    for entry in iter(query):
        aliquot = model.Aliquot(
            id = entry.id,
            specimen_id = entry.specimen_id,
            aliquot_type_id = entry.type_id,
            state_id = entry.state_id,
            volume = entry.volume,
            cell_amount = entry.cell_amount,
            store_date = entry.store_date,
            freezer = entry.freezer,
            rack =entry.rack,
            box = entry.box,
            location_id = entry.sent_site_id is not None and entry.sent_site_id or entry.storage_site_id,
            thawed_num = entry.thawed_num,
            inventory_date = entry.inventory_date,
            sent_date = entry.sent_date,
            sent_name = entry.sent_name,
            sent_notes = entry.sent_notes,
            notes =entry.notes,
            special_instruction_id = entry.special_instruction_id,
            )
        Session.add(aliquot)
        print aliquot.id
        Session.flush()


def retire(table_name, new_model):
    """
    Docstring me
    """
    global Session
    global old_model
    old_table = old_model.entity(table_name)
    for entry in iter(Session.query(old_table).filter(old_table.c.is_active == False)):
        newEntry = Session.query(new_model).filter(new_model.id == entry.id).one()
        Session.delete(newEntry)
        Session.flush()


def configureGlobalSession(old_connect, new_connect):
    """Set up Session for data manipulation and create new tables as side effect."""
    global old_model
    new_engine = create_engine(new_connect)
    dsmodel.Model.metadata.create_all(bind=new_engine, checkfirst=True)
    tables = []
    tables_model = dsmodel.Model.metadata.sorted_tables
    tables += dict.fromkeys(tables_model, new_engine).items()
    Session.configure(binds=dict(tables))
    old_model = SqlSoup(old_connect,session=Session)

def addUser(email):
    user = Session.query(dsmodel.User).filter(dsmodel.User.key == email).first()
    if not user:
        Session.add(dsmodel.User(key=email))
        Session.flush()

if __name__ == '__main__':
    main()