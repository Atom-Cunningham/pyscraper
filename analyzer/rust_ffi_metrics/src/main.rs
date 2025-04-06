use std::{env, fs};
use syn::{Item, Attribute, File};
use walkdir::WalkDir;

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("Usage: rust_ffi_metrics <path>");
        std::process::exit(1);
    }

    let repo_path = &args[1];

    let mut extern_c_count = 0;
    let mut link_attr_count = 0;
    let mut no_mangle_count = 0;

    for entry in WalkDir::new(repo_path)
        .into_iter()
        .filter_map(Result::ok)
        .filter(|e| e.path().extension().map(|ext| ext == "rs").unwrap_or(false))
    {
        let content = fs::read_to_string(entry.path()).unwrap_or_default();
        let parsed: syn::File = match syn::parse_file(&content) {
            Ok(p) => p,
            Err(_) => continue,
        };

        for item in parsed.items {
            match &item {
                Item::ForeignMod(fm) => {
                    if fm.abi.name.as_ref().map(|n| n.value() == "C").unwrap_or(false) {
                        extern_c_count += 1;
                    }
                }
                _ => {}
            }

            for attr in get_attrs(&item) {
                if attr.path().is_ident("link") {
                    link_attr_count += 1;
                }
                if attr.path().is_ident("no_mangle") {
                    no_mangle_count += 1;
                }
            }
        }
    }

    println!("Extern \"C\" blocks: {}", extern_c_count);
    println!("#[link(...)] attributes: {}", link_attr_count);
    println!("#[no_mangle] functions: {}", no_mangle_count);
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
