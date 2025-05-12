use std::{env, fs};
use std::path::Path;
use syn::{Item, Attribute, File};
use walkdir::WalkDir;
use serde::Serialize;

#[derive(Serialize)]
struct RepoStats {
    total_lines: usize,
    extern_c: usize,
    link_attr: usize,
    no_mangle: usize,
    unsafe_count: usize,
    unsafe_fn_count: usize,
    ffi_file_count: usize,
    max_depth: usize,
    classification: String,
}

fn get_attrs(item: &Item) -> &[Attribute] {
    match item {
        Item::Fn(f) => &f.attrs,
        Item::Mod(m) => &m.attrs,
        Item::Static(s) => &s.attrs,
        Item::Const(c) => &c.attrs,
        Item::Struct(s) => &s.attrs,
        Item::Enum(e) => &e.attrs,
        Item::Union(u) => &u.attrs,
        Item::Trait(t) => &t.attrs,
        Item::Impl(i) => &i.attrs,
        _ => &[],
    }
}

fn analyze_repo(repo_path: &str) -> RepoStats {
    let mut total_lines = 0;
    let mut extern_c = 0;
    let mut link_attr = 0;
    let mut no_mangle = 0;
    let mut unsafe_count = 0;
    let mut unsafe_fn_count = 0;
    let mut ffi_file_count = 0;
    let mut max_depth = 0;

    for entry in WalkDir::new(repo_path)
        .into_iter()
        .filter_map(Result::ok)
        .filter(|e| e.path().extension().map(|ext| ext == "rs").unwrap_or(false))
    {
        let content = fs::read_to_string(entry.path()).unwrap_or_default();
        let lines = content.lines().count();
        total_lines += lines;
        max_depth = max_depth.max(entry.depth());

        let parsed = match syn::parse_file(&content) {
            Ok(p) => p,
            Err(_) => continue,
        };

        let mut file_has_ffi = false;

        for item in &parsed.items {
            if let Item::ForeignMod(fm) = &item {
                if fm.abi.name.as_ref().map(|n| n.value() == "C").unwrap_or(false) {
                    extern_c += 1;
                    file_has_ffi = true;
                }
            }
            if let Item::Fn(f) = &item {
                if f.sig.unsafety.is_some() {
                    unsafe_fn_count += 1;
                    file_has_ffi = true;
                }
            }
            for attr in get_attrs(item) {
                if attr.path().is_ident("link") {
                    link_attr += 1;
                    file_has_ffi = true;
                }
                if attr.path().is_ident("no_mangle") {
                    no_mangle += 1;
                    file_has_ffi = true;
                }
            }
        }

        // Count unsafe blocks
        unsafe_count += content.matches("unsafe {").count(); // Fast and simple heuristic
        if content.contains("unsafe") {
            file_has_ffi = true;
        }

        if file_has_ffi {
            ffi_file_count += 1;
        }
    }

    let classification = if extern_c > 0 || link_attr > 0 || no_mangle > 0 {
        "FFI-related"
    } else {
        "Pure Rust"
    }.to_string();

    RepoStats {
        total_lines,
        extern_c,
        link_attr,
        no_mangle,
        unsafe_count,
        unsafe_fn_count,
        ffi_file_count,
        max_depth,
        classification,
    }
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("Usage: rust_ffi_metrics <path>");
        std::process::exit(1);
    }

    let repo_path = &args[1];
    let stats = analyze_repo(repo_path);

    let json = serde_json::to_string_pretty(&stats).unwrap();
    println!("{}", json);
}
