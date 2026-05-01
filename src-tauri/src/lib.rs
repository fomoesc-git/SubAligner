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
    let sidecar_command = app.shell()
        .sidecar("subaligner-engine")
        .map_err(|e| format!("Failed to create sidecar command: {}", e))?
        .args(["--port", &picked_port.to_string()]);

    sidecar_command.spawn()
        .map_err(|e| format!("Failed to spawn sidecar: {}", e))?;

    *port_guard = Some(picked_port);

    Ok(picked_port)
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
            get_engine_port,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
