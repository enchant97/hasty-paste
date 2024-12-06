package handlers

import (
	"net/http"

	"github.com/a-h/templ"
	"github.com/enchant97/hasty-paste/app/components"
	"github.com/enchant97/hasty-paste/app/services"
	"github.com/go-chi/chi/v5"
	"github.com/go-playground/validator/v10"
)

type HomeHandler struct {
	validator *validator.Validate
	service   services.HomeService
}

func (h HomeHandler) Setup(
	r *chi.Mux,
	service services.HomeService,
	v *validator.Validate,
) {
	h = HomeHandler{
		validator: v,
		service:   service,
	}
	r.Get("/", h.GetHomePage)
}

func (h *HomeHandler) GetHomePage(w http.ResponseWriter, r *http.Request) {
	if latestPastes, err := h.service.GetLatestPastes(); err != nil {
		http.Error(w, "Internal Server Error", http.StatusInternalServerError)
	} else {
		templ.Handler(components.IndexPage(latestPastes)).ServeHTTP(w, r)
	}
}
