package core

import (
	"errors"
	"log"
	"time"

	"github.com/golang-jwt/jwt/v5"
	"golang.org/x/crypto/bcrypt"
)

var (
	JWTClaimsNotValidError  = errors.New("invalid jwt claims")
	DefaultJwtSigningMethod = jwt.SigningMethodHS256
)

type AuthenticationToken struct {
	TokenContent string
	ExpiresAt    time.Time
}

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
		return false
	}
	return true
}

func CreateAuthenticationToken(username string, secretKey []byte, durationUntilExpiry time.Duration) (AuthenticationToken, error) {
	expiresAt := time.Now().Add(durationUntilExpiry)
	token := jwt.NewWithClaims(DefaultJwtSigningMethod, jwt.RegisteredClaims{
		Subject:   username,
		ExpiresAt: jwt.NewNumericDate(expiresAt),
		IssuedAt:  jwt.NewNumericDate(time.Now()),
		NotBefore: jwt.NewNumericDate(time.Now()),
	})
	tokenContent, err := token.SignedString(secretKey)
	return AuthenticationToken{
		TokenContent: tokenContent,
		ExpiresAt:    expiresAt,
	}, err
}

func ParseAuthenticationToken(token string, secretKey []byte) (string, error) {
	if token, err := jwt.ParseWithClaims(token, &jwt.RegisteredClaims{}, func(t *jwt.Token) (interface{}, error) {
		return secretKey, nil
	},
		jwt.WithValidMethods([]string{DefaultJwtSigningMethod.Alg()}),
		jwt.WithExpirationRequired(),
		jwt.WithIssuedAt(),
		jwt.WithLeeway(3*time.Minute),
	); err != nil {
		return "", err
	} else {
		if claims, ok := token.Claims.(*jwt.RegisteredClaims); !ok {
			return "", JWTClaimsNotValidError
		} else {
			return claims.Subject, nil
		}
	}
}
