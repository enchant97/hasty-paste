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

    // Process all given attachments
	// TODO needs some error checking
	attachments := make([]core.NewPasteFormAttachment, len(r.MultipartForm.File["pasteAttachmentFile[]"]))
	for i, fileHeader := range r.MultipartForm.File["pasteAttachmentFile[]"] {
		attachment := core.NewPasteFormAttachment{
			Slug: strings.Trim(fileHeader.Filename, " "),
			Open: fileHeader.Open,
		}
		attachments[i] = attachment
	}

	pasteSlug := r.PostFormValue("pasteSlug")
	if pasteSlug == "" {
		pasteSlug = core.GenerateRandomSlug(10)
	}

	form := core.NewPasteForm{
		Slug:        strings.Trim(pasteSlug, " "),
		Attachments: attachments,
	}

	if err := h.validator.Struct(form); err != nil {
		http.Error(w, "Bad Request", http.StatusBadRequest)
		return
	}

	if err := h.service.NewPaste(0, form); err != nil {
		http.Error(w, "Internal Server Error", http.StatusInternalServerError)
		return
	}

    // TODO redirect to the created paste
	http.Redirect(w, r, "/pastes/new", http.StatusSeeOther)
}
