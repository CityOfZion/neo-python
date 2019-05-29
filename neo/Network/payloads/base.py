from neo.Network.core.mixin.serializable import SerializableMixin


class BasePayload(SerializableMixin):

    def serialize(self, writer) -> None:
        pass

    def deserialize(self, reader) -> None:
        pass

    def to_array(self) -> bytearray:
        pass
