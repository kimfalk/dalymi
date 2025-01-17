import os.path
import pickle


class Resource:

    def __init__(self, name=None, loc=None, assertions=[]):
        self.name = name
        self.loc = loc
        self.assertions = assertions

    def _check(self, context):
        path = self.loc.format(**context)
        return self.check(path)

    def _delete(self, context):
        path = self.loc.format(**context)
        self.delete(path)

    def _load(self, context):
        path = self.loc.format(**context)
        data = self.load(path)
        self.assert_integrity(data)
        return data

    def _save(self, data, context):
        self.assert_integrity(data)
        path = self.loc.format(**context)
        self.save(path, data)

    def assert_integrity(self, data):
        for assertion in self.assertions:
            assertion(data)

    def check(self, path):
        msg = 'Could not *check* resource <{}> (and possibly others), '.format(self.name)
        msg += 'because the resource class has no implementation of the `check` method.'
        raise NotImplementedError(msg)

    def delete(self, path):
        msg = 'Could not *delete* resource <{}> (and possibly others), '.format(self.name)
        msg += 'because the resource class has no implementation of the `delete` method.'
        raise NotImplementedError(msg)

    def load(self, path):
        msg = 'Could not *load* resource <{}> (and possibly others), '.format(self.name)
        msg += 'because the resource class has no implementation of the `load` method.'
        raise NotImplementedError(msg)

    def save(self, path, data):
        msg = 'Could not *save* resource <{}> (and possibly others), '.format(self.name)
        msg += 'because the resource class has no implementation of the `save` method.'
        raise NotImplementedError(msg)


class LocalFileMixin:
    '''
    Provides default `check` and `delete` methods for local file resources.
    Inherit from this before other resource classes to avoid `NotImplementedError`.
    '''
    def makedirs(self, path):
        '''
        Convenience method to recursively create directories for a path if it does not exist.
        Could be called, for example, in the `save` method of a sub-class.
        '''
        dirs = os.path.dirname(path)
        if dirs:
            os.makedirs(dirs, exist_ok=True)

    def check(self, path):
        return os.path.isfile(path)

    def delete(self, path):
        return os.remove(path)


class PandasDF(Resource):

    def __init__(self, name=None, loc=None, columns=None, assertions=[]):
        assertions = [self.assert_columns] + assertions
        super().__init__(name=name, loc=loc, assertions=assertions)
        self.columns = columns

    def assert_columns(self, df):
        if self.columns is not None:
            assert set(df.columns) == set(self.columns), \
                'Columns of resource <{}> do not match expected. '.format(self.name) \
                + 'Present: {}. Expected: {}.'.format(set(df.columns,set(self.columns)))


class PandasCSV(LocalFileMixin, PandasDF):

    def __init__(self, name=None, loc=None, columns=None, assertions=[]):
        PandasDF.__init__(self, name=name, loc=loc, columns=columns, assertions=assertions)

    def load(self, path):
        import pandas as pd  # importing pandas here to avoid general dependency on it
        return pd.read_csv(path)

    def save(self, path, data):
        self.makedirs(path)
        return data.to_csv(path, index=False)


class Pickle(LocalFileMixin, Resource):

    def __init__(self, name=None, loc=None, assertions=[]):
        Resource.__init__(self, name=name, loc=loc, assertions=assertions)

    def load(self, path):
        with open(path, 'rb') as f:
            return pickle.load(f)

    def save(self, path, data):
        self.makedirs(path)
        with open(path, 'wb') as f:
            pickle.dump(data, f)
