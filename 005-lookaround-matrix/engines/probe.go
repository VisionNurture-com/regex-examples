// 機能判定の Go 側。matrix.py から TSV を受け取り、判定結果を TSV で返す。
//
// Go の regexp は RE2 系で、バックトラッキングしない代わりに書けない記法がある。
// 「書けない」ことも成果物なので、コンパイルエラーはそのまま出力する。
package main

import (
	"bufio"
	"fmt"
	"os"
	"regexp"
	"strings"
)

func main() {
	scanner := bufio.NewScanner(os.Stdin)
	out := bufio.NewWriter(os.Stdout)
	defer out.Flush()

	for scanner.Scan() {
		line := scanner.Text()
		if strings.TrimSpace(line) == "" {
			continue
		}
		cols := strings.Split(line, "\t")
		if len(cols) < 4 {
			continue
		}
		id, pattern, subject, expected := cols[0], cols[1], cols[2], cols[3]

		re, err := regexp.Compile(pattern)
		if err != nil {
			msg := strings.SplitN(err.Error(), "\n", 2)[0]
			fmt.Fprintf(out, "%s\tERROR:%s\n", id, msg)
			continue
		}
		got := re.FindString(subject)
		switch {
		case got == "":
			fmt.Fprintf(out, "%s\tNG:none\n", id)
		case got == expected:
			fmt.Fprintf(out, "%s\tOK\n", id)
		default:
			fmt.Fprintf(out, "%s\tNG:%s\n", id, got)
		}
	}
}
