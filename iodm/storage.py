import json
import hashlib

from iodm import Q
from iodm.models import DataObject
from iodm.util import order_dictionary
from iodm.backends.ext import TranslatingBackend


class ReadOnlyStorage:

    def __init__(self, backend):
        self._backend = TranslatingBackend(DataObject, backend)

    def get(self, key):
        return self._backend.get(key)

    def bulk_read(self, keys):
        return self._backend.query(Q('ref', 'in', keys))


class Storage(ReadOnlyStorage):

    def create(self, data):
        if isinstance(data, dict):
            data = order_dictionary(data)

        hasher = hashlib.new('sha1')
        hasher.update(json.dumps(data).encode('utf-8'))

        # Optimistic check to see if this data object already exists
        try:
            # TODO Decide what happens when a key is not found
            data_obj = self._backend.get(hasher.hexdigest())
            if data_obj is not None:
                return data_obj
        except Exception:
            pass

        data_obj = DataObject(ref=hasher.hexdigest(), data=data)

        self._backend.set(data_obj.ref, data_obj)

        return data_obj
