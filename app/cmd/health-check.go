package cmd

import (
	"fmt"
	"net/http"
	"os"

	"github.com/spf13/cobra"
)

var healthCheckCmd = &cobra.Command{
	Use:   "health-check",
	Short: "Perform health-check on running server",
	Run: func(cmd *cobra.Command, args []string) {
		resp, err := http.Get(fmt.Sprintf("http://localhost:%d/_/is-healthy", appConfig.Bind.Port))
		if err != nil || resp.StatusCode >= 400 {
			fmt.Println("health-check failed")
			os.Exit(1)
		}
		defer resp.Body.Close()
		fmt.Println("health-check successful")
		os.Exit(0)
	},
}

func init() {
	rootCmd.AddCommand(healthCheckCmd)
}
