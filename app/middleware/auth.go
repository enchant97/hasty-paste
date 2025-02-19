package middleware

import (
	"context"
	"net/http"
	"time"

	"github.com/enchant97/hasty-paste/app/core"
	"github.com/google/uuid"
)

const (
	AnonymousUsername         = "anonymous"
	ContextCurrentUsernameKey = "currentUsername"
	ContextCurrentUserIDKey   = "currentUserID"
	CookieAuthTokenName       = "AuthenticatedUser"
)

type AuthenticationProvider struct {
	secureMode  bool
	tokenSecret []byte
	dao         *core.DAO
}

func (m AuthenticationProvider) New(secureMode bool, tokenSecret []byte, dao *core.DAO) AuthenticationProvider {
	return AuthenticationProvider{secureMode: secureMode, tokenSecret: tokenSecret, dao: dao}
}

func (m *AuthenticationProvider) ProviderMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		currentUsername := AnonymousUsername
		cookie, err := r.Cookie(CookieAuthTokenName)
		if err == nil {
			if username, err := core.ParseAuthenticationToken(cookie.Value, m.tokenSecret); err != nil {
				// invalid authentication token
				m.ClearCookieAuthToken(w)
				http.Redirect(w, r, "/login", http.StatusTemporaryRedirect)
				return
			} else {
				currentUsername = username
			}
		}

		if user, err := m.dao.Queries.GetUserByUsername(context.Background(), currentUsername); err != nil {
			http.Error(w, "Internal Server Error", http.StatusInternalServerError)
			return
		} else {
			ctx := context.WithValue(r.Context(), ContextCurrentUsernameKey, currentUsername)
			ctx = context.WithValue(ctx, ContextCurrentUserIDKey, user.ID)
			next.ServeHTTP(w, r.WithContext(ctx))
		}
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

func (m *AuthenticationProvider) GetCurrentUserID(r *http.Request) uuid.UUID {
	return r.Context().Value(ContextCurrentUserIDKey).(uuid.UUID)
}

func (m *AuthenticationProvider) IsCurrentUserAnonymous(r *http.Request) bool {
	return m.GetCurrentUsername(r) == AnonymousUsername
}

func (m *AuthenticationProvider) SetCookieAuthToken(w http.ResponseWriter, token core.AuthenticationToken) {
	http.SetCookie(w, &http.Cookie{
		Name:     CookieAuthTokenName,
		Path:     "/",
		Value:    token.TokenContent,
		Expires:  token.ExpiresAt,
		HttpOnly: true,
		Secure:   m.secureMode,
	})
}

func (m *AuthenticationProvider) ClearCookieAuthToken(w http.ResponseWriter) {
	http.SetCookie(w, &http.Cookie{
		Name:     CookieAuthTokenName,
		Path:     "/",
		Value:    "",
		Expires:  time.Date(2000, 1, 1, 0, 0, 0, 0, time.UTC),
		HttpOnly: true,
		Secure:   m.secureMode,
	})
}
