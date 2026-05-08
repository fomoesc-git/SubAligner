use std::process::Command;
use std::sync::Mutex;

use tauri::Manager;

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

    let port_arg = picked_port.to_string();

    // 1) Prefer bundled standalone engine executable (for production packages)
    let bundled_engine_name = if cfg!(target_os = "windows") {
        "subaligner-engine-x86_64-pc-windows-msvc.exe"
    } else if cfg!(target_os = "macos") {
        if cfg!(target_arch = "aarch64") {
            "subaligner-engine-aarch64-apple-darwin"
        } else {
            "subaligner-engine-x86_64-apple-darwin"
        }
    } else {
        if cfg!(target_arch = "aarch64") {
            "subaligner-engine-aarch64-unknown-linux"
        } else {
            "subaligner-engine-x86_64-unknown-linux"
        }
    };

    let bundled_engine_path = engine_dir.join("bin").join(bundled_engine_name);
    let mut started = false;
    let mut start_errors: Vec<String> = Vec::new();

    if bundled_engine_path.exists() {
        if let Err(e) = Command::new(&bundled_engine_path)
            .arg("--port")
            .arg(&port_arg)
            .current_dir(&engine_dir)
            .spawn()
        {
            start_errors.push(format!(
                "独立引擎可执行文件启动失败 ({}): {}",
                bundled_engine_path.display(),
                e
            ));
        } else {
            started = true;
        }
    }

    // 2) Fallback to Python script (for local development)
    if !started {
        let main_py = engine_dir.join("main.py");

        if main_py.exists() {
            let python_cmds: &[&str] = if cfg!(target_os = "windows") {
                &["python", "py"]
            } else {
                &["python3", "python"]
            };

            for python_cmd in python_cmds {
                match Command::new(python_cmd)
                    .arg(&main_py)
                    .arg("--port")
                    .arg(&port_arg)
                    .current_dir(&engine_dir)
                    .spawn()
                {
                    Ok(_) => {
                        started = true;
                        break;
                    }
                    Err(e) => {
                        start_errors.push(format!("{} 启动失败: {}", python_cmd, e));
                    }
                }
            }
        } else {
            start_errors.push(format!("引擎入口文件不存在: {}", main_py.display()));
        }
    }

    if !started {
        return Err(format!(
            "AI 引擎启动失败。\n\n尝试记录:\n{}\n\n可能原因:\n1. 安装包未包含对应平台引擎二进制\n2. 系统安全策略/杀毒软件拦截了引擎进程\n3. 开发模式下缺少 Python 运行环境",
            start_errors.join("\n")
        ));
    }

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
