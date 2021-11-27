from web3_helper import Web3Helper, Contract
from pathlib import Path

class CollectionContract(Web3Helper):
    def claim_nft(self, token_uri):
        self.handle_transaction("claimItem", [token_uri])

        balance = self.get_balance()
        print("balance", balance)

def generate():
    source_code = Path('./Web3Helper.sol').read_text()
    contract_information = Contract(
        address="", # will be updated after the contract has been deployed, don't forget to save it
        abi="", # only used after the contract has been deployed, abi will be updated after the deploy_smart_contracts call, don't forget to save it
        source_code=source_code, # only used for the deployment
    )
    MyHelper = CollectionContract(
        contract_information=contract_information,
        private_key="",
        provider_url="http://ganache:8545",
        provider= "GANACHE"
    )
    MyHelper.deploy_smart_contracts()
    print("contact_address:", MyHelper.contract_address)
    print("abi:", MyHelper.abi)
    print("bytecode:", MyHelper.bytecode)
    MyHelper.claim_nft(token_uri="http://example.com/api/nft/1/json")
    MyHelper.claim_nft(token_uri="http://example.com/api/nft/2/json")

generate()
