package services

import (
	"context"

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
