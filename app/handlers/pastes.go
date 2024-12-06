package handlers

import (
	"net/http"
	"strings"

	"github.com/a-h/templ"
	"github.com/enchant97/hasty-paste/app/components"
	"github.com/enchant97/hasty-paste/app/core"
	"github.com/enchant97/hasty-paste/app/services"
	"github.com/go-chi/chi/v5"
	"github.com/go-playground/validator/v10"
)

type PastesHandler struct {
	validator *validator.Validate
	service   services.PastesService
}

func (h PastesHandler) Setup(
	r *chi.Mux,
	service services.PastesService,
	v *validator.Validate,
) {
	h = PastesHandler{
		validator: v,
		service:   service,
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

	attachmentReader, attachmentHeader, err := r.FormFile("pasteAttachmentFile")
	if err != nil {
		http.Error(w, "Bad Request", http.StatusBadRequest)
		return
	}
	defer attachmentReader.Close()

	pasteSlug := r.PostFormValue("pasteSlug")
	if pasteSlug == "" {
		pasteSlug = core.GenerateRandomSlug(10)
	}
	form := core.NewPasteForm{
		Slug:             strings.Trim(pasteSlug, " "),
		AttachmentSlug:   strings.Trim(attachmentHeader.Filename, " "),
		AttachmentReader: attachmentReader,
	}

	if err := h.validator.Struct(form); err != nil {
		http.Error(w, "Bad Request", http.StatusBadRequest)
		return
	}

	if err := h.service.NewPaste(0, form); err != nil {
		http.Error(w, "Internal Server Error", http.StatusInternalServerError)
		return
	}

	http.Redirect(w, r, "/pastes/new", http.StatusSeeOther)
}
