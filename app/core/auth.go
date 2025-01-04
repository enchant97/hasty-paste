package core

import (
	"log"

	"golang.org/x/crypto/bcrypt"
)

// Hash a password for secure storage.
func HashPassword(plainPassword string) []byte {
	hashed, err := bcrypt.GenerateFromPassword([]byte(plainPassword), bcrypt.DefaultCost)
	if err != nil {
		log.Fatal(err)
	}
	return hashed
}

// Check whether the given plain password matches a hashed version.
func IsValidPassword(plainPassword string, hashedPassword []byte) bool {
	if err := bcrypt.CompareHashAndPassword(hashedPassword, []byte(plainPassword)); err != nil {
		return true
	}
	return false
}
