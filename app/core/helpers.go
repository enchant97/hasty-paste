package core

import (
	"crypto/rand"
	"math/big"
	"strings"
)

const RandomSlugCharacters = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

func GenerateRandomSlug(n int) string {
	var out strings.Builder
	maxIndex := big.NewInt(int64(len(RandomSlugCharacters)))
	for i := 0; i < n; i++ {
		charIndex, _ := rand.Int(rand.Reader, maxIndex)
		char := RandomSlugCharacters[charIndex.Int64()]
		out.Grow(1)
		out.WriteByte(char)
	}
	return out.String()
}
