package handlers

import (
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"time"

	"github.com/enchant97/hasty-paste/app/core"
	"github.com/enchant97/hasty-paste/app/services"
	"github.com/go-chi/chi/v5"
	"github.com/go-playground/validator/v10"
)

type ApiHandler struct {
	service   services.ApiService
	appConfig core.AppConfig
	validator *validator.Validate
}

func (h ApiHandler) Setup(
	r *chi.Mux,
	service services.ApiService,
	appConfig core.AppConfig,
	v *validator.Validate,
) {
	h = ApiHandler{
		service:   service,
		validator: v,
		appConfig: appConfig,
	}
	r.Group(func(r chi.Router) {
		r.Post("/api/q/", h.PostCreateQuickPaste)
	})
}

func (h *ApiHandler) PostCreateQuickPaste(w http.ResponseWriter, r *http.Request) {
	if !h.appConfig.AnonymousPastesEnabled {
		http.Error(w, "Anonymous Pastes Disabled", http.StatusForbidden)
		return
	}
	// impose max body size limit
	r.Body = http.MaxBytesReader(w, r.Body, h.appConfig.MaxPasteSize)
	// read & process paste content
	rawPasteContent, err := io.ReadAll(r.Body)
	if err != nil {
		if _, ok := err.(*http.MaxBytesError); ok {
			http.Error(w, "Paste Content Too Large", http.StatusRequestEntityTooLarge)
		} else {
			http.Error(w, "Failure To Process Paste Content", http.StatusBadRequest)
		}
		return
	}
	pasteContent := string(rawPasteContent)
	// create random slug
	pasteSlug := core.GenerateRandomSlug(h.appConfig.RandomSlugLength)
	// set expiry if required
	var pasteExpiry *time.Time = nil
	if h.appConfig.Expiry.Anonymous.LimitEnabled {
		t := makeExpiryTime(h.appConfig.Expiry.Anonymous)
		pasteExpiry = &t
	}
	// validate fields
	form := core.NewPasteForm{
		Slug:          pasteSlug,
		Content:       pasteContent,
		ContentFormat: "plaintext",
		Visibility:    "public",
		Expiry:        pasteExpiry,
	}
	if err := h.validator.Struct(form); err != nil {
		http.Error(w, "Failure Validate Fields", http.StatusBadRequest)
		return
	}
	// create paste
	if pasteID, err := h.service.NewQuickPaste(form); err != nil {
		if errors.Is(err, services.ErrConflict) {
			http.Error(w, fmt.Sprintf("Paste Name \"%s\" Already Exists", pasteID), http.StatusConflict)
		} else {
			InternalErrorResponse(w, err)
		}
	} else {
		pasteURL, err := url.JoinPath(h.appConfig.PublicURL, fmt.Sprintf("/@/anonymous/%s", pasteSlug))
		if err != nil {
			InternalErrorResponse(w, err)
			return
		}
		w.WriteHeader(http.StatusCreated)
		w.Write([]byte(pasteURL + "\n"))
	}
}
