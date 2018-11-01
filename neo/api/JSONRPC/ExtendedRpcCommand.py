from abc import ABC, abstractmethod


class ExtendedRpcCommand(ABC):
    @classmethod
    @abstractmethod
    def commands(cls):
        return []

    @classmethod
    @abstractmethod
    def execute(cls, json_rpc_api, method):
        return "result"
