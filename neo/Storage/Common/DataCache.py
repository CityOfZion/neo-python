from enum import Enum, auto


class TrackState(Enum):
    NONE = auto()
    ADDED = auto()
    CHANGED = auto()
    DELETED = auto()


class Trackable:
    def __init__(self, key, value, state: TrackState):
        self.Key = key
        self.Item = value
        self.State = state


class DataCache:
    def __init__(self):
        self.dictionary = {}

    def __getitem__(self, key):

        trackable = self.dictionary.get(key, None)  # type: Trackable
        if trackable is not None:
            if trackable.State == TrackState.DELETED:
                raise KeyError
        else:
            trackable = Trackable(key, self.GetInternal(key), TrackState.NONE)
            self.dictionary.update({key: trackable})
        return trackable.Item

    def Add(self, key, value):
        trackable = self.dictionary.get(key, None)  # type: Trackable
        if trackable is not None and trackable.State != TrackState.DELETED:
            raise ValueError("Value already exists")

        if trackable is None:
            trackable = Trackable(key, value, TrackState.ADDED)
        else:
            trackable = Trackable(key, value, TrackState.CHANGED)

        self.dictionary.update({key: trackable})

    def AddInternal(self, key, value):
        raise NotImplementedError()

    def Commit(self):
        for trackable in self.dictionary.values():  # type: Trackable
            if trackable.State == TrackState.ADDED:
                self.AddInternal(trackable.Key, trackable.Item)
            elif trackable.State == TrackState.CHANGED:
                self.UpdateInternal(trackable.Key, trackable.Item)
            elif trackable.State == TrackState.DELETED:
                self.DeleteInternal(trackable.Key)

    def UpdateInternal(self, key, value):
        raise NotImplementedError()

    def CreateSnapshot(self):
        from neo.Storage.Common.CloneCache import CloneCache
        return CloneCache(self)

    def Delete(self, key):
        trackable = self.dictionary.get(key, None)  # type: Trackable
        if trackable is not None:
            if trackable.State == TrackState.ADDED:
                self.dictionary.pop(key)
            else:
                trackable.State = TrackState.DELETED
        else:
            item = self.TryGetInternal(key)
            if item is None:
                return

            self.dictionary.update({key: Trackable(key, item, TrackState.DELETED)})

    def DeleteInternal(self, key):
        raise NotImplementedError()

    def DeleteWhere(self, predicate_func):
        for trackable in self.dictionary.values():
            if trackable.State != TrackState.DELETED and predicate_func(trackable.Key, trackable.Item):
                trackable.State = TrackState.DELETED

    def Find(self, key_prefix=None):
        if key_prefix is None:
            key_prefix = b''

        for k, v in self.FindInternal(key_prefix):
            if k not in self.dictionary:
                yield k, v

        for k, v in self.dictionary.items():
            if v.State != TrackState.DELETED and (key_prefix is None or key_prefix in k):
                yield k, v.Item

    def FindInternal(self, key_prefix) -> dict:
        # should be equal to DBInterface.Find
        raise NotImplementedError()

    def GetAndChange(self, key, factory=None):
        # neo-cli used this very confusing naming. It is actually more close to GetOrCreate
        trackable = self.dictionary.get(key, None)
        if trackable is not None:
            if trackable.State == TrackState.DELETED:
                if factory is None:
                    raise KeyError
                trackable.Item = factory()
                trackable.State = TrackState.CHANGED
            elif trackable.State == TrackState.NONE:
                trackable.State = TrackState.CHANGED
        else:
            trackable = Trackable(key, self.TryGetInternal(key), TrackState.NONE)
            if trackable.Item is None:
                if factory is None:
                    raise KeyError
                trackable.Item = factory()
                trackable.State = TrackState.ADDED
            else:
                trackable.State = TrackState.CHANGED
            self.dictionary.update({key: trackable})

        return trackable.Item

    def GetOrAdd(self, key, factory):
        trackable = self.dictionary.get(key, None)
        if trackable is not None:
            if trackable.State == TrackState.DELETED:
                trackable.Item = factory()
                trackable.State = TrackState.CHANGED
        else:
            trackable = Trackable(key, self.TryGetInternal(key), TrackState.NONE)
            if trackable.Item is None:
                trackable.Item = factory()
                trackable.State = TrackState.ADDED
            self.dictionary.update({key: trackable})

        return trackable.Item

    def GetInternal(self, key):
        raise NotImplementedError()

    def TryGet(self, key):
        """
        Get Item, by key

        :param key:
        :return: Item if found, None otherwise
        """
        trackable = self.dictionary.get(key, None)
        if trackable is not None:
            if trackable.State == TrackState.DELETED:
                return None
            return trackable.Item

        item = self.TryGetInternal(key)
        if item is None:
            return None

        self.dictionary.update({key: Trackable(key, item, TrackState.NONE)})
        return item

    def TryGetInternal(self, key):
        raise NotImplementedError()

    def GetChangeSet(self):
        for trackable in self.dictionary.values():
            if trackable.State != TrackState.NONE:
                yield trackable
