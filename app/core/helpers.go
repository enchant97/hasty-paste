package core

import (
	"crypto/rand"
	"fmt"
	"hash/crc32"
	"io"
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

func MakeChecksum(r io.Reader) (string, error) {
	h := crc32.New(crc32.MakeTable(crc32.IEEE))
	buf := make([]byte, 1024)
	for {
		n, err := r.Read(buf)
		if err != nil && err != io.EOF {
			return "", err
		}
		if n == 0 {
			break
		}
		if _, err := h.Write(buf); err != nil {
			return "", err
		}
	}
	return fmt.Sprintf("crc32-%x", h.Sum32()), nil
}
