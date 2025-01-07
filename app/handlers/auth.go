package handlers

import (
	"net/http"
	"time"

	"github.com/a-h/templ"
	"github.com/enchant97/hasty-paste/app/components"
	"github.com/enchant97/hasty-paste/app/core"
	"github.com/enchant97/hasty-paste/app/middleware"
	"github.com/enchant97/hasty-paste/app/services"
	"github.com/go-chi/chi/v5"
	"github.com/go-playground/validator/v10"
)

type AuthHandler struct {
	appConfig    core.AppConfig
	validator    *validator.Validate
	service      services.AuthService
	authProvider *middleware.AuthenticationProvider
}

func (h AuthHandler) Setup(
	r *chi.Mux,
	appConfig core.AppConfig,
	s services.AuthService,
	v *validator.Validate,
	ap *middleware.AuthenticationProvider,
) {
	h = AuthHandler{appConfig: appConfig, validator: v, service: s, authProvider: ap}
	r.Group(func(r chi.Router) {
		r.Use(ap.RequireAuthenticationMiddleware)
		r.Get("/logout", h.GetLogoutPage)
	})
	r.Group(func(r chi.Router) {
		r.Use(ap.RequireNoAuthenticationMiddleware)
		r.Get("/signup", h.GetUserSignupPage)
		r.Post("/signup/_post", h.PostUserSignupPage)
		r.Get("/login", h.GetUserLoginPage)
		r.Post("/login/_post", h.PostUserLoginPage)
	})
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

func (h *AuthHandler) GetUserLoginPage(w http.ResponseWriter, r *http.Request) {
	templ.Handler(components.UserLoginPage()).ServeHTTP(w, r)
}

func (h *AuthHandler) PostUserLoginPage(w http.ResponseWriter, r *http.Request) {
	if err := r.ParseForm(); err != nil {
		http.Error(w, "Bad Request", http.StatusBadRequest)
		return
	}

	form := core.LoginUserForm{
		Username: r.PostFormValue("username"),
		Password: r.PostFormValue("password"),
	}

	if err := h.validator.Struct(form); err != nil {
		http.Error(w, "Bad Request", http.StatusBadRequest)
		return
	}

	if isValid, err := h.service.CheckIfValidUser(form); err != nil {
		http.Error(w, "Internal Server Error", http.StatusInternalServerError)
		return
	} else if !isValid {
		http.Redirect(w, r, "/login", http.StatusFound)
		return
	}

	if token, err := core.CreateAuthenticationToken(
		form.Username,
		h.appConfig.TokenSecret,
		time.Duration(int64(time.Second)*h.appConfig.TokenExpiry),
	); err != nil {
		http.Error(w, "Internal Server Error", http.StatusInternalServerError)
	} else {
		h.authProvider.SetCookieAuthToken(w, token)
		http.Redirect(w, r, "/", http.StatusFound)
	}

}

func (h *AuthHandler) GetLogoutPage(w http.ResponseWriter, r *http.Request) {
	h.authProvider.ClearCookieAuthToken(w)
	http.Redirect(w, r, "/login", http.StatusTemporaryRedirect)
}
