use std::{env, fs, path::Path};
use syn::{Item, Attribute};
use walkdir::WalkDir;

struct RustFileStats {
    lines: usize,
    depth: usize,
    extern_c: usize,
    link_attr: usize,
    no_mangle: usize,
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

fn analyze_repo(repo_path: &str) -> Vec<RustFileStats> {
    let mut stats = Vec::new();

    for entry in WalkDir::new(repo_path)
        .into_iter()
        .filter_map(Result::ok)
        .filter(|e| e.path().extension().map(|ext| ext == "rs").unwrap_or(false))
    {
        let content = fs::read_to_string(entry.path()).unwrap_or_default();
        let lines = content.lines().count();
        let depth = entry.depth();

        let parsed = match syn::parse_file(&content) {
            Ok(p) => p,
            Err(_) => continue,
        };

        let mut extern_c = 0;
        let mut link_attr = 0;
        let mut no_mangle = 0;

        for item in parsed.items {
            if let Item::ForeignMod(fm) = &item {
                if fm.abi.name.as_ref().map(|n| n.value() == "C").unwrap_or(false) {
                    extern_c += 1;
                }
            }

            for attr in get_attrs(&item) {
                if attr.path().is_ident("link") {
                    link_attr += 1;
                }
                if attr.path().is_ident("no_mangle") {
                    no_mangle += 1;
                }
            }
        }

        stats.push(RustFileStats {
            lines,
            depth,
            extern_c,
            link_attr,
            no_mangle,
        });
    }

    stats
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("Usage: rust_ffi_metrics <path>");
        std::process::exit(1);
    }

    let repo_path = &args[1];
    let stats = analyze_repo(repo_path);

    let total_lines: usize = stats.iter().map(|s| s.lines).sum();
    let total_extern_c: usize = stats.iter().map(|s| s.extern_c).sum();
    let total_link_attr: usize = stats.iter().map(|s| s.link_attr).sum();
    let total_no_mangle: usize = stats.iter().map(|s| s.no_mangle).sum();
    let max_depth: usize = stats.iter().map(|s| s.depth).max().unwrap_or(0);

    println!("Total lines of Rust code: {}", total_lines);
    println!("Total extern \"C\" blocks: {}", total_extern_c);
    println!("Total #[link(...)] attributes: {}", total_link_attr);
    println!("Total #[no_mangle] functions: {}", total_no_mangle);
    println!("Maximum Rust file depth: {}", max_depth);

    let classification = if total_extern_c > 0 || total_link_attr > 0 || total_no_mangle > 0 {
        "FFI-related"
    } else {
        "Pure Rust"
    };
    println!("Repository classification: {}", classification);
}
