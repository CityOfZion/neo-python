from .StateBase import StateBase
from neocore.Fixed8 import Fixed8
from neocore.IO.BinaryReader import BinaryReader
from neo.IO.MemoryStream import StreamManager
from neo.Core.AssetType import AssetType
from neocore.UInt160 import UInt160
from neocore.Cryptography.Crypto import Crypto
from neocore.Cryptography.ECCurve import EllipticCurve, ECDSA


class AssetState(StateBase):
    AssetId = None
    AssetType = None
    Name = None
    Amount = Fixed8(0)
    Available = Fixed8(0)
    Precision = 0
    FeeMode = 0
    Fee = Fixed8(0)
    FeeAddress = None
    Owner = None
    Admin = None
    Issuer = None
    Expiration = None
    IsFrozen = False

    def __init__(self, asset_id=None, asset_type=None, name=None, amount=Fixed8(0), available=Fixed8(0),
                 precision=0, fee_mode=0, fee=Fixed8(0), fee_addr=UInt160(data=bytearray(20)), owner=None,
                 admin=None, issuer=None, expiration=None, is_frozen=False):
        """
        Create an instance.

        Args:
            asset_id (UInt256):
            asset_type (neo.Core.AssetType):
            name (str): the asset name.
            amount (Fixed8):
            available (Fixed8):
            precision (int): number of decimals the asset has.
            fee_mode (Fixed8):
            fee (int):
            fee_addr (UInt160): where the fee will be send to.
            owner (EllipticCurve.ECPoint):
            admin (UInt160): the administrator of the asset.
            issuer (UInt160): the issuer of the asset.
            expiration (UInt32): the block number on which the asset expires.
            is_frozen (bool):
        """
        self.AssetId = asset_id
        self.AssetType = asset_type
        self.Name = name

        self.Amount = amount
        self.Available = available
        self.Precision = precision
        self.FeeMode = fee_mode
        self.Fee = fee
        self.FeeAddress = fee_addr

        if owner is not None and type(owner) is not EllipticCurve.ECPoint:
            raise Exception("Owner must be ECPoint Instance")

        self.Owner = owner
        self.Admin = admin
        self.Issuer = issuer
        self.Expiration = expiration
        self.IsFrozen = is_frozen

    #    def Size(self):
    #        return super(AssetState, self).Size()

    @staticmethod
    def DeserializeFromDB(buffer):
        """
        Deserialize full object.

        Args:
            buffer (bytes, bytearray, BytesIO): (Optional) data to create the stream from.

        Returns:
            AssetState:
        """
        m = StreamManager.GetStream(buffer)
        reader = BinaryReader(m)
        account = AssetState()
        account.Deserialize(reader)

        StreamManager.ReleaseStream(m)

        return account

    def Deserialize(self, reader):
        """
        Deserialize full object.

        Args:
            reader (neocore.IO.BinaryReader):
        """
        super(AssetState, self).Deserialize(reader)
        self.AssetId = reader.ReadUInt256()
        self.AssetType = reader.ReadByte()
        self.Name = reader.ReadVarString()

        position = reader.stream.tell()

        try:
            self.Amount = reader.ReadFixed8()
        except Exception as e:
            reader.stream.seek(position)
            self.Amount = reader.ReadFixed8()

        self.Available = reader.ReadFixed8()
        self.Precision = reader.ReadByte()

        # fee mode
        reader.ReadByte()

        self.Fee = reader.ReadFixed8()
        self.FeeAddress = reader.ReadUInt160()
        self.Owner = ECDSA.Deserialize_Secp256r1(reader)
        self.Admin = reader.ReadUInt160()
        self.Issuer = reader.ReadUInt160()
        self.Expiration = reader.ReadUInt32()
        self.IsFrozen = reader.ReadBool()

    def Serialize(self, writer):
        """
        Serialize full object.

        Args:
            writer (neo.IO.BinaryWriter):
        """
        super(AssetState, self).Serialize(writer)
        writer.WriteUInt256(self.AssetId)
        writer.WriteByte(self.AssetType)
        writer.WriteVarString(self.Name)

        if self.Amount.value > -1:
            writer.WriteFixed8(self.Amount, unsigned=True)
        else:
            writer.WriteFixed8(self.Amount)

        if type(self.Available) is not Fixed8:
            raise Exception("AVAILABLE IS NOT FIXED 8!")
        writer.WriteFixed8(self.Available, unsigned=True)
        writer.WriteByte(self.Precision)
        writer.WriteByte(b'\x00')
        writer.WriteFixed8(self.Fee)
        writer.WriteUInt160(self.FeeAddress)
        self.Owner.Serialize(writer)
        writer.WriteUInt160(self.Admin)
        writer.WriteUInt160(self.Issuer)
        writer.WriteUInt32(self.Expiration)
        writer.WriteBool(self.IsFrozen)

    def GetName(self):
        """
        Get the asset name based on its type.

        Returns:
            str: 'NEO' or 'NEOGas'
        """
        if self.AssetType == AssetType.GoverningToken:
            return "NEO"
        elif self.AssetType == AssetType.UtilityToken:
            return "NEOGas"

        if type(self.Name) is bytes:
            return self.Name.decode('utf-8')
        return self.Name

    def ToJson(self):
        """
        Convert object members to a dictionary that can be parsed as JSON.

        Returns:
             dict:
        """
        return {
            'assetId': self.AssetId.ToString(),
            'assetType': self.AssetType,
            'name': self.GetName(),
            'amount': self.Amount.value,
            'available': self.Available.value,
            'precision': self.Precision,
            'fee': self.Fee.value,
            'address': self.FeeAddress.ToString(),
            'owner': self.Owner.ToString(),
            'admin': Crypto.ToAddress(self.Admin),
            'issuer': Crypto.ToAddress(self.Issuer),
            'expiration': self.Expiration,
            'is_frozen': self.IsFrozen
        }
