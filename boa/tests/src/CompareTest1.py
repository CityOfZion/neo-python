from neo.SmartContract.Framework.FunctionCode import FunctionCode

expected = '54c56b6c766b00527ac46c766b51527ac461006c766b52527ac46c766b00c36c766b51c3a06c766b53527ac46c766b53c364100061516c766b52527ac461620d0061526c766b52527ac461616c7566'




class SCTest(FunctionCode):


    @staticmethod
    def Main(a, b):

        j = 0

        if a > b:

            j = 1

        else:

            j = 2




#1>  Converting op code IL_0000 Nop
#1>  Converting op code IL_0001 Ldc_I4_0
#1>  Converting op code IL_0002 Stloc_0
#1>  Converting op code IL_0003 Ldarg_0
#1>  Converting op code IL_0004 Ldarg_1
#1>  Converting op code IL_0005 Cgt
#1>  Converting op code IL_0007 Stloc_1
#1>  Converting op code IL_0008 Ldloc_1
#1>  Converting op code IL_0009 Brfalse_S
#1>  Converting op code IL_000B Nop
#1>  Converting op code IL_000C Ldc_I4_1
#1>  Converting op code IL_000D Stloc_0
#1>  Converting op code IL_000E Nop
#1>  Converting op code IL_000F Br_S
#1>  Converting op code IL_0011 Nop
#1>  Converting op code IL_0012 Ldc_I4_2
#1>  Converting op code IL_0013 Stloc_0
#1>  Converting op code IL_0014 Nop
#1>  Converting op code IL_0015 Ret


