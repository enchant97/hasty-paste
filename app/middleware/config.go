package middleware

import (
	"context"
	"net/http"

	"github.com/enchant97/hasty-paste/app/core"
)

const (
	ContextConfigKey = "appConfig"
)

type AppConfigProvider struct {
	config core.AppConfig
}

func (m AppConfigProvider) New(config core.AppConfig) AppConfigProvider {
	return AppConfigProvider{
		config: config,
	}
}

func (m *AppConfigProvider) ProviderMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		ctx := context.WithValue(r.Context(), ContextConfigKey, m.config)
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

func GetAppConfig(ctx context.Context) core.AppConfig {
	return ctx.Value(ContextConfigKey).(core.AppConfig)
}
