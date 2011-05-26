
from avrc.data.store.interfaces import IManager



class ISpecimenManager(IManager):
    """ Marker interface for managing specimen """

    def list(start=None, num=None):
        """ """
