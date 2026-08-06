// Rust の regex クレートは有限オートマトンで線形時間を保証する
use regex::Regex;
use std::time::Instant;

fn main() {
    let re = Regex::new(r"(a+)+$").unwrap();
    for n in [16usize, 20, 24, 26, 28] {
        let subject = format!("{}!", "a".repeat(n));
        let start = Instant::now();
        re.is_match(&subject);
        let sec = start.elapsed().as_secs_f64();
        println!("  n={:3}  {:.6} s", n, sec);
    }
}
