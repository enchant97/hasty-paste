package cmd

import (
	"context"
	"log"
	"time"

	"github.com/enchant97/hasty-paste/app/database"
	"github.com/google/uuid"
	"github.com/spf13/cobra"
)

var (
	cleanupCreatedBefore time.Time
	cleanupCreatedAfter  time.Time
	cleanupUserID        string
)

var removeCmd = &cobra.Command{
	Use:   "remove",
	Short: "Remove entries",
}

var removePastesCmd = &cobra.Command{
	Use:   "pastes",
	Short: "Remove pastes",
}

var removePastesByIdCmd = &cobra.Command{
	Use:                   "id [paste ids]",
	Short:                 "Remove pastes by ids",
	Args:                  cobra.MinimumNArgs(1),
	DisableFlagsInUseLine: true,
	RunE: func(cmd *cobra.Command, args []string) error {
		for _, arg := range args {
			pasteID, err := uuid.Parse(arg)
			if err != nil {
				return err
			}
			attachmentIDs, err := dao.Queries.AdminGetAttachmentsByPasteId(context.Background(), pasteID)
			if err != nil {
				return err
			}
			for _, attachmentID := range attachmentIDs {
				if err := sc.DeletePasteAttachment(attachmentID); err != nil {
					return err
				}
				if err := dao.Queries.AdminDeleteAttachmentByID(context.Background(), attachmentID); err != nil {
					return err
				}
			}
			if err := dao.Queries.AdminDeletePasteByID(context.Background(), pasteID); err != nil {
				return err
			}
			log.Printf("removed paste: '%s' and %d attachments\n", pasteID, len(attachmentIDs))
		}
		return nil
	},
}

var removePastesInRangeCmd = &cobra.Command{
	Use:   "range",
	Short: "Remove pastes in provided range",
	RunE: func(cmd *cobra.Command, args []string) error {
		var userID *uuid.UUID = nil
		if cleanupUserID != "" {
			id, err := uuid.Parse(cleanupUserID)
			if err != nil {
				return err
			}
			userID = &id
		}
		for {
			pasteIDs, err := dao.Queries.AdminGetPastesInDateRangeWithLimit(
				context.Background(),
				database.AdminGetPastesInDateRangeWithLimitParams{
					Before: cleanupCreatedBefore,
					After:  cleanupCreatedAfter,
					UserID: userID,
				})
			if err != nil {
				return err
			} else if len(pasteIDs) == 0 {
				return nil
			}
			for _, pasteID := range pasteIDs {
				log.Printf("found paste: '%s'\n", pasteID)
				attachmentIDs, err := dao.Queries.AdminGetAttachmentsByPasteId(context.Background(), pasteID)
				if err != nil {
					return err
				}
				for _, attachmentID := range attachmentIDs {
					if err := sc.DeletePasteAttachment(attachmentID); err != nil {
						return err
					}
					if err := dao.Queries.AdminDeleteAttachmentByID(context.Background(), attachmentID); err != nil {
						return err
					}
				}
				if err := dao.Queries.AdminDeletePasteByID(context.Background(), pasteID); err != nil {
					return err
				}
				log.Printf("removed paste: '%s' and %d attachments\n", pasteID, len(attachmentIDs))
			}
		}
	},
}

func init() {
	removePastesInRangeCmd.Flags().TimeVar(
		&cleanupCreatedBefore,
		"created-before",
		time.Time{},
		[]string{time.RFC3339},
		"Remove pastes created before the given date",
	)
	removePastesInRangeCmd.Flags().TimeVar(
		&cleanupCreatedAfter,
		"created-after",
		time.Time{},
		[]string{time.RFC3339},
		"Remove pastes created after the given date",
	)
	removePastesInRangeCmd.Flags().StringVar(&cleanupUserID, "user-id", "", "filter by given user id")
	removePastesInRangeCmd.MarkFlagsOneRequired("created-before", "created-after")
	removePastesInRangeCmd.MarkFlagsRequiredTogether("created-before", "created-after")
	removePastesCmd.AddCommand(removePastesByIdCmd)
	removePastesCmd.AddCommand(removePastesInRangeCmd)
	removeCmd.AddCommand(removePastesCmd)
	rootCmd.AddCommand(removeCmd)
}
