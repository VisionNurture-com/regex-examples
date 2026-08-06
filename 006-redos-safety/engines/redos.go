// Go の regexp は RE2 系で、バックトラッキングをしない
package main

import (
	"encoding/json"
	"fmt"
	"regexp"
	"strings"
	"time"
)

type row struct {
	N   int     `json:"n"`
	Sec float64 `json:"sec"`
}

func main() {
	re := regexp.MustCompile(`(a+)+$`)
	var rows []row
	for _, n := range []int{16, 20, 24, 26, 28} {
		subject := strings.Repeat("a", n) + "!"
		start := time.Now()
		re.MatchString(subject)
		sec := time.Since(start).Seconds()
		rows = append(rows, row{n, sec})
		fmt.Printf("  n=%3d  %.6f s\n", n, sec)
	}
	out, _ := json.Marshal(map[string]any{"engine": "Go regexp (RE2)", "results": rows})
	fmt.Println(string(out))
}
