package middleware

import (
	"context"
	"encoding/json"
	"log"
	"net/http"
	"os"
	"strings"

	"github.com/enchant97/hasty-paste/app/core"
	"github.com/go-chi/chi/v5"
)

const ContextViteHeadKey = "viteHead"

type ViteManifestSection struct {
	File string   `json:"file"`
	Css  []string `json:"css"`
}

type ViteProvider struct {
	devConfig core.DevConfig
	scripts   []string
	css       []string
}

func (m ViteProvider) New(devConfig core.DevConfig) ViteProvider {
	scriptFiles := make([]string, 0)
	cssFiles := make([]string, 0)
	if !devConfig.Enabled {
		rawContent, err := os.ReadFile("dist/.vite/manifest.json")
		if err != nil {
			log.Fatalln("vite manifest could not be found")
		}
		var viteManifest map[string]ViteManifestSection
		if err := json.Unmarshal(rawContent, &viteManifest); err != nil {
			log.Fatalln("vite manifest could not be loaded")
		}
		for _, section := range viteManifest {
			scriptFiles = append(scriptFiles, section.File)
			cssFiles = append(cssFiles, section.Css...)
		}

	}
	return ViteProvider{devConfig: devConfig, scripts: scriptFiles, css: cssFiles}
}

func (m *ViteProvider) ProviderMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		var ctx context.Context
		if m.devConfig.Enabled {
			ctx = context.WithValue(r.Context(), ContextViteHeadKey,
				`<script type="module" src="http://`+m.devConfig.ViteDevHost+`/@vite/client"></script>
            <script type="module" src="http://`+m.devConfig.ViteDevHost+`/main.js"></script>`)
		} else {
			builder := strings.Builder{}
			for _, cssFile := range m.css {
				builder.WriteString(`<link rel="stylesheet" href="/` + cssFile + `">`)
			}
			for _, scriptFile := range m.scripts {
				builder.WriteString(`<script type="module" src="/` + scriptFile + `"></script>`)
			}
			ctx = context.WithValue(r.Context(), ContextViteHeadKey, builder.String())
		}
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

func (m *ViteProvider) SetupHandlers(r *chi.Mux) {
	fs := http.FileServer(http.Dir(m.devConfig.ViteDistPath))
	r.Handle("/assets/*", http.StripPrefix("/assets/", fs))
}
