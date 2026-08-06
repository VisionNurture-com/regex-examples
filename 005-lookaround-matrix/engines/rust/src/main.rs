// 機能判定の Rust 側。matrix.py から TSV を受け取り、判定結果を TSV で返す。
//
// regex クレートは RE2 系で線形時間を保証する代わりに、先読みや後方参照を持たない。
// 「書けない」ことも成果物なので、コンパイルエラーはそのまま出力する。
use regex::Regex;
use std::io::{self, BufRead, Write};

fn main() {
    let stdin = io::stdin();
    let stdout = io::stdout();
    let mut out = stdout.lock();

    for line in stdin.lock().lines() {
        let line = match line {
            Ok(l) => l,
            Err(_) => break,
        };
        if line.trim().is_empty() {
            continue;
        }
        let cols: Vec<&str> = line.split('\t').collect();
        if cols.len() < 4 {
            continue;
        }
        let (id, pattern, subject, expected) = (cols[0], cols[1], cols[2], cols[3]);

        match Regex::new(pattern) {
            Err(e) => {
                // regex クレートのエラーは複数行にわたる。TSV に収めるため 1 行へ畳む
                let msg = e
                    .to_string()
                    .lines()
                    .map(str::trim)
                    .filter(|l| !l.is_empty())
                    .collect::<Vec<_>>()
                    .join(" / ");
                writeln!(out, "{}\tERROR:{}", id, msg).ok();
            }
            Ok(re) => match re.find(subject) {
                None => {
                    writeln!(out, "{}\tNG:none", id).ok();
                }
                Some(m) if m.as_str() == expected => {
                    writeln!(out, "{}\tOK", id).ok();
                }
                Some(m) => {
                    writeln!(out, "{}\tNG:{}", id, m.as_str()).ok();
                }
            },
        }
    }
}
