package middleware

import (
	"context"
	"net/http"
	"time"

	"github.com/enchant97/hasty-paste/app/core"
)

const (
	AnonymousUsername         = "anonymous"
	ContextCurrentUsernameKey = "currentUsername"
	CookieAuthTokenName       = "AuthenticatedUser"
)

type AuthenticationProvider struct {
	tokenSecret []byte
}

func (m AuthenticationProvider) New(tokenSecret []byte) AuthenticationProvider {
	return AuthenticationProvider{tokenSecret: tokenSecret}
}

func (m *AuthenticationProvider) ProviderMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		currentUser := AnonymousUsername
		cookie, err := r.Cookie(CookieAuthTokenName)
		if err == nil {
			if username, err := core.ParseAuthenticationToken(cookie.Value, m.tokenSecret); err != nil {
				m.ClearCookieAuthToken(w)
				http.Redirect(w, r, "/login", http.StatusTemporaryRedirect)
				return
			} else {
				currentUser = username
			}
		}
		ctx := context.WithValue(r.Context(), ContextCurrentUsernameKey, currentUser)
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

func (m *AuthenticationProvider) RequireAuthenticationMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Context().Value(ContextCurrentUsernameKey) == AnonymousUsername {
			http.Redirect(w, r, "/login", http.StatusTemporaryRedirect)
			return
		}
		next.ServeHTTP(w, r)
	})
}

func (m *AuthenticationProvider) RequireNoAuthenticationMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Context().Value(ContextCurrentUsernameKey) != AnonymousUsername {
			http.Redirect(w, r, "/", http.StatusTemporaryRedirect)
			return
		}
		next.ServeHTTP(w, r)
	})
}

func (m *AuthenticationProvider) GetCurrentUsername(r *http.Request) string {
	return r.Context().Value(ContextCurrentUsernameKey).(string)
}

func (m *AuthenticationProvider) SetCookieAuthToken(w http.ResponseWriter, token core.AuthenticationToken) {
	http.SetCookie(w, &http.Cookie{
		Name:     CookieAuthTokenName,
		Path:     "/",
		Value:    token.TokenContent,
		Expires:  token.ExpiresAt,
		HttpOnly: true,
		SameSite: http.SameSiteStrictMode,
		// TODO Add Secure (if running under server https)
	})
}

func (m *AuthenticationProvider) ClearCookieAuthToken(w http.ResponseWriter) {
	http.SetCookie(w, &http.Cookie{
		Name:     CookieAuthTokenName,
		Path:     "/",
		Value:    "",
		Expires:  time.Date(2000, 1, 1, 0, 0, 0, 0, time.UTC),
		HttpOnly: true,
		SameSite: http.SameSiteStrictMode,
		// TODO Add Secure (if running under server https)
	})
}
