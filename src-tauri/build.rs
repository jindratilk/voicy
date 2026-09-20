fn main() {
    tauri_build::try_build(tauri_build::Attributes::new().app_manifest(
        tauri_build::AppManifest::new().commands(&[
            "export_audio",
            "open_audio",
            "take_open_file",
            "preferences",
            "save_preferences",
            "set_activity",
            "open_diagnostics",
        ]),
    ))
    .expect("Tauri build failed")
}
