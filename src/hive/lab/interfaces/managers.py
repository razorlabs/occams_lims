from avrc.data.store.interfaces import IManager


class IBaseConventionalManager(IManager):
    """
    """
    def get_vocabulary(name):
        """ Utility method for retrieving supported vocabulary terms for
            specimen and aliquot attributes.

            Arguments:
                name: (unicode) the name of the vocabulary to fetch
            Returns:
                SimpleVocabulary object
        """

    def vocab_map(source, **kw):
        """
        """

    def makefilter(**kw):
        """
        Generic specimen filter. Takes kw arguments, generally matching
        the ISpecimen interface
        """

    def count_records(**kw):
        """
        Generic specimen filter. Takes kw arguments, generally matching
        the ISpecimen interface
        """
        
    def filter_records(**kw):
        """
        Generic specimen filter. Takes kw arguments, generally matching
        the ISpecimen interface
        """
        
class IAliquotManager(IBaseConventionalManager):
    """  interface for managing specimen """


class ISpecimenManager(IBaseConventionalManager):
    """  interface for managing specimen """
