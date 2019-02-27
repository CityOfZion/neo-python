from abc import abstractmethod, ABC


class SerializableMixin(ABC):

    @abstractmethod
    def serialize(self, writer) -> None:
        pass

    @abstractmethod
    def deserialize(self, reader) -> None:
        pass

    @abstractmethod
    def to_array(self) -> bytearray:
        pass
