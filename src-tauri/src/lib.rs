use std::sync::Mutex;

use tauri::Manager;
use tauri_plugin_shell::ShellExt;

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

    // Find the bundled engine directory inside the app resources
    let engine_dir = if let Ok(resource_dir) = app.path().resource_dir() {
        resource_dir.join("engine")
    } else {
        return Err("无法获取应用资源目录".into());
    };

    if !engine_dir.exists() {
        return Err(format!("引擎目录不存在: {}", engine_dir.display()));
    }

    // On macOS, remove quarantine attribute so Gatekeeper doesn't block the engine
    #[cfg(target_os = "macos")]
    {
        let _ = std::process::Command::new("xattr")
            .args(["-cr", &engine_dir.to_string_lossy()])
            .output();
    }

    // Find Python interpreter
    let python_cmd = if cfg!(target_os = "windows") { "python" } else { "python3" };

    let main_py = engine_dir.join("main.py");
    if !main_py.exists() {
        return Err(format!("引擎入口文件不存在: {}", main_py.display()));
    }

    // Spawn the Python engine process
    app.shell()
        .command(python_cmd)
        .args([main_py.to_string_lossy().as_ref(), "--port", &picked_port.to_string()])
        .spawn()
        .map_err(|e| format!(
            "AI 引擎启动失败: {}\n\n可能原因:\n1. 系统缺少 Python 环境\n2. macOS 安全限制阻止了引擎运行\n3. 杀毒软件拦截了引擎进程",
            e
        ))?;

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
