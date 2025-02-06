package services

import (
	"database/sql"
	"errors"

	"modernc.org/sqlite"
	sqlite3 "modernc.org/sqlite/lib"
)

var ErrNotFound = errors.New("resource not found")
var ErrConflict = errors.New("resource conflict")

// / wrap a database error with a specific service error
func wrapDbError(err error) error {
	if errors.Is(err, sql.ErrNoRows) {
		return errors.Join(err, ErrNotFound)
	} else if err, ok := err.(*sqlite.Error); ok {
		switch err.Code() {
		case sqlite3.SQLITE_CONSTRAINT_UNIQUE:
			return errors.Join(err, ErrConflict)
		}
	}
	return err
}
