#!/usr/bin/env python3

from core.llms import LLMFactory, AzureOpenAIConfig, BedrockConfig, GeminiConfig, LLMProvider

# Test configuration creation
azure_config = AzureOpenAIConfig(
    provider=LLMProvider.AZURE_OPENAI,
    model_name='gpt-4',
    api_key='test',
    endpoint='https://test.openai.azure.com/',
    deployment_name='test-deployment'
)
print('Azure configuration created successfully!')

bedrock_config = BedrockConfig(
    provider=LLMProvider.BEDROCK,
    model_name='anthropic.claude-3-sonnet-20240229-v1:0',
    api_key='test',
    region='us-east-1'
)
print('Bedrock configuration created successfully!')

gemini_config = GeminiConfig(
    provider=LLMProvider.GEMINI,
    model_name='gemini-pro',
    api_key='test',
    project_id='test-project'
)
print('Gemini configuration created successfully!')

# Test provider listing
providers = LLMFactory.get_supported_providers()
print(f'Available providers: {[p.value for p in providers]}')

# Test LLM creation (will fail due to missing dependencies)
print('Trying to create Azure LLM (will fail due to missing openai library)...')
try:
    llm = LLMFactory.create_llm(azure_config)
    print('LLM created successfully!')
except Exception as e:
    print(f'Expected error: {type(e).__name__}: {e}')

print('All tests completed successfully!')
