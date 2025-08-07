package main

import (
	"fmt"
	"os"

	"github.com/enchant97/hasty-paste/app/cmd"
	_ "modernc.org/sqlite"
)

func main() {
	if err := cmd.Execute(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
