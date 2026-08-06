// 機能判定の .NET 側。matrix.py から TSV を受け取り、判定結果を TSV で返す。
// 実行: dotnet run probe.cs（.NET 10 のファイルベース実行）
using System.Text.RegularExpressions;

string? line;
while ((line = Console.ReadLine()) != null)
{
    if (string.IsNullOrWhiteSpace(line)) continue;
    var cols = line.Split('\t');
    if (cols.Length < 4) continue;
    var (id, pattern, subject, expected) = (cols[0], cols[1], cols[2], cols[3]);

    try
    {
        var re = new Regex(pattern);
        var m = re.Match(subject);
        if (!m.Success) Console.WriteLine($"{id}\tNG:none");
        else if (m.Value == expected) Console.WriteLine($"{id}\tOK");
        else Console.WriteLine($"{id}\tNG:{m.Value}");
    }
    catch (Exception e)
    {
        var msg = e.Message.Split('\n')[0];
        Console.WriteLine($"{id}\tERROR:{msg}");
    }
}
