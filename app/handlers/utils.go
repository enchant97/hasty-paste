package handlers

import (
	"crypto/rand"
	"crypto/subtle"
	"fmt"
	"log"
	"net/http"

	"github.com/a-h/templ"
	"github.com/enchant97/hasty-paste/app/components"
)

func InternalErrorResponse(w http.ResponseWriter, err error) {
	log.Println(err)
	http.Error(w, "Internal Server Error", http.StatusInternalServerError)
}

func NotFoundErrorResponse(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusNotFound)
	templ.Handler(components.NotFoundPage()).ServeHTTP(w, r)
}

func GenerateCSRFToken(w http.ResponseWriter, secure bool) string {
	token := rand.Text()
	http.SetCookie(w, &http.Cookie{
		Name:     "CsrfToken",
		Value:    token,
		Path:     "/",
		MaxAge:   0,
		Secure:   secure,
		HttpOnly: true,
		SameSite: http.SameSiteLaxMode,
	})
	return token
}

func ConsumeCSRFToken(
	w http.ResponseWriter,
	r *http.Request,
	expectedToken string,
	secure bool,
) error {
	tokenCookie, err := r.Cookie("CsrfToken")
	if err != nil {
		return err
	}
	http.SetCookie(w, &http.Cookie{
		Name:     "CsrfToken",
		Value:    "",
		Path:     "/",
		MaxAge:   -1,
		HttpOnly: true,
		Secure:   secure,
		SameSite: http.SameSiteLaxMode,
	})
	if subtle.ConstantTimeCompare([]byte(expectedToken), []byte(tokenCookie.Value)) == 1 {
		return nil
	}
	return fmt.Errorf("invalid csrf token")
}
