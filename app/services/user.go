package services

import (
	"context"
	"io"
	"strconv"

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

func (s *UserService) GetPastes(username string) ([]database.Paste, error) {
	return s.dao.Queries.GetLatestPastesByUser(context.Background(), username)
}

func (s *UserService) GetPaste(username string, slug string) (database.Paste, error) {
	return s.dao.Queries.GetPasteBySlug(context.Background(), database.GetPasteBySlugParams{
		Username: username,
		Slug:     slug,
	})
}

func (s *UserService) GetPasteAttachments(pasteId int64) ([]database.Attachment, error) {
	return s.dao.Queries.GetAttachmentsByPasteId(context.Background(), pasteId)
}

func (s *UserService) GetPasteAttachment(
	username string,
	pasteSlug string,
	attachmentSlug string,
) (database.Attachment, io.ReadCloser, error) {
	attachment, err := s.dao.Queries.GetAttachmentBySlug(context.Background(), database.GetAttachmentBySlugParams{
		Username:       username,
		PasteSlug:      pasteSlug,
		AttachmentSlug: attachmentSlug,
	})
	if err != nil {
		return database.Attachment{}, nil, err
	}
	attachmentReader, err := s.sc.ReadPasteAttachment(strconv.Itoa(int(attachment.ID)))
	return attachment, attachmentReader, err
}
