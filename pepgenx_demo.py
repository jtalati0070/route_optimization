PEPGENX_PROJECT_ID = "1cdfabed-cc85-490c-98de-718ca1d9de1d"
PEPGENX_TEAM_ID = "8e23d57d-cd0a-4a38-9542-53607206f3a6"

# PepGenX API key
PEPGENX_API_KEY = "4d7811b7-ebfe-4036-b7e0-a63ce699a0e1"

PEPGENX_API_URL = "https://apim-na.qa.mypepsico.com/cgf/pepgenx/v2/llm/openai/generate-response"

PEPGENX_OKTA_CLIENT_ID = '0oa2hu2jylmU9cuvH0h8'
PEPGENX_OKTA_CLIENT_SECRET = 'vgwZia2ARBrYSNi0pwqTiQeGWu3jLRl-xRNxclA0gACDuY1DJbnyKI1J_P-GO8aw'

# --------------------

# Use config values from the global config dictionary loaded at module level
pepgenx_api_url = config['PEPGENX_API_URL']
pepgenx_api_key = config['PEPGENX_API_KEY']
pepgenx_project_id = config['PEPGENX_PROJECT_ID']
pepgenx_team_id = config['PEPGENX_TEAM_ID']
pepgenx_model = config['PEPGENX_MODEL']
pepgenx_max_tokens = config['PEPGENX_MAX_TOKENS']
okta_client_credentials = config['OKTA_CLIENT_CREDENTIALS']
okta_token_url = config['OKTA_TOKEN_URL']
try:
    from app.utils.auth import AsyncOktaTokenManager
except ModuleNotFoundError:
    from utils.auth import AsyncOktaTokenManager
# Create token manager instance
okta_token_manager = AsyncOktaTokenManager(okta_client_credentials, okta_token_url)
# Get Okta bearer token
bearer = await okta_token_manager.get_token()
# Build LLM request headers and payload
headers = {
    'Authorization': f'Bearer {bearer}',
    'project_id': pepgenx_project_id,
    'team_id': pepgenx_team_id,
    'transaction_id': '',
    'user_id': '',
    'x-pepgenx-apikey': pepgenx_api_key,
    'Content-Type': 'application/json'
}
# Convert max_tokens to integer if it's a string
max_tokens_int = int(pepgenx_max_tokens) if isinstance(pepgenx_max_tokens, str) else pepgenx_max_tokens
payload = {
    "generation_model": pepgenx_model,
    "max_tokens": max_tokens_int,
    "temperature": temperature,
    "top_p": 0.9,
    "n": 1,
    "stop": ["string"],
    "presence_penalty": 0,
    "frequency_penalty": 0,
    "logit_bias": {},
    "tool_choice": "none",
    "seed": 0,
    "custom_prompt": formatting_prompt,
}
# Increased timeout to 120 seconds for large formatting requests
# Add retry logic for transient failures
max_retries = 2
result = None
for attempt in range(max_retries):
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(pepgenx_api_url, json=payload, headers=headers)