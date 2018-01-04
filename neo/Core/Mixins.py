# -*- coding: UTF-8 -*-

from neocore.IO.Mixins import SerializableMixin


class ClonableMixin(object):
    def clone(self):
        pass


class CodeMixin(object):
    scripts = []
    parameter_list = []
    return_type = None
    script_hash = None


class VerifiableMixin(SerializableMixin):

    scripts = []

    # <summary>
    # 反序列化未签名的数据
    # </summary>
    # <param name="reader">数据来源</param>
    def DeserializeUnsigned(self, reader):
        pass

    # <summary>
    # 获得需要校验的脚本Hash值
    # </summary>
    # <returns>返回需要校验的脚本Hash值</returns>
    def GetScriptHashesForVerifying(self):
        pass

    # <summary>
    # 序列化未签名的数据
    # </summary>
    # <param name="writer">存放序列化后的结果</param>
    def SerializeUnsigned(self, writer):
        pass


class EquatableMixin():

    def __eq__(self, other):
        return self.__dict__ == other.__dict__
