from ..tl.types import AccountAddress, Internal_TransactionId
from ..tl.functions import Raw_GetAccountState, GetAccountState, Raw_GetTransactions
from ..utils import KNOWN_CONTRACT_TYPES
from ..errors import InvalidUsage

class Contract:
    def __repr__(self): return f"Contract<{self.account_address.account_address}>"

    def __init__(self, address, key=None, local_password=None, client=None):
        if isinstance(address, AccountAddress):
            self.account_address = self.account_address
        elif isinstance(address, str):
            self.account_address = AccountAddress(address)
        else:
            raise InvalidUsage('Specify the account address')

        self.key = key
        self.local_password = local_password
        self.client = client

    async def get_state(self, raw=False):
        return await self.client.tonlib_wrapper.execute(
            Raw_GetAccountState(self.account_address) if raw is True else GetAccountState(self.account_address)
        )

    async def find_type(self):
        state = await self.get_state(raw=True)
        return KNOWN_CONTRACT_TYPES.get(state.code, None)

    async def get_balance(self):
        return int((await self.get_state()).balance) # in nanocoins

    async def get_transactions(self, from_transaction_lt=None, from_transaction_hash=None, to_transaction_lt=0, limit=10):
        if from_transaction_lt == None or from_transaction_hash == None:
            state = await self.get_state()
            from_transaction_lt, from_transaction_hash = state.last_transaction_id.lt, state.last_transaction_id.hash

        reach_lt = False
        all_transactions = []
        current_tx = Internal_TransactionId(
            from_transaction_lt, from_transaction_hash
        )
        while not reach_lt and len(all_transactions) < limit:
            raw_transactions = await self.client.tonlib_wrapper.execute(
                Raw_GetTransactions(
                    self.account_address,
                    current_tx
                )
            )
            transactions, current_tx = raw_transactions.transactions, raw_transactions.__dict__.get("previous_transaction_id", None)
            for tx in transactions:
                tlt = int(tx.transaction_id.lt)
                if tlt <= to_transaction_lt:
                    reach_lt = True
                    break
                all_transactions.append(tx)

            if current_tx is None:
                break

            if int(current_tx.lt) == 0:
                break

        return all_transactions
