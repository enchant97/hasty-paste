package cmd

import (
	"context"
	"log"

	"github.com/google/uuid"
	"github.com/spf13/cobra"
)

var (
	cleanupExpiredEnabled bool
	cleanupDeletedEnabled bool
)

var cleanupCmd = &cobra.Command{
	Use:   "cleanup",
	Short: "Cleanup pastes",
	RunE: func(cmd *cobra.Command, args []string) error {
		if cleanupExpiredEnabled {
			if err := removeExpired(); err != nil {
				return err
			}
		}
		if cleanupDeletedEnabled {
			if err := removeDeleted(); err != nil {
				return err
			}
		}
		return nil
	},
}

func removeAttachments(pasteID uuid.UUID) (int, error) {
	attachmentIDs, err := dao.Queries.AdminGetAttachmentsByPasteId(context.Background(), pasteID)
	if err != nil {
		return 0, err
	}
	for _, attachmentID := range attachmentIDs {
		if err := sc.DeletePasteAttachment(attachmentID); err != nil {
			return 0, err
		}
		if err := dao.Queries.AdminDeleteAttachmentByID(context.Background(), attachmentID); err != nil {
			return 0, err
		}
	}
	return len(attachmentIDs), nil
}

func removeExpired() error {
	for {
		pasteIDs, err := dao.Queries.AdminGetExpiredPastesWithLimit(context.Background())
		if err != nil {
			return err
		} else if len(pasteIDs) == 0 {
			return nil
		}
		for _, pasteID := range pasteIDs {
			log.Printf("found expired paste: '%s'\n", pasteID)
			attachmentCount, err := removeAttachments(pasteID)
			if err != nil {
				return err
			}
			if err := dao.Queries.AdminDeletePasteByID(context.Background(), pasteID); err != nil {
				return err
			}
			log.Printf("removed expired paste: '%s' and %d attachments\n", pasteID, attachmentCount)
		}
	}
}

func removeDeleted() error {
	for {
		pasteIDs, err := dao.Queries.AdminGetDeletedPastesWithLimit(context.Background())
		if err != nil {
			return err
		} else if len(pasteIDs) == 0 {
			return nil
		}
		for _, pasteID := range pasteIDs {
			log.Printf("found user deleted paste: '%s'\n", pasteID)
			attachmentCount, err := removeAttachments(pasteID)
			if err != nil {
				return err
			}
			if err := dao.Queries.AdminDeletePasteByID(context.Background(), pasteID); err != nil {
				return err
			}
			log.Printf("removed user deleted paste: '%s' and %d attachments\n", pasteID, attachmentCount)
		}
	}
}

func init() {
	cleanupCmd.Flags().BoolVar(&cleanupExpiredEnabled, "expired", false, "Enable cleanup for expired pastes")
	cleanupCmd.Flags().BoolVar(&cleanupDeletedEnabled, "deleted", false, "Enable cleanup for user deleted pastes")
	rootCmd.AddCommand(cleanupCmd)
}
