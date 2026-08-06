// Rust の regex クレートは置換文字列で $1 系を使う（JavaScript と同じ系統）。
// ただし名前の切れ目の決め方が JavaScript とは違うため、matrix.py で差分を測る。
//
//   group-replace <入力>                    既定のテンプレート $3/$2/$1 で置換して出力する
//   group-replace <入力> <テンプレート>        指定のテンプレートで置換して出力する
//   group-replace <入力> <テンプレート> all    replace_all で全件置換する（既定は replace = 1 件）
//   group-replace <入力> <テンプレート> count  該当件数を find_iter で数えて出力する
use regex::Regex;
use std::env;

const PATTERN: &str = r"(\d{4})-(\d{2})-(\d{2})";
const DEFAULT_TEMPLATE: &str = "$3/$2/$1";

fn main() {
    let args: Vec<String> = env::args().skip(1).collect();
    let input = args
        .first()
        .cloned()
        .unwrap_or_else(|| "納品日は 2026-06-12 です".to_string());
    let template = args.get(1).cloned().unwrap_or_else(|| DEFAULT_TEMPLATE.to_string());
    let mode = args.get(2).cloned().unwrap_or_else(|| "first".to_string());

    let re = Regex::new(PATTERN).unwrap();

    // 置換関数は件数を返さない。何件当たったかは find_iter で別に数える。
    if mode == "count" {
        println!("{}", re.find_iter(&input).count());
        return;
    }

    let replaced = if mode == "all" {
        re.replace_all(&input, template.as_str()).into_owned()
    } else {
        re.replace(&input, template.as_str()).into_owned()
    };
    println!("{}", replaced);
}
