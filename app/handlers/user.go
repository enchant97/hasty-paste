package handlers

import (
	"io"
	"net/http"

	"github.com/a-h/templ"
	"github.com/enchant97/hasty-paste/app/components"
	"github.com/enchant97/hasty-paste/app/middleware"
	"github.com/enchant97/hasty-paste/app/services"
	"github.com/go-chi/chi/v5"
	"github.com/go-playground/validator/v10"
)

type UserHandler struct {
	service      services.UserService
	validator    *validator.Validate
	authProvider *middleware.AuthenticationProvider
}

func (h UserHandler) Setup(
	r *chi.Mux,
	service services.UserService,
	v *validator.Validate,
	ap *middleware.AuthenticationProvider,
) {
	h = UserHandler{
		service:      service,
		validator:    v,
		authProvider: ap,
	}
	r.Get("/@/{username}", h.GetPastes)
	r.Get("/@/{username}/{pasteSlug}", h.GetPaste)
	r.Get("/@/{username}/{pasteSlug}/{attachmentSlug}", h.GetPasteAttachment)
}

func (h *UserHandler) GetPastes(w http.ResponseWriter, r *http.Request) {
	username := r.PathValue("username")
	if pastes, err := h.service.GetPastes(h.authProvider.GetCurrentUserID(r), username); err != nil {
		http.Error(w, "Internal Server Error", http.StatusInternalServerError)
	} else {
		templ.Handler(components.PastesPage(username, pastes)).ServeHTTP(w, r)
	}
}

func (h *UserHandler) GetPaste(w http.ResponseWriter, r *http.Request) {
	username := r.PathValue("username")
	pasteSlug := r.PathValue("pasteSlug")
	paste, err := h.service.GetPaste(h.authProvider.GetCurrentUserID(r), username, pasteSlug)
	if err != nil {
		http.Error(w, "Internal Server Error", http.StatusInternalServerError)
		return
	}
	attachments, err := h.service.GetPasteAttachments(paste.ID)
	if err != nil {
		http.Error(w, "Internal Server Error", http.StatusInternalServerError)
		return
	}
	templ.Handler(components.PastePage(username, paste, attachments)).ServeHTTP(w, r)
}

func (h *UserHandler) GetPasteAttachment(w http.ResponseWriter, r *http.Request) {
	username := r.PathValue("username")
	pasteSlug := r.PathValue("pasteSlug")
	attachmentSlug := r.PathValue("attachmentSlug")

	attachment, attachmentReader, err := h.service.GetPasteAttachment(
		h.authProvider.GetCurrentUserID(r),
		username,
		pasteSlug,
		attachmentSlug,
	)
	if err != nil {
		http.Error(w, "Internal Server Error", http.StatusInternalServerError)
		return
	}
	defer attachmentReader.Close()
	w.Header().Add("Content-Type", attachment.MimeType)
	w.Header().Add("ETag", attachment.Checksum)
	w.WriteHeader(http.StatusOK)
	io.Copy(w, attachmentReader)
}
