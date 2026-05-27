use std::process::Command;
use thiserror::Error;

#[derive(Error, Debug)]
pub enum RiskError {
    #[error("Command failed")]
    Failed,
}

pub fn command_exists(cmd: &str) -> bool {
    if cmd.is_empty() { return false; }
    #[cfg(unix)]
    {
        Command::new("sh")
            .args(["-c", &format!("command -v {} 2>/dev/null || which {} 2>/dev/null", cmd, cmd)])
            .output()
            .map(|o| o.status.success())
            .unwrap_or(false)
    }
    #[cfg(windows)]
    { Command::new("where").arg(cmd).output().map(|o| o.status.success()).unwrap_or(false) }
    #[cfg(not(any(unix, windows)))]
    { true }
}

pub fn is_destructive(cmd: &str) -> bool {
    ["rm -rf", "dd", "mkfs", ":(){ :|:& };:"].iter().any(|p| cmd.contains(p))
}
