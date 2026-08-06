// .NET は既定でバックトラッキングするが、NonBacktracking を指定できる
using System.Diagnostics;
using System.Text.RegularExpressions;

foreach (var (name, opts) in new (string, RegexOptions)[] {
    ("既定", RegexOptions.None),
    ("NonBacktracking", RegexOptions.NonBacktracking) })
{
    Console.WriteLine($"  {name}:");
    var re = new Regex(@"(a+)+$", opts);
    foreach (var n in new[] { 16, 20, 24, 26, 28 })
    {
        var subject = new string('a', n) + "!";
        var sw = Stopwatch.StartNew();
        re.IsMatch(subject);
        sw.Stop();
        Console.WriteLine($"    n={n,3}  {sw.Elapsed.TotalSeconds:F6} s");
        if (sw.Elapsed.TotalSeconds > 10) { Console.WriteLine("    （10 秒を超えたため打ち切り）"); break; }
    }
}

// 戻らない方式は速いが、受け付けない書き方がある。
// 「爆発しないエンジンに替えれば済む」と考える前に、手元のパターンが移せるかを確かめる。
Console.WriteLine("  NonBacktracking が受け付ける書き方:");
foreach (var (label, pattern) in new (string, string)[] {
    ("後方参照", @"(\w+) \1"),
    ("先読み", @"\d+(?=円)"),
    ("後読み", @"(?<=¥)\d+"),
    ("入れ子の量指定子", @"(a+)+$") })
{
    try
    {
        _ = new Regex(pattern, RegexOptions.NonBacktracking);
        Console.WriteLine($"    ○ {label,-8} {pattern}");
    }
    catch (NotSupportedException e)
    {
        Console.WriteLine($"    × {label,-8} {pattern}");
        Console.WriteLine($"        {e.Message}");
    }
}
