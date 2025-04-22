package services

import "github.com/enchant97/hasty-paste/app/core"

type AuxService struct {
	dao *core.DAO
}

func (s AuxService) New(dao *core.DAO) AuxService {
	return AuxService{
		dao: dao,
	}
}

func (s *AuxService) IsHealthy() bool {
	return s.dao.DB.Ping() == nil
}
