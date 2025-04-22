package handlers

import (
	"net/http"

	"github.com/enchant97/hasty-paste/app/services"
	"github.com/go-chi/chi/v5"
)

type AuxHandler struct {
	service services.AuxService
}

func (h AuxHandler) Setup(
	r *chi.Mux,
	service services.AuxService,
) {
	h = AuxHandler{
		service: service,
	}
	r.Get("/_/is-healthy", h.GetHealthCheck)
}

func (h *AuxHandler) GetHealthCheck(w http.ResponseWriter, r *http.Request) {
	if h.service.IsHealthy() {
		w.WriteHeader(http.StatusNoContent)
	} else {
		w.WriteHeader(http.StatusInternalServerError)
	}
}
