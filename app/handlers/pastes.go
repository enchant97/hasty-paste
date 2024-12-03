package handlers

import (
	"net/http"

	"github.com/a-h/templ"
	"github.com/enchant97/hasty-paste/app/components"
	"github.com/enchant97/hasty-paste/app/database"
	"github.com/enchant97/hasty-paste/app/services"
	"github.com/enchant97/hasty-paste/app/storage"
	"github.com/go-chi/chi/v5"
)

type PastesHandler struct {
	service services.PastesService
}

func (h PastesHandler) Setup(r *chi.Mux, dao *database.Queries, sc *storage.StorageController) {
	h = PastesHandler{
		services.PastesService{}.New(dao, sc),
	}
	r.Get("/pastes/new", h.GetNewPastePage)
	r.Post("/pastes/new/_post", h.PostNewPastePage)
}

func (h *PastesHandler) GetNewPastePage(w http.ResponseWriter, r *http.Request) {
	templ.Handler(components.NewPastePage()).ServeHTTP(w, r)
}

func (h *PastesHandler) PostNewPastePage(w http.ResponseWriter, r *http.Request) {
	if err := r.ParseMultipartForm(1048576); err != nil {
		http.Error(w, "Bad Request", http.StatusBadRequest)
		return
	}
	http.Redirect(w, r, "/pastes/new", http.StatusSeeOther)
}
