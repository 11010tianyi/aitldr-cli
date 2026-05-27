use std::path::PathBuf;
use dirs::home_dir;
use thiserror::Error;

#[derive(Error, Debug)]
pub enum CacheError {
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
    #[error("No home directory")]
    NoHome,
}

pub fn get_ai_cache_dir() -> Result<PathBuf, CacheError> {
    let home = home_dir().ok_or(CacheError::NoHome)?;
    let dir = home.join(".aitldr/ai");
    std::fs::create_dir_all(&dir)?;
    Ok(dir)
}

pub fn save_page(cmd: &str, content: &str) -> Result<(), CacheError> {
    let path = get_ai_cache_dir()?.join(format!("{}.md", cmd));
    std::fs::write(&path, content)?;
    Ok(())
}

pub fn load_page(cmd: &str) -> Result<Option<String>, CacheError> {
    let path = get_ai_cache_dir()?.join(format!("{}.md", cmd));
    Ok(path.exists().then(|| std::fs::read_to_string(&path).ok()).flatten())
}
