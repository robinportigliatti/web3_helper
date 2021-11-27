pip install web3
pip install py-solc-x
touch install_solc.py
echo 'from solcx import install_solc' >> install_solc.py
echo 'install_solc(version='latest')' >> install_solc.py
python install_solc.py
mkdir /app
git clone git@github.com:OpenZeppelin/openzeppelin-contracts.git /app/
