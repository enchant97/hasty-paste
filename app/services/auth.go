package services

import (
	"context"
	"errors"

	"github.com/enchant97/hasty-paste/app/core"
	"github.com/enchant97/hasty-paste/app/database"
	"github.com/google/uuid"
)

type AuthService struct {
	dao *core.DAO
}

func (s AuthService) New(dao *core.DAO) AuthService {
	return AuthService{
		dao: dao,
	}
}

func (s *AuthService) CreateNewUser(form core.NewUserForm) (uuid.UUID, error) {
	id, err := s.dao.Queries.InsertUser(context.Background(), database.InsertUserParams{
		ID:           core.NewUUID(),
		Username:     form.Username,
		PasswordHash: core.HashPassword(form.Password),
	})
	return id, wrapDbError(err)
}

func (s *AuthService) CreateNewOIDCUser(username string, clientID string, userSub string) (uuid.UUID, error) {
	ctx := context.Background()
	tx, err := s.dao.DB.Begin()
	if err != nil {
		return uuid.Nil, wrapDbError(err)
	}
	q := s.dao.Queries.WithTx(tx)
	userID, err := q.InsertUser(ctx, database.InsertUserParams{
		ID:       core.NewUUID(),
		Username: username,
	})
	if err != nil {
		return uuid.Nil, wrapDbError(err)
	}
	if err := q.InsertOIDCUser(ctx, database.InsertOIDCUserParams{
		UserID:   userID,
		ClientID: clientID,
		UserSub:  userSub,
	}); err != nil {

		return uuid.Nil, wrapDbError(err)
	}
	return userID, wrapDbError(tx.Commit())
}

func (s *AuthService) CheckIfValidUser(form core.LoginUserForm) (bool, error) {
	user, err := s.dao.Queries.GetUserByUsername(context.Background(), form.Username)
	if err != nil {
		return false, wrapDbError(err)
	}
	return core.IsValidPassword(form.Password, user.PasswordHash), nil
}

func (s *AuthService) GetOIDCUser(oidcUser core.OIDCUser) (database.User, error) {
	return wrapDbErrorWithValue(s.dao.Queries.GetUserByOIDC(context.Background(), database.GetUserByOIDCParams{
		ClientID: oidcUser.ClientID,
		UserSub:  oidcUser.Subject,
	}))
}

func (s *AuthService) GetOrCreateOIDCUser(oidcUser core.OIDCUserWithUsername) (database.User, error) {
	user, err := s.GetOIDCUser(oidcUser.OIDCUser)
	if err != nil {
		if errors.Is(err, ErrNotFound) {
			userID, err := s.CreateNewOIDCUser(oidcUser.Username, oidcUser.ClientID, oidcUser.Subject)
			if err != nil {
				return database.User{}, err
			}
			return wrapDbErrorWithValue(s.dao.Queries.GetUserByID(context.Background(), userID))
		} else {
			return database.User{}, err
		}
	} else {
		return user, err
	}
}
