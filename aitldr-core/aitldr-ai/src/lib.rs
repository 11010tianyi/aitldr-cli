pub mod config;

use config::AiConfig;
use thiserror::Error;

#[derive(Error, Debug)]
pub enum AiError {
    #[error("No API key for provider: {0}")]
    MissingKey(String),
    #[error("HTTP error: {0}")]
    Http(#[from] reqwest::Error),
    #[error("Invalid response: {0}")]
    InvalidResponse(String),
}

pub type Result<T> = std::result::Result<T, AiError>;

pub async fn generate_page(command: &str, config: &AiConfig) -> Result<String> {
    match config.provider.as_str() {
        "deepseek" => generate_deepseek(command, config).await,
        "openai" => generate_openai(command, config).await,
        _ => Err(AiError::MissingKey(config.provider.clone())),
    }
}

async fn generate_deepseek(command: &str, config: &AiConfig) -> Result<String> {
    let api_key = config.deepseek_key.as_ref().ok_or_else(|| AiError::MissingKey("deepseek".to_string()))?;

    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(30))
        .build()?;

    let lang_instruction = if config.language == "zh" {
        "用中文输出命令说明和示例描述"
    } else {
        "Output command descriptions in English"
    };

    let prompt = format!(r#"Generate a TLDR page for command: {}

CRITICAL: If unsure if command exists, output "# {}\n\n> Command not found, may be a typo."

Requirements:
- Follow tldr-pages format
- Maximum 8 examples
- Use concise wording
- {}

Format:
# {}

> Brief description

- Example description:
`{{{{{arg1}}}}`

Generate only markdown, no other text."#, command, command, lang_instruction, command);

    let response = client
        .post("https://api.deepseek.com/chat/completions")
        .header("Authorization", format!("Bearer {}", api_key))
        .header("Content-Type", "application/json")
        .json(&serde_json::json!({
            "model": config.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 800,
        }))
        .send()
        .await?;

    let data: serde_json::Value = response.json().await?;
    data["choices"][0]["message"]["content"]
        .as_str()
        .map(|s| s.trim().to_string())
        .ok_or_else(|| AiError::InvalidResponse("No content".to_string()))
}

async fn generate_openai(command: &str, config: &AiConfig) -> Result<String> {
    Err(AiError::MissingKey("openai".to_string()))
}
