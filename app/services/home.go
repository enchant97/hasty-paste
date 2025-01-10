package services

import (
	"context"
	"strconv"

	"github.com/enchant97/hasty-paste/app/core"
	"github.com/enchant97/hasty-paste/app/database"
	"github.com/enchant97/hasty-paste/app/storage"
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

func (s *HomeService) GetLatestPastes() ([]database.GetLatestPastesRow, error) {
	return s.dao.Queries.GetLatestPastes(context.Background(), 5)
}

func (s *HomeService) NewPaste(ownerID int64, pasteForm core.NewPasteForm) error {
	ctx := context.Background()
	tx, err := s.dao.DB.Begin()
	if err != nil {
		return err
	}
	defer tx.Rollback()

	dbQueries := s.dao.Queries.WithTx(tx)
	pasteID, err := dbQueries.InsertPaste(ctx, database.InsertPasteParams{
		OwnerID: ownerID,
		Slug:    pasteForm.Slug,
		Content: pasteForm.Content,
	})
	if err != nil {
		return err
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
				PasteID:  pasteID,
				Slug:     attachment.Slug,
				MimeType: attachment.Type,
				Size:     attachment.Size,
				Checksum: checksum,
			})
			if err != nil {
				return err
			}
			if err := s.sc.WritePasteAttachment(strconv.Itoa(int(attachmentID)), r); err != nil {
				return err
			}
			return nil
		}(); err != nil {
			return err
		}
	}

	return tx.Commit()
}
