package middleware

import (
	"context"
	"encoding/gob"
	"log"
	"net/http"

	"github.com/gorilla/sessions"
)

type FlashType string

const (
	ContextSessionKey        = "session"
	ContextSessionFlashesKey = "flashes"
	FlashTypeOk              = "ok"
	FlashTypeError           = "error"
)

type Flash struct {
	Type    FlashType
	Message string
}

type SessionProvider struct {
	store sessions.Store
}

func (m SessionProvider) New(sessionSecret []byte) SessionProvider {
	gob.Register(Flash{})
	store := sessions.NewCookieStore(sessionSecret)
	store.Options.Secure = false // TODO Add Secure (if running under server https)
	store.Options.SameSite = http.SameSiteDefaultMode
	store.Options.HttpOnly = true
	return SessionProvider{store: store}
}

func (m *SessionProvider) ProviderMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		s := m.GetSession(r)
		ctx := context.WithValue(r.Context(), ContextSessionKey, s)
		ctx = context.WithValue(r.Context(), ContextSessionFlashesKey, s.Flashes())
		if err := s.Save(r, w); err != nil {
			log.Println(err)
			http.Error(w, "Internal Server Error", http.StatusInternalServerError)
			return
		}
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

func (m *SessionProvider) GetSession(r *http.Request) *sessions.Session {
	s, _ := m.store.Get(r, "session")
	return s
}

func CreateOkFlash(message string) Flash {
	return Flash{
		Type:    FlashTypeOk,
		Message: message,
	}
}

func CreateErrorFlash(message string) Flash {
	return Flash{
		Type:    FlashTypeError,
		Message: message,
	}
}

func GetFlashes(ctx context.Context) []Flash {
	rawValues := ctx.Value(ContextSessionFlashesKey).([]interface{})
	f := make([]Flash, len(rawValues))
	for i, v := range rawValues {
		f[i] = v.(Flash)
	}
	return f
}
