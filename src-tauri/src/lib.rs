use std::sync::Mutex;

struct AppState {
    engine_port: Mutex<Option<u16>>,
}

#[tauri::command]
fn start_engine(app: tauri::AppHandle, state: tauri::State<'_, AppState>) -> Result<u16, String> {
    let mut port_guard = state.engine_port.lock().unwrap();
    if let Some(p) = *port_guard {
        return Ok(p);
    }

    let picked_port = portpicker::pick_unused_port()
        .ok_or("No available port found")?;

    use tauri_plugin_shell::ShellExt;

    // On macOS, remove quarantine attribute from sidecar binary
    // so Gatekeeper doesn't block it from running
    #[cfg(target_os = "macos")]
    {
        if let Ok(resource_dir) = app.path().resource_dir() {
            let binaries_dir = resource_dir.join("binaries");
            if binaries_dir.exists() {
                // Remove quarantine from the entire binaries directory
                let _ = std::process::Command::new("xattr")
                    .args(["-cr", &binaries_dir.to_string_lossy()])
                    .output();
            }
        }
    }

    let sidecar_command = app.shell()
        .sidecar("subaligner-engine")
        .map_err(|e| format!("Failed to create sidecar command: {}", e))?
        .args(["--port", &picked_port.to_string()]);

    let (mut rx, _child) = sidecar_command.spawn()
        .map_err(|e| format!(
            "AI 引擎启动失败: {}\n\n可能原因：\n1. 缺少 AI 引擎可执行文件\n2. 系统不兼容\n3. macOS 安全限制阻止了引擎运行\n\n请尝试：系统设置 → 隐私与安全性 → 允许运行",
            e
        ))?;

    // Monitor sidecar output for crash detection and logging
    let app_handle = app.clone();
    std::thread::spawn(move || {
        while let Some(event) = rx.blocking_recv() {
            match event {
                tauri_plugin_shell::process::CommandEvent::Terminated(status) => {
                    eprintln!("[SubAligner] Engine process exited with status: {:?}", status);
                    let msg = format!("AI 引擎已退出 (状态: {:?})", status);
                    let _ = app_handle.emit("engine-exit", &msg);
                }
                tauri_plugin_shell::process::CommandEvent::Error(err) => {
                    eprintln!("[SubAligner] Engine error: {}", err);
                    let _ = app_handle.emit("engine-error", &err);
                }
                tauri_plugin_shell::process::CommandEvent::Stdout(line) => {
                    eprintln!("[SubAligner] Engine stdout: {}", String::from_utf8_lossy(&line));
                }
                tauri_plugin_shell::process::CommandEvent::Stderr(line) => {
                    let msg = String::from_utf8_lossy(&line).to_string();
                    eprintln!("[SubAligner] Engine stderr: {}", msg);
                    // Forward important stderr to frontend
                    if msg.contains("Error") || msg.contains("error") || msg.contains("Traceback") {
                        let _ = app_handle.emit("engine-error", &msg);
                    }
                }
                _ => {}
            }
        }
    });

    *port_guard = Some(picked_port);
    Ok(picked_port)
}

#[tauri::command]
fn reset_engine(state: tauri::State<'_, AppState>) {
    let mut port_guard = state.engine_port.lock().unwrap();
    *port_guard = None;
}

#[tauri::command]
fn get_engine_port(state: tauri::State<'_, AppState>) -> Option<u16> {
    *state.engine_port.lock().unwrap()
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .manage(AppState {
            engine_port: Mutex::new(None),
        })
        .invoke_handler(tauri::generate_handler![
            start_engine,
            reset_engine,
            get_engine_port,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
