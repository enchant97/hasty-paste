package core

import (
	"database/sql"

	"github.com/enchant97/hasty-paste/app/database"
)

type DAO struct {
	DB      *sql.DB
	Queries *database.Queries
}

func (dao DAO) New(db *sql.DB, queries *database.Queries) DAO {
	return DAO{
		DB:      db,
		Queries: queries,
	}
}
