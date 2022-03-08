# Create secrets for market-maker-keeper staging
kubectl ~/.kube/kube.config create secret generic mmk-staging-secrets \
  --from-literal=rpc_url="https://polygon-mumbai.infura.io/v3/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" \
  --from-literal=pk="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" \
  --from-literal=clob_api_key="xxxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxxxx" \
  --from-literal=clob_api_secret="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" \
  --from-literal=clob_api_passphrase="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
