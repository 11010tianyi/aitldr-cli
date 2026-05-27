use serde::{Deserialize, Serialize};
use dirs::home_dir;
use std::fs;

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct AiConfig {
    pub provider: String,
    pub model: String,
    pub deepseek_key: Option<String>,
    pub openai_key: Option<String>,
    pub language: String,
}

impl Default for AiConfig {
    fn default() -> Self {
        Self {
            provider: "deepseek".to_string(),
            model: "deepseek-chat".to_string(),
            deepseek_key: None,
            openai_key: None,
            language: "zh".to_string(),
        }
    }
}

pub fn load_config() -> AiConfig {
    let config_path = home_dir()
        .unwrap()
        .join(".aitldr/config.toml");

    if !config_path.exists() {
        return AiConfig::default();
    }

    let content = match fs::read_to_string(&config_path) {
        Ok(c) => c,
        Err(_) => return AiConfig::default(),
    };

    parse_config(&content)
}

fn parse_config(content: &str) -> AiConfig {
    let provider = extract_value(content, "model", "provider")
        .unwrap_or_else(|| "deepseek".to_string());

    let model = extract_value(content, "model", "model")
        .unwrap_or_else(|| "deepseek-chat".to_string());

    let language = extract_value(content, "general", "language")
        .unwrap_or_else(|| "zh".to_string());

    let deepseek_key = extract_value(content, "deepseek", "api_key");
    let openai_key = extract_value(content, "openai", "api_key");

    AiConfig {
        provider,
        model,
        deepseek_key,
        openai_key,
        language,
    }
}

fn extract_value(content: &str, section: &str, key: &str) -> Option<String> {
    let section_start = content.find(&format!("[{}]", section))?;
    let section_end = content.find(|c| c == '[').map(|i| {
        let after_section = &content[section_start..];
        let next = after_section[1..].find('[');
        match next {
            Some(n) => section_start + 1 + n,
            None => content.len(),
        }
    }).unwrap_or(content.len());

    let section_content = &content[section_start..section_end];
    let key_line = section_content.lines().find(|line| line.starts_with(&format!("{} =", key)))?;
    let value = key_line.split('=').nth(1)?.trim().trim_matches('"').to_string();

    if value.starts_with("env:") {
        None  // Skip env vars for now
    } else if !value.is_empty() {
        Some(value)
    } else {
        None
    }
}
