package handlers

import (
	"net/http"

	"github.com/a-h/templ"
	"github.com/enchant97/hasty-paste/app/components"
	"github.com/enchant97/hasty-paste/app/core"
	"github.com/enchant97/hasty-paste/app/services"
	"github.com/go-chi/chi/v5"
	"github.com/go-playground/validator/v10"
)

type AuthHandler struct {
	validator *validator.Validate
	service   services.AuthService
}

func (h AuthHandler) Setup(
	r *chi.Mux,
	s services.AuthService,
	v *validator.Validate,
) {
	h = AuthHandler{validator: v, service: s}
	r.Get("/signup", h.GetUserSignupPage)
	r.Post("/signup/_post", h.PostUserSignupPage)
}

func (h *AuthHandler) GetUserSignupPage(w http.ResponseWriter, r *http.Request) {
	templ.Handler(components.UserSignupPage()).ServeHTTP(w, r)
}

func (h *AuthHandler) PostUserSignupPage(w http.ResponseWriter, r *http.Request) {
	if err := r.ParseForm(); err != nil {
		http.Error(w, "Bad Request", http.StatusBadRequest)
		return
	}

	form := core.NewUserForm{
		Username:        r.PostFormValue("username"),
		Password:        r.PostFormValue("password"),
		PasswordConfirm: r.PostFormValue("passwordConfirm"),
	}

	if err := h.validator.Struct(form); err != nil {
		http.Error(w, "Bad Request", http.StatusBadRequest)
		return
	}

	if _, err := h.service.CreateNewUser(form); err != nil {
		http.Error(w, "Internal Server Error", http.StatusInternalServerError)
		return
	}

	http.Redirect(w, r, "/login", http.StatusSeeOther)
}
