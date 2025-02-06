package services

import (
	"context"

	"github.com/enchant97/hasty-paste/app/core"
	"github.com/enchant97/hasty-paste/app/database"
)

type AuthService struct {
	dao *core.DAO
}

func (s AuthService) New(dao *core.DAO) AuthService {
	return AuthService{
		dao: dao,
	}
}

func (s *AuthService) CreateNewUser(form core.NewUserForm) (int64, error) {
	id, err := s.dao.Queries.InsertUser(context.Background(), database.InsertUserParams{
		Username:     form.Username,
		PasswordHash: core.HashPassword(form.Password),
	})
	return id, wrapDbError(err)
}

func (s *AuthService) CheckIfValidUser(form core.LoginUserForm) (bool, error) {
	user, err := s.dao.Queries.GetUserByUsername(context.Background(), form.Username)
	if err != nil {
		return false, wrapDbError(err)
	}
	return core.IsValidPassword(form.Password, user.PasswordHash), nil
}
