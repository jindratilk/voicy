#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]
use serde::{Deserialize, Serialize};
use std::{
    fs,
    io::{self, Write},
    net::TcpListener,
    path::PathBuf,
    process::{Child, Command, Stdio},
    sync::{
        atomic::{AtomicBool, Ordering},
        Mutex,
    },
    time::{Duration, Instant},
};
use tauri::{
    menu::{AboutMetadata, Menu, MenuItem, PredefinedMenuItem as P, Submenu},
    Emitter, Manager, WindowEvent,
};
use tauri_plugin_dialog::{DialogExt, MessageDialogButtons};

struct Backend {
    child: Mutex<Option<Child>>,
    url: Mutex<String>,
    token: String,
    busy: AtomicBool,
    exiting: AtomicBool,
    quit_pending: AtomicBool,
    pending: Mutex<Vec<PathBuf>>,
}
#[derive(Default, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
struct Preferences {
    active_id: Option<String>,
    level: Option<bool>,
    width: Option<f64>,
    height: Option<f64>,
}
fn support() -> PathBuf {
    PathBuf::from(std::env::var_os("HOME").unwrap_or_default())
        .join("Library/Application Support/Voicy")
}
fn prefs() -> Preferences {
    fs::read(support().join("preferences.json"))
        .ok()
        .and_then(|v| serde_json::from_slice(&v).ok())
        .unwrap_or_default()
}
fn client() -> Result<reqwest::blocking::Client, reqwest::Error> {
    reqwest::blocking::Client::builder()
        .timeout(Duration::from_secs(120))
        .build()
}
fn show(app: &tauri::AppHandle) {
    if let Some(w) = app.get_webview_window("main") {
        let _ = w.show();
        let _ = w.unminimize();
        let _ = w.set_focus();
    }
}
fn stop(app: &tauri::AppHandle) {
    let state = app.state::<Backend>();
    state.exiting.store(true, Ordering::SeqCst);
    if let Some(mut c) = state.child.lock().unwrap().take() {
        unsafe {
            libc::kill(-(c.id() as i32), libc::SIGTERM);
        }
        let _ = c.kill();
        let _ = c.wait();
    };
}
#[tauri::command]
fn open_diagnostics() {
    let _ = Command::new("/usr/bin/open")
        .arg(support().join("logs"))
        .spawn();
}
#[tauri::command]
fn preferences() -> Preferences {
    prefs()
}
#[tauri::command]
fn save_preferences(
    active_id: Option<String>,
    level: bool,
    app: tauri::AppHandle,
) -> Result<(), String> {
    let mut p = prefs();
    p.active_id = active_id;
    p.level = Some(level);
    if let Some(w) = app.get_webview_window("main") {
        if let Ok(size) = w.inner_size() {
            let factor = w.scale_factor().unwrap_or(1.);
            p.width = Some(size.width as f64 / factor);
            p.height = Some(size.height as f64 / factor);
        }
    }
    fs::create_dir_all(support()).map_err(|e| e.to_string())?;
    let temp = support().join("preferences.next");
    fs::write(&temp, serde_json::to_vec(&p).unwrap()).map_err(|e| e.to_string())?;
    fs::rename(temp, support().join("preferences.json")).map_err(|e| e.to_string())
}
#[tauri::command]
fn set_activity(busy: bool, exportable: bool, app: tauri::AppHandle) {
    app.state::<Backend>().busy.store(busy, Ordering::SeqCst);
    if let Some(menu) = app.menu() {
        for (id, enabled) in [
            ("open", !busy),
            ("save", exportable && !busy),
            ("enhance", !busy),
        ] {
            if let Some(item) = menu.get(id).and_then(|i| i.as_menuitem().cloned()) {
                let _ = item.set_enabled(enabled);
            }
        }
    }
}
fn upload_path(app: &tauri::AppHandle, path: PathBuf) -> Result<serde_json::Value, String> {
    let size = fs::metadata(&path).map_err(|e| e.to_string())?.len();
    if size == 0 || size > 250 * 1024 * 1024 {
        return Err("Choose an audio file between 1 byte and 250 MB.".into());
    }
    let state = app.state::<Backend>();
    let url = state.url.lock().unwrap().clone();
    let form = reqwest::blocking::multipart::Form::new()
        .file("file", path)
        .map_err(|e| e.to_string())?;
    client()
        .map_err(|e| e.to_string())?
        .post(format!("{url}/api/jobs"))
        .header("X-Voicy-Token", &state.token)
        .multipart(form)
        .send()
        .map_err(|e| e.to_string())?
        .error_for_status()
        .map_err(|e| e.to_string())?
        .json()
        .map_err(|e| e.to_string())
}
#[tauri::command]
async fn open_audio(app: tauri::AppHandle) -> Result<Option<serde_json::Value>, String> {
    tauri::async_runtime::spawn_blocking(move || {
        if app.state::<Backend>().busy.load(Ordering::SeqCst) {
            return Err("Wait for processing to finish.".into());
        }
        let Some(file) = app
            .dialog()
            .file()
            .add_filter(
                "Audio",
                &[
                    "wav", "mp3", "m4a", "flac", "ogg", "aiff", "aif", "webm", "mp4",
                ],
            )
            .blocking_pick_file()
        else {
            return Ok(None);
        };
        upload_path(&app, file.into_path().map_err(|e| e.to_string())?).map(Some)
    })
    .await
    .map_err(|e| e.to_string())?
}
#[tauri::command]
async fn take_open_file(app: tauri::AppHandle) -> Result<Option<serde_json::Value>, String> {
    tauri::async_runtime::spawn_blocking(move || {
        let path = app.state::<Backend>().pending.lock().unwrap().pop();
        path.map(|p| upload_path(&app, p)).transpose()
    })
    .await
    .map_err(|e| e.to_string())?
}
#[tauri::command]
async fn export_audio(job_id: String, app: tauri::AppHandle) -> Result<bool, String> {
    tauri::async_runtime::spawn_blocking(move || {
        if job_id.len() != 32 || !job_id.chars().all(|c| c.is_ascii_hexdigit()) {
            return Err("Invalid recording".into());
        }
        let state = app.state::<Backend>();
        let url = state.url.lock().unwrap().clone();
        let c = client().map_err(|e| e.to_string())?;
        let metadata: serde_json::Value = c
            .get(format!("{url}/api/jobs/{job_id}"))
            .header("X-Voicy-Token", &state.token)
            .send()
            .and_then(|r| r.error_for_status())
            .and_then(|r| r.json())
            .map_err(|e| e.to_string())?;
        let name = metadata["name"].as_str().unwrap_or("Recording");
        let name = PathBuf::from(name);
        let name = name.file_stem().unwrap_or_default().to_string_lossy();
        let Some(file) = app
            .dialog()
            .file()
            .set_file_name(format!("{name}-voicy.wav"))
            .add_filter("WAV audio", &["wav"])
            .blocking_save_file()
        else {
            return Ok(false);
        };
        let path = file.into_path().map_err(|e| e.to_string())?;
        let mut response = c
            .get(format!("{url}/api/jobs/{job_id}/audio/enhanced"))
            .header("X-Voicy-Token", &state.token)
            .send()
            .and_then(|r| r.error_for_status())
            .map_err(|e| e.to_string())?;
        let temporary = path.with_file_name(format!(".voicy-{}.tmp", uuid::Uuid::new_v4()));
        let result = (|| -> Result<(), io::Error> {
            let mut out = fs::OpenOptions::new()
                .write(true)
                .create_new(true)
                .open(&temporary)?;
            io::copy(&mut response, &mut out)?;
            out.flush()?;
            out.sync_all()?;
            fs::rename(&temporary, &path)
        })();
        if result.is_err() {
            let _ = fs::remove_file(temporary);
        }
        result.map_err(|e| e.to_string())?;
        Ok(true)
    })
    .await
    .map_err(|e| e.to_string())?
}
fn native_menu(app: &tauri::AppHandle) -> tauri::Result<Menu<tauri::Wry>> {
    let app_menu = Submenu::with_items(
        app,
        "Voicy",
        true,
        &[
            &P::about(
                app,
                None,
                Some(AboutMetadata {
                    name: Some("Voicy".into()),
                    version: Some("0.3.0".into()),
                    comments: Some("Local speech enhancement with AuK.".into()),
                    ..Default::default()
                }),
            )?,
            &P::separator(app)?,
            &P::services(app, None)?,
            &P::separator(app)?,
            &P::hide(app, None)?,
            &P::hide_others(app, None)?,
            &P::show_all(app, None)?,
            &P::separator(app)?,
            &MenuItem::with_id(app, "quit", "Quit Voicy", true, Some("CmdOrCtrl+Q"))?,
        ],
    )?;
    let file = Submenu::with_items(
        app,
        "File",
        true,
        &[
            &MenuItem::with_id(app, "open", "Open Audio…", true, Some("CmdOrCtrl+O"))?,
            &MenuItem::with_id(app, "save", "Export Audio…", false, Some("CmdOrCtrl+S"))?,
            &P::separator(app)?,
            &P::close_window(app, None)?,
        ],
    )?;
    let edit = Submenu::with_items(
        app,
        "Edit",
        true,
        &[
            &P::undo(app, None)?,
            &P::redo(app, None)?,
            &P::separator(app)?,
            &P::cut(app, None)?,
            &P::copy(app, None)?,
            &P::paste(app, None)?,
            &P::select_all(app, None)?,
        ],
    )?;
    let audio = Submenu::with_items(
        app,
        "Audio",
        true,
        &[
            &MenuItem::with_id(app, "play", "Play / Pause", true, None::<&str>)?,
            &MenuItem::with_id(
                app,
                "compare",
                "Compare Original / Enhanced",
                true,
                Some("CmdOrCtrl+Shift+A"),
            )?,
            &MenuItem::with_id(app, "enhance", "Enhance", true, Some("CmdOrCtrl+Return"))?,
        ],
    )?;
    let window = Submenu::with_items(
        app,
        "Window",
        true,
        &[
            &P::minimize(app, None)?,
            &P::maximize(app, None)?,
            &P::fullscreen(app, None)?,
            &P::separator(app)?,
            &MenuItem::with_id(
                app,
                "history",
                "Recordings",
                true,
                Some("CmdOrCtrl+Shift+O"),
            )?,
            &MenuItem::with_id(app, "show", "Show Voicy", true, Some("CmdOrCtrl+1"))?,
        ],
    )?;
    let help = Submenu::with_items(
        app,
        "Help",
        true,
        &[&MenuItem::with_id(
            app,
            "diagnostics",
            "Open Diagnostics…",
            true,
            None::<&str>,
        )?],
    )?;
    Menu::with_items(app, &[&app_menu, &file, &edit, &audio, &window, &help])
}
fn start_backend(app: tauri::AppHandle) -> Result<(), Box<dyn std::error::Error>> {
    let resource = app.path().resource_dir()?;
    let bundled = resource.join("runtime");
    let root = std::env::var_os("CLEARVOICE_ROOT")
        .map(PathBuf::from)
        .unwrap_or_else(|| {
            if bundled.join("server/app.py").is_file() {
                bundled
            } else {
                support().join("runtime")
            }
        });
    let data = support().join("runtime/.data");
    fs::create_dir_all(&data)?;
    fs::create_dir_all(support().join("logs"))?;
    let log_path = support().join("logs/engine.log");
    if fs::metadata(&log_path)
        .map(|m| m.len() > 5 * 1024 * 1024)
        .unwrap_or(false)
    {
        let _ = fs::rename(&log_path, log_path.with_extension("previous.log"));
    }
    let log = fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open(log_path)?;
    let listener = TcpListener::bind("127.0.0.1:0")?;
    let port = listener.local_addr()?.port();
    drop(listener);
    let state = app.state::<Backend>();
    let url = format!("http://127.0.0.1:{port}");
    *state.url.lock().unwrap() = url.clone();
    let portable = root.join("python/bin/python3");
    let python = if portable.exists() {
        portable
    } else {
        root.join(".venv/bin/python")
    };
    let mut cmd = Command::new(python);
    cmd.current_dir(&root)
        .args([
            "-m",
            "uvicorn",
            "server.app:app",
            "--host",
            "127.0.0.1",
            "--port",
            &port.to_string(),
            "--no-access-log",
        ])
        .env("VOICY_SESSION_TOKEN", &state.token)
        .env("CLEARVOICE_DATA", &data)
        .env("VOICY_WEB_ROOT", resource.join("web"))
        .env(
            "PATH",
            format!(
                "{}:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin",
                root.join("bin").display()
            ),
        )
        .env("PYTHONUNBUFFERED", "1")
        .env("PYTHONNOUSERSITE", "1")
        .env("PYTHONPATH", &root)
        .env("PYTHONDONTWRITEBYTECODE", "1")
        .env("NUMBA_CACHE_DIR", support().join("cache/numba"))
        .env("MPLCONFIGDIR", support().join("cache/matplotlib"))
        .env("MPLBACKEND", "Agg")
        .env("HF_HUB_OFFLINE", "1")
        .env("TRANSFORMERS_OFFLINE", "1")
        .stdout(Stdio::from(log.try_clone()?))
        .stderr(Stdio::from(log));
    if root.join("python").exists() {
        cmd.env("PYTHONHOME", root.join("python"))
            .env("CLEARVOICE_AUK_PYTHON", root.join("python/bin/python3"))
            .env("CLEARVOICE_AUK_HOME", root.join(".auk"));
    }
    use std::os::unix::process::CommandExt;
    cmd.process_group(0);
    {
        let mut child = state.child.lock().unwrap();
        if state.exiting.load(Ordering::SeqCst) {
            return Ok(());
        }
        *child = Some(cmd.spawn()?);
    }
    let deadline = Instant::now() + Duration::from_secs(90);
    let c = reqwest::blocking::Client::builder()
        .timeout(Duration::from_secs(1))
        .build()?;
    loop {
        if state.exiting.load(Ordering::SeqCst) {
            return Ok(());
        }
        if let Some(child) = state.child.lock().unwrap().as_mut() {
            if let Some(status) = child.try_wait()? {
                return Err(format!(
                    "Audio engine exited ({status}). See Help → Open Diagnostics."
                )
                .into());
            }
        }
        if c.get(format!("{url}/api/health"))
            .header("X-Voicy-Token", &state.token)
            .send()
            .ok()
            .and_then(|r| r.json::<serde_json::Value>().ok())
            .is_some_and(|v| v["version"] == "0.3.0")
        {
            break;
        }
        if Instant::now() > deadline {
            return Err("Audio engine startup timed out. See Help → Open Diagnostics.".into());
        }
        std::thread::sleep(Duration::from_millis(100));
    }
    if let Some(w) = app.get_webview_window("main") {
        w.navigate(format!("{url}/session?token={}", state.token).parse()?)?;
    }
    Ok(())
}
fn request_quit(app: &tauri::AppHandle) {
    let state = app.state::<Backend>();
    if state.quit_pending.swap(true, Ordering::SeqCst) {
        return;
    }
    let handle = app.clone();
    std::thread::spawn(move || {
        let state = handle.state::<Backend>();
        let url = state.url.lock().unwrap().clone();
        let busy = reqwest::blocking::Client::builder()
            .timeout(Duration::from_secs(2))
            .build()
            .ok()
            .and_then(|c| {
                c.get(format!("{url}/api/jobs"))
                    .header("X-Voicy-Token", &state.token)
                    .send()
                    .ok()
            })
            .and_then(|r| r.json::<Vec<serde_json::Value>>().ok())
            .map(|jobs| {
                jobs.iter().any(|j| {
                    matches!(
                        j["status"].as_str(),
                        Some("queued" | "analyzing" | "enhancing")
                    )
                })
            })
            .unwrap_or_else(|| state.busy.load(Ordering::SeqCst));
        let confirmed = if busy {
            show(&handle);
            let mut dialog = handle
                .dialog()
                .message("An enhancement is running. Quit and stop processing?")
                .title("Quit Voicy?")
                .buttons(MessageDialogButtons::OkCancelCustom(
                    "Quit".into(),
                    "Keep Processing".into(),
                ));
            if let Some(window) = handle.get_webview_window("main") {
                dialog = dialog.parent(&window);
            }
            dialog.blocking_show()
        } else {
            true
        };
        if confirmed {
            stop(&handle);
            handle.exit(0);
        } else {
            state.quit_pending.store(false, Ordering::SeqCst);
        }
    });
}
fn main() {
    let app=tauri::Builder::default().plugin(tauri_plugin_single_instance::init(|app,_,_|show(app))).plugin(tauri_plugin_dialog::init())
    .invoke_handler(tauri::generate_handler![export_audio,open_audio,take_open_file,preferences,save_preferences,set_activity,open_diagnostics])
    .setup(|app|{
        fs::create_dir_all(support())?;
        app.manage(Backend{child:Mutex::new(None),url:Mutex::new(String::new()),token:format!("{}{}",uuid::Uuid::new_v4().simple(),uuid::Uuid::new_v4().simple()),busy:AtomicBool::new(false),exiting:AtomicBool::new(false),quit_pending:AtomicBool::new(false),pending:Mutex::new(Vec::new())});
        app.set_menu(native_menu(app.handle())?)?;
        let p=prefs();
        tauri::WebviewWindowBuilder::new(app,"main",tauri::WebviewUrl::App("startup.html".into())).title("Voicy")
         .inner_size(p.width.unwrap_or(1000.).clamp(760.,1600.),p.height.unwrap_or(650.).clamp(520.,1000.)).min_inner_size(760.,520.)
         .title_bar_style(tauri::TitleBarStyle::Overlay).hidden_title(true).traffic_light_position(tauri::LogicalPosition::new(20.,24.))
         .theme(Some(tauri::Theme::Dark)).background_color(tauri::window::Color(8,8,8,255)).disable_drag_drop_handler()
         .on_navigation(|url|url.scheme()=="tauri"||(url.scheme()=="http"&&url.host_str()==Some("127.0.0.1"))).build()?;
        let handle=app.handle().clone();std::thread::spawn(move||{if let Err(error)=start_backend(handle.clone()){
            let message=serde_json::to_string(&format!("{error}")).unwrap();if let Some(w)=handle.get_webview_window("main"){let _=w.eval(format!("document.querySelector('p').textContent={message};document.querySelector('button').hidden=false").as_str());}
        }});Ok(())
    }).on_menu_event(|app,event|{match event.id().as_ref(){"quit"=>request_quit(app),"show"=>show(app),"diagnostics"=>{let _=Command::new("/usr/bin/open").arg(support().join("logs")).spawn();},id=>{show(app);let _=app.emit("voicy-menu",id);}}})
    .on_window_event(|window,event|match event{WindowEvent::CloseRequested{api,..}=>{api.prevent_close();let p=prefs();let _=save_preferences(p.active_id,p.level.unwrap_or(true),window.app_handle().clone());let _=window.hide();},_=>{}})
    .build(tauri::generate_context!()).expect("Unable to start Voicy");
    app.run(|app, event| match event {
        tauri::RunEvent::Reopen { .. } => show(app),
        tauri::RunEvent::Opened { urls } => {
            let state = app.state::<Backend>();
            for url in urls {
                if let Ok(path) = url.to_file_path() {
                    state.pending.lock().unwrap().push(path)
                }
            }
            show(app);
            let _ = app.emit("voicy-open", ());
        }
        tauri::RunEvent::ExitRequested { api, .. } => {
            if !app.state::<Backend>().exiting.load(Ordering::SeqCst) {
                api.prevent_exit();
                request_quit(app);
            }
        }
        tauri::RunEvent::Exit => stop(app),
        _ => {}
    });
}
