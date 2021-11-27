from itertools import permutations
from os import listdir
from os.path import isfile, join
from solcx import compile_source
from web3 import Account, Web3, HTTPProvider
from web3.exceptions import ContractLogicError
from web3.middleware import geth_poa_middleware
import itertools
import json
import os
import requests
import subprocess
import sys
import time

class Contract():
    def __init__(self, address, abi=None, source_code=None):
        self.address = address
        self.abi = abi
        self.bytecode = None
        if source_code is not None:
            self.source_code = source_code
            self.init_abi_and_bin_from_source_code()

    def init_abi_and_bin_from_source_code(self):
        compiled_sol = compile_source(
            self.source_code,
            output_values=["abi", "bin"],
        )
        contract_id, contract_interface = compiled_sol.popitem()
        self.bytecode, self.abi = contract_interface['bin'], json.dumps(contract_interface['abi'])

class Web3Helper():
    def __init__(self, contract_information , private_key, provider_url, provider=None):
        self.contract_address = contract_information.address
        self.abi = contract_information.abi
        self.bytecode = contract_information.bytecode
        self.private_key = private_key
        self.provider_url = provider_url
        self.w3 = Web3(HTTPProvider(provider_url))
        if provider == "GANACHE":
            self.account_address = self.w3.eth.accounts[0]
            print(self.account_address)
        else:
            self.account = self.get_account()
            self.account_address = self.account.address
        self.w3.eth.defaultAccount = self.account_address
        self.contract = self.w3.eth.contract(
            address=self.contract_address,
            abi=json.loads(contract_information.abi),
        )

    def get_account():
        return Account.from_key(private_key)

    def calculate_nonce(self):
        return Web3.toHex(self.w3.eth.get_transaction_count(self.account_address))

    def get_gas_price_from_gas_station():
        req = requests.get('https://ethgasstation.info/json/ethgasAPI.json')
        t = json.loads(req.content)
        metadata = {}
        metadata['safeLow'] = t['safeLow']
        metadata['average'] = t['average']
        metadata['fast'] = t['fast']
        metadata['fastest'] = t['fastest']
        return metadata

    def get_estimate_gas(self, fn_name, args):
        return getattr(self.contract.functions, fn_name)(*args).estimateGas({'from': self.account_address})

    def handle_transaction(self, fn_name, args):
        from_addr = self.account_address

        data = self.contract.encodeABI(fn_name, args=args)

        gas = self.get_estimate_gas(fn_name, args)

        prices = Web3Helper.get_gas_price_from_gas_station()
        gasprice = self.w3.toWei(prices['safeLow'], 'gwei')
        txn_fee = gas * gasprice

        tr = {'to': self.contract.address,
                'from': from_addr,
                'value': Web3.toHex(0),
                'gasPrice': Web3.toHex(gasprice),
                'nonce': self.calculate_nonce(),
                'data': data,
                'gas': gas,
                }

        signed = self.w3.eth.account.sign_transaction(tr, self.private_key)
        tx = self.w3.eth.sendRawTransaction(signed.rawTransaction)
        tx_receipt = self.w3.eth.waitForTransactionReceipt(tx)
        return tx_receipt

    def get_from_address(self):
        return Web3.toChecksumAddress(self.account_address)

    def get_balance(self):
        return self.contract.functions.balanceOf(self.account_address).call({'from': self.account_address})

    def deploy_smart_contracts(self):
        print("deploy_smart_contracts", "Begin")
        # # Instantiate and deploy contract
        contract_definition = self.w3.eth.contract(abi=self.abi, bytecode=self.bytecode)
        #tx_hash = contract_definition.constructor().transact()
        gas = contract_definition.constructor().estimateGas()

        prices = Web3Helper.get_gas_price_from_gas_station()
        gasprice = self.w3.toWei(prices['safeLow'], 'gwei')
        txn_fee = gas * gasprice
        data = contract_definition._encode_constructor_data()
        tr = {
                'from': self.account_address,
                'value': Web3.toHex(0),
                'gasPrice': Web3.toHex(gasprice),
                'nonce': self.calculate_nonce(),
                'data': data,
                'gas': gas,
                }
        signed = self.w3.eth.account.sign_transaction(tr, self.private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed.rawTransaction)
        ## # Wait for the transaction to be mined, and get the transaction receipt
        tx_receipt = self.w3.eth.waitForTransactionReceipt(tx_hash)
        self.contract_address = tx_receipt.contractAddress
        self.contract = self.w3.eth.contract(
            address=self.contract_address,
            abi=self.abi,
        )
        print("Smart contract created", self.contract_address)

        return self.contract_address
