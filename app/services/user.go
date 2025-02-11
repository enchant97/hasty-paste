package services

import (
	"context"
	"io"

	"github.com/enchant97/hasty-paste/app/core"
	"github.com/enchant97/hasty-paste/app/database"
	"github.com/enchant97/hasty-paste/app/storage"
)

type UserService struct {
	dao *core.DAO
	sc  *storage.StorageController
}

func (s UserService) New(dao *core.DAO, sc *storage.StorageController) UserService {
	return UserService{
		dao: dao,
		sc:  sc,
	}
}

func (s *UserService) GetPastes(currentUserID int64, username string) ([]database.GetLatestPastesByUserRow, error) {
	return wrapDbErrorWithValue(s.dao.Queries.GetLatestPastesByUser(context.Background(), database.GetLatestPastesByUserParams{
		Username:      username,
		CurrentUserID: currentUserID,
	}))
}

func (s *UserService) GetPaste(currentUserID int64, username string, slug string) (database.Paste, error) {
	return wrapDbErrorWithValue(s.dao.Queries.GetPasteBySlug(context.Background(), database.GetPasteBySlugParams{
		CurrentUserID: currentUserID,
		Username:      username,
		PasteSlug:     slug,
	}))
}

func (s *UserService) GetPasteAttachments(pasteId int64) ([]database.Attachment, error) {
	return wrapDbErrorWithValue(s.dao.Queries.GetAttachmentsByPasteID(context.Background(), pasteId))
}

func (s *UserService) GetPasteAttachment(
	currentUserID int64,
	username string,
	pasteSlug string,
	attachmentSlug string,
) (database.Attachment, io.ReadCloser, error) {
	attachment, err := s.dao.Queries.GetAttachmentBySlug(context.Background(), database.GetAttachmentBySlugParams{
		CurrentUserID:  currentUserID,
		Username:       username,
		PasteSlug:      pasteSlug,
		AttachmentSlug: attachmentSlug,
	})
	if err != nil {
		return database.Attachment{}, nil, wrapDbError(err)
	}
	attachmentReader, err := s.sc.ReadPasteAttachment(attachment.ID)
	return attachment, attachmentReader, wrapDbError(err)
}
