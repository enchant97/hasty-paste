package handlers

import (
	"errors"
	"net/http"
	"net/url"
	"strings"
	"time"

	"github.com/a-h/templ"
	"github.com/enchant97/hasty-paste/app/components"
	"github.com/enchant97/hasty-paste/app/core"
	"github.com/enchant97/hasty-paste/app/middleware"
	"github.com/enchant97/hasty-paste/app/services"
	"github.com/go-chi/chi/v5"
	"github.com/go-playground/validator/v10"
	"github.com/google/uuid"
)

type HomeHandler struct {
	service         services.HomeService
	validator       *validator.Validate
	authProvider    *middleware.AuthenticationProvider
	sessionProvider *middleware.SessionProvider
}

func (h HomeHandler) Setup(
	r *chi.Mux,
	service services.HomeService,
	v *validator.Validate,
	ap *middleware.AuthenticationProvider,
	sp *middleware.SessionProvider,
) {
	h = HomeHandler{
		service:         service,
		validator:       v,
		authProvider:    ap,
		sessionProvider: sp,
	}
	r.Get("/", h.GetHomePage)
	r.Get("/~/{pasteID}", h.GetPasteIDRedirect)
	r.Get("/new", h.GetNewPastePage)
	r.Post("/new/_post", h.PostNewPastePage)
}

func (h *HomeHandler) GetHomePage(w http.ResponseWriter, r *http.Request) {
	if latestPastes, err := h.service.GetLatestPublicPastes(); err != nil {
		InternalErrorResponse(w, err)
	} else {
		templ.Handler(components.IndexPage(latestPastes)).ServeHTTP(w, r)
	}
}

func (h *HomeHandler) GetPasteIDRedirect(w http.ResponseWriter, r *http.Request) {
	pasteID, err := uuid.Parse(r.PathValue("pasteID"))
	if err != nil {
		NotFoundErrorResponse(w, r)
		return
	}
	if parts, err := h.service.GetPastePathPartsByPasteID(pasteID); err != nil {
		if errors.Is(err, services.ErrNotFound) {
			NotFoundErrorResponse(w, r)
		} else {
			InternalErrorResponse(w, err)
		}
	} else {
		p, err := url.JoinPath("/@/", parts.Username, parts.Slug)
		if err != nil {
			InternalErrorResponse(w, err)
		} else {
			http.Redirect(w, r, p, http.StatusTemporaryRedirect)
		}
	}
}

func (h *HomeHandler) GetNewPastePage(w http.ResponseWriter, r *http.Request) {
	templ.Handler(components.NewPastePage()).ServeHTTP(w, r)
}

func (h *HomeHandler) PostNewPastePage(w http.ResponseWriter, r *http.Request) {
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
			Size: fileHeader.Size,
			Type: fileHeader.Header.Get("Content-Type"),
			Open: fileHeader.Open,
		}
		attachments[i] = attachment
	}

	pasteSlug := r.PostFormValue("pasteSlug")
	if pasteSlug == "" {
		pasteSlug = core.GenerateRandomSlug(10)
	}

	visibility := r.PostFormValue("pasteVisibility")
	if h.authProvider.IsCurrentUserAnonymous(r) {
		visibility = "public"
	}

	var expiry *time.Time

	if v := r.PostFormValue("pasteExpiry"); v != "" {
		if t, err := time.Parse("2006-01-02T15:04", v); err != nil {
			http.Error(w, "Bad Request", http.StatusBadRequest)
			return
		} else {
			expiry = &t
		}
	}

	form := core.NewPasteForm{
		Slug:          strings.Trim(pasteSlug, " "),
		Content:       r.PostFormValue("pasteContent"),
		ContentFormat: r.PostFormValue("pasteContentFormat"),
		Visibility:    visibility,
		Expiry:        expiry,
		Attachments:   attachments,
	}

	if err := h.validator.Struct(form); err != nil {
		http.Error(w, "Bad Request", http.StatusBadRequest)
		return
	}

	if err := h.service.NewPaste(h.authProvider.GetCurrentUserID(r), form); err != nil {
		if errors.Is(err, services.ErrConflict) {
			s := h.sessionProvider.GetSession(r)
			s.AddFlash(middleware.CreateErrorFlash("paste with that slug already exists"))
			s.Save(r, w) // TODO handle error
			http.Redirect(w, r, "/new", http.StatusFound)
		} else {
			InternalErrorResponse(w, err)
		}
		return
	}

	// TODO redirect to the created paste
	http.Redirect(w, r, "/new", http.StatusSeeOther)
}
