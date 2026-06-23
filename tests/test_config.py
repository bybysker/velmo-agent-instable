from velmo.config import load_settings


def test_load_settings_reads_inference_env(monkeypatch):
    monkeypatch.delenv("AZURE_AI_ENDPOINT", raising=False)
    monkeypatch.setenv(
        "AZURE_AI_INFERENCE_ENDPOINT", "https://demo.services.ai.azure.com/openai/v1"
    )
    monkeypatch.setenv("AZURE_AI_INFERENCE_API_KEY", "secret-key")
    monkeypatch.setenv("AZURE_AI_INFERENCE_MODEL", "Kimi-K2.6")

    settings = load_settings()

    assert settings.endpoint == "https://demo.services.ai.azure.com/openai/v1"
    assert settings.api_key == "secret-key"
    assert settings.model == "Kimi-K2.6"
