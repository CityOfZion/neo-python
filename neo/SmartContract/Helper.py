from neo.logging import log_manager

logger = log_manager.getLogger()


class Helper:
    @staticmethod
    def VerifyWitnesses(verifiable, snapshot):
        """
        Verify the scripts of the provided `verifiable` object.

        Args:
            verifiable (neo.IO.Mixins.VerifiableMixin):

        Returns:
            bool: True if verification is successful. False otherwise.
        """
        try:
            hashes = verifiable.GetScriptHashesForVerifying(snapshot)
        except Exception as e:
            logger.debug("couldn't get script hashes %s " % e)
            return False

        if len(hashes) != len(verifiable.Scripts):
            logger.debug(f"hash - verification script length mismatch ({len(hashes)}/{len(verifiable.Scripts)})")
            return False

        blockchain = GetBlockchain()

        for i in range(0, len(hashes)):
            verification = verifiable.Scripts[i].VerificationScript

            if len(verification) == 0:
                sb = ScriptBuilder()
                sb.EmitAppCall(hashes[i].Data)
                verification = sb.ms.getvalue()
                sb.ms.Cleanup()
            else:
                verification_hash = Crypto.ToScriptHash(verification, unhex=False)
                if hashes[i] != verification_hash:
                    logger.debug(f"hash {hashes[i]} does not match verification hash {verification_hash}")
                    return False

            service = GetStateMachine()
            script_table = CachedScriptTable(DBInterface(blockchain._db, DBPrefix.ST_Contract, ContractState))

            engine = ApplicationEngine(TriggerType.Verification, verifiable, script_table, service, Fixed8.Zero())
            engine.LoadScript(verification)
            invocation = verifiable.Scripts[i].InvocationScript
            engine.LoadScript(invocation)

            try:
                success = engine.Execute()
                service.ExecutionCompleted(engine, success)
            except Exception as e:
                service.ExecutionCompleted(engine, False, e)

            if engine.ResultStack.Count != 1 or not engine.ResultStack.Pop().GetBoolean():
                Helper.EmitServiceEvents(service)
                if engine.ResultStack.Count > 0:
                    logger.debug(
                        f"Result stack failure! Count: {engine.ResultStack.Count} bool value: {engine.ResultStack.Pop().GetBoolean()}")
                else:
                    logger.debug(f"Result stack failure! Count: {engine.ResultStack.Count}")
                return False

            Helper.EmitServiceEvents(service)

        return True
