
from occams.datastore.batch import SqlBatch

class SqlDictBatch(SqlBatch):
    """
    Batch implementation for sqlalchemy.
    See IBatch
    """
    @property
    def firstElement(self):
        """
        See interfaces.IBatch
        """
        result = self.query.offset(self.start).limit(1).one()
        result_id = result.id
        result = result.__dict__
        return (result_id, result)

    @property
    def lastElement(self):
        """
        See interfaces.IBatch
        """
        result = self.query.offset(self.end).limit(1).one()
        result_id = result.id
        result = result.__dict__
        return (result_id, result)

    def __getitem__(self, key):
        """
        See zope.interface.common.sequence.IMinimalSequence
        """
        if key >= self._trueSize:
            raise IndexError('batch index out of range')
        result = self.query.offset(self.start + key).limit(1).one()
        result_id = result.id
        result = result.__dict__
        return (result_id, result)

    def __iter__(self):
        """
        See zope.interface.common.sequence.IMinimalSequence
        """
        if self._length > 0:
            for result in self.query.slice(self.start, self.end + 1):
                result_id = result.id
                result = result.__dict__
                yield (result_id, result)

    def __getslice__(self, i, j):
        if j > self.end:
            j = self._trueSize
        query = self.query.slice(i, j)
        for result in query:
            result_id = result.id
            result = result.__dict__
            yield (result_id, result)

