package services

import (
	"github.com/enchant97/hasty-paste/app/database"
	"github.com/enchant97/hasty-paste/app/storage"
)

type PastesService struct {
	dao *database.Queries
	sc  *storage.StorageController
}

func (s PastesService) New(dao *database.Queries, sc *storage.StorageController) PastesService {
	return PastesService{
		dao: dao,
		sc:  sc,
	}
}
