package cmd

import (
	"context"
	"log"

	"github.com/spf13/cobra"
)

var (
	cleanupExpiredEnabled bool
)

var cleanupCmd = &cobra.Command{
	Use:   "cleanup",
	Short: "Cleanup pastes",
	RunE: func(cmd *cobra.Command, args []string) error {
		if cleanupExpiredEnabled {
			return removeExpired()
		}
		log.Println("No cleanup flags provided, nothing enabled")
		return nil
	},
}

func removeExpired() error {
	for {
		pasteIDs, err := dao.Queries.GetExpiredPastesWithLimit(context.Background())
		if err != nil {
			return err
		} else if len(pasteIDs) == 0 {
			return nil
		}
		for _, pasteID := range pasteIDs {
			log.Printf("found expired paste: '%s'\n", pasteID)
			attachmentIDs, err := dao.Queries.GetAttachmentsByPasteIdNoExpiryCheck(context.Background(), pasteID)
			if err != nil {
				return err
			}
			for _, attachmentID := range attachmentIDs {
				if err := sc.DeletePasteAttachment(attachmentID); err != nil {
					return err
				}
				if err := dao.Queries.DeleteAttachmentByID(context.Background(), attachmentID); err != nil {
					return err
				}
			}
			if err := dao.Queries.DeletePasteByID(context.Background(), pasteID); err != nil {
				return err
			}
			log.Printf("removed expired paste: '%s' and %d attachments\n", pasteID, len(attachmentIDs))
		}
	}
}

func init() {
	cleanupCmd.Flags().BoolVar(&cleanupExpiredEnabled, "expired", false, "Enable cleanup for expired pastes")
	rootCmd.AddCommand(cleanupCmd)
}
