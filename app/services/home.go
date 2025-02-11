package services

import (
	"context"
	"database/sql"

	"github.com/enchant97/hasty-paste/app/core"
	"github.com/enchant97/hasty-paste/app/database"
	"github.com/enchant97/hasty-paste/app/storage"
	"github.com/google/uuid"
)

type HomeService struct {
	dao *core.DAO
	sc  *storage.StorageController
}

func (s HomeService) New(dao *core.DAO, sc *storage.StorageController) HomeService {
	return HomeService{
		dao: dao,
		sc:  sc,
	}
}

func (s *HomeService) GetLatestPublicPastes() ([]database.GetLatestPublicPastesRow, error) {
	return wrapDbErrorWithValue(s.dao.Queries.GetLatestPublicPastes(context.Background(), 5))
}

func (s *HomeService) NewPaste(ownerID int64, pasteForm core.NewPasteForm) error {
	ctx := context.Background()
	tx, err := s.dao.DB.Begin()
	if err != nil {
		return err
	}
	defer tx.Rollback()

	var expiry sql.NullTime
	if pasteForm.Expiry != nil {
		if err := expiry.Scan(*pasteForm.Expiry); err != nil {
			return err
		}
	}

	dbQueries := s.dao.Queries.WithTx(tx)
	pasteID, err := dbQueries.InsertPaste(ctx, database.InsertPasteParams{
		OwnerID:       ownerID,
		Slug:          pasteForm.Slug,
		Content:       pasteForm.Content,
		ContentFormat: pasteForm.ContentFormat,
		Visibility:    pasteForm.Visibility,
		ExpiresAt:     expiry,
	})
	if err != nil {
		return wrapDbError(err)
	}

	// Process each attachment one by one (maybe make it do parallel in future?)
	for _, attachment := range pasteForm.Attachments {
		if err := func() error {
			r, err := attachment.Open()
			if err != nil {
				return err
			}
			defer r.Close()
			checksum, err := core.MakeChecksum(r)
			if err != nil {
				return err
			}
			r.Seek(0, 0)
			attachmentID, err := dbQueries.InsertPasteAttachment(ctx, database.InsertPasteAttachmentParams{
				ID: func() uuid.UUID {
					id, err := uuid.NewV7()
					if err != nil {
						panic(err)
					}
					return id
				}(),
				PasteID:  pasteID,
				Slug:     attachment.Slug,
				MimeType: attachment.Type,
				Size:     attachment.Size,
				Checksum: checksum,
			})
			if err != nil {
				return err
			}
			if err := s.sc.WritePasteAttachment(attachmentID, r); err != nil {
				return err
			}
			return nil
		}(); err != nil {
			return err
		}
	}

	return wrapDbError(tx.Commit())
}
