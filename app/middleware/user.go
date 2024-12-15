package middleware

import (
	"context"
	"net/http"
)

type CurrentUserMiddleware struct{}

func (m CurrentUserMiddleware) New() CurrentUserMiddleware {
	return CurrentUserMiddleware{}
}

func (m *CurrentUserMiddleware) Handler(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		ctx := context.WithValue(r.Context(), "currentUsername", "anonymous")
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}
