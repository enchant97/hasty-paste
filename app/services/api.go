package services

import (
	"context"
	"database/sql"

	"github.com/enchant97/hasty-paste/app/core"
	"github.com/enchant97/hasty-paste/app/database"
	"github.com/enchant97/hasty-paste/app/middleware"
	"github.com/google/uuid"
)

type ApiService struct {
	dao *core.DAO
}

func (s ApiService) New(dao *core.DAO) ApiService {
	return ApiService{
		dao: dao,
	}
}

func (s *ApiService) NewQuickPaste(
	pasteForm core.NewPasteForm,
) (uuid.UUID, error) {
	// convert expiry time into SQL compatible
	var expiry sql.NullTime
	if pasteForm.Expiry != nil {
		if err := expiry.Scan(*pasteForm.Expiry); err != nil {
			return uuid.Nil, err
		}
	}
	// get user id
	user, err := s.dao.Queries.GetUserByUsername(context.Background(), middleware.AnonymousUsername)
	if err != nil {
		wrapDbErrorWithValue(uuid.Nil, err)
	}
	// create paste
	pasteID, err := s.dao.Queries.InsertPaste(context.Background(), database.InsertPasteParams{
		ID:            core.NewUUID(),
		OwnerID:       user.ID,
		Slug:          pasteForm.Slug,
		Content:       pasteForm.Content,
		ContentFormat: pasteForm.ContentFormat,
		Visibility:    pasteForm.Visibility,
		ExpiresAt:     expiry,
	})
	return wrapDbErrorWithValue(pasteID, err)
}
