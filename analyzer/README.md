🧭 Goal
From a Rust repository, collect metrics like:

Number of extern "C" blocks

Number of #[link(name = "...")] attributes

Number of use std::ffi::* or unsafe extern usage

Function signatures exposed with extern "C" or marked #[no_mangle]

🎈 Method
clone repositories with rust scripts
use the syn crate to parse Rust files
walk the Abstract Syntax Tree for Foreign Function Interface indicators.

👓 args for analyzer.py
python analyzer.py <repo json filename>

you can use filtered_rs_repos.json
