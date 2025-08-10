package cmd

import (
	"context"
	"fmt"

	"github.com/spf13/cobra"
)

var (
	viewUsername string
)

var viewCmd = &cobra.Command{
	Use:   "view",
	Short: "View entries",
}

var viewUsersCmd = &cobra.Command{
	Use:   "users",
	Short: "View users",
	RunE: func(cmd *cobra.Command, args []string) error {
		user, err := dao.Queries.GetUserByUsername(context.Background(), viewUsername)
		if err != nil {
			return err
		}
		fmt.Printf("---\nID: %s\nUsername: %s\nCreated At: %s\n---\n", user.ID, user.Username, user.CreatedAt)
		return nil
	},
}

func init() {
	viewUsersCmd.Flags().StringVar(&viewUsername, "username", "", "select a user by username")
	viewUsersCmd.MarkFlagRequired("username")
	viewCmd.AddCommand(viewUsersCmd)
	rootCmd.AddCommand(viewCmd)
}
