package services

import (
	"context"
	"strconv"

	"github.com/enchant97/hasty-paste/app/core"
	"github.com/enchant97/hasty-paste/app/database"
	"github.com/enchant97/hasty-paste/app/storage"
)

type PastesService struct {
	dao *core.DAO
	sc  *storage.StorageController
}

func (s PastesService) New(dao *core.DAO, sc *storage.StorageController) PastesService {
	return PastesService{
		dao: dao,
		sc:  sc,
	}
}

func (s *PastesService) NewPaste(ownerID int64, pasteForm core.NewPasteForm) error {
	ctx := context.Background()
	tx, err := s.dao.DB.Begin()
	if err != nil {
		return err
	}
	defer tx.Rollback()

	dbQueries := s.dao.Queries.WithTx(tx)
	pasteID, err := dbQueries.InsertPaste(ctx, database.InsertPasteParams{
		Ownerid: ownerID,
		Slug:    pasteForm.Slug,
	})
	if err != nil {
		return err
	}
	attachmentID, err := dbQueries.InsertPasteAttachment(ctx, database.InsertPasteAttachmentParams{
		Pasteid: pasteID,
		Slug:    pasteForm.AttachmentSlug,
	})
	if err != nil {
		return err
	}

	if err := s.sc.WritePasteAttachment(strconv.Itoa(int(attachmentID)), pasteForm.AttachmentReader); err != nil {
		return err
	}
	return tx.Commit()
}
