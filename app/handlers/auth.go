package handlers

import (
	"context"
	"errors"
	"log"
	"net/http"
	"net/url"
	"time"

	"github.com/a-h/templ"
	"github.com/coreos/go-oidc/v3/oidc"
	"github.com/enchant97/hasty-paste/app/components"
	"github.com/enchant97/hasty-paste/app/core"
	"github.com/enchant97/hasty-paste/app/database"
	"github.com/enchant97/hasty-paste/app/middleware"
	"github.com/enchant97/hasty-paste/app/services"
	"github.com/go-chi/chi/v5"
	"github.com/go-playground/validator/v10"
	"github.com/google/uuid"
	"golang.org/x/oauth2"
)

type OIDCUserClaims struct {
	Subject           string `json:"sub"`
	PreferredUsername string `json:"preferred_username"`
	Name              string `json:"name"`
}

func setupOIDC(appConfig core.AppConfig) (*oidc.Provider, oauth2.Config, error) {
	provider, err := oidc.NewProvider(context.Background(), appConfig.OIDC.IssuerUrl)
	if err != nil {
		return nil, oauth2.Config{}, err
	}
	callbackURL, err := url.JoinPath(appConfig.PublicURL, "/sso/oidc/callback")
	if err != nil {
		return nil, oauth2.Config{}, err
	}
	config := oauth2.Config{
		ClientID:     appConfig.OIDC.ClientID,
		ClientSecret: appConfig.OIDC.ClientSecret,
		Endpoint:     provider.Endpoint(),
		RedirectURL:  callbackURL,
		Scopes:       []string{oidc.ScopeOpenID, "profile"},
	}
	return provider, config, nil
}

type AuthHandler struct {
	appConfig       core.AppConfig
	validator       *validator.Validate
	service         services.AuthService
	authProvider    *middleware.AuthenticationProvider
	sessionProvider *middleware.SessionProvider
	OIDCProvider    *oidc.Provider
	OAuth2Config    oauth2.Config
}

func (h AuthHandler) Setup(
	r *chi.Mux,
	appConfig core.AppConfig,
	s services.AuthService,
	v *validator.Validate,
	ap *middleware.AuthenticationProvider,
	sp *middleware.SessionProvider,
) {
	var OIDCProvider *oidc.Provider
	var OAuth2Config oauth2.Config
	if appConfig.OIDC.Enabled {
		var err error
		OIDCProvider, OAuth2Config, err = setupOIDC(appConfig)
		if err != nil {
			log.Fatal(err)
		}
	}
	h = AuthHandler{
		appConfig:       appConfig,
		validator:       v,
		service:         s,
		authProvider:    ap,
		sessionProvider: sp,
		OIDCProvider:    OIDCProvider,
		OAuth2Config:    OAuth2Config,
	}
	r.Group(func(r chi.Router) {
		r.Use(ap.RequireAuthenticationMiddleware)
		r.Get("/logout", h.GetLogoutPage)
	})
	r.Group(func(r chi.Router) {
		r.Use(ap.RequireNoAuthenticationMiddleware)
		if appConfig.SignupEnabled {
			r.Get("/signup", h.GetUserSignupPage)
			r.Post("/signup/_post", h.PostUserSignupPage)
		}
		r.Get("/login", h.GetUserLoginPage)
		if appConfig.InternalAuthEnabled {
			r.Post("/login/_post", h.PostUserLoginPage)
		}
		if appConfig.OIDC.Enabled {
			r.Get("/sso/oidc", h.GetOIDCPage)
			r.Get("/sso/oidc/callback", h.GetOIDCCallbackPage)
		}
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
		s := h.sessionProvider.GetSession(r)
		s.AddFlash(middleware.CreateErrorFlash("given details are invalid, do your passwords match?"))
		s.Save(r, w) // TODO handle error
		http.Redirect(w, r, "/signup", http.StatusFound)
		return
	}

	if _, err := h.service.CreateNewUser(form); err != nil {
		if errors.Is(err, services.ErrConflict) {
			s := h.sessionProvider.GetSession(r)
			s.AddFlash(middleware.CreateErrorFlash("user with that username already exists"))
			s.Save(r, w) // TODO handle error
			http.Redirect(w, r, "/signup", http.StatusFound)
		} else {
			InternalErrorResponse(w, err)
		}
		return
	}

	s := h.sessionProvider.GetSession(r)
	s.AddFlash(middleware.CreateOkFlash("user created"))
	s.Save(r, w) // TODO handle error

	http.Redirect(w, r, "/login", http.StatusSeeOther)
}

func (h *AuthHandler) GetUserLoginPage(w http.ResponseWriter, r *http.Request) {
	templ.Handler(components.UserLoginPage(
		h.appConfig.InternalAuthEnabled,
		h.appConfig.SignupEnabled,
		h.appConfig.OIDC,
	)).ServeHTTP(w, r)
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
		if errors.Is(err, services.ErrNotFound) {
			s := h.sessionProvider.GetSession(r)
			s.AddFlash(middleware.CreateErrorFlash("username or password invalid"))
			s.Save(r, w) // TODO handle error
			http.Redirect(w, r, "/login", http.StatusFound)
		} else {
			InternalErrorResponse(w, err)
		}
		return
	} else if !isValid {
		s := h.sessionProvider.GetSession(r)
		s.AddFlash(middleware.CreateErrorFlash("username or password invalid"))
		s.Save(r, w) // TODO handle error
		http.Redirect(w, r, "/login", http.StatusFound)
		return
	}

	if token, err := core.CreateAuthenticationToken(
		form.Username,
		h.appConfig.TokenSecret,
		time.Duration(int64(time.Second)*h.appConfig.TokenExpiry),
	); err != nil {
		InternalErrorResponse(w, err)
	} else {
		h.authProvider.SetCookieAuthToken(w, token)
		http.Redirect(w, r, "/", http.StatusFound)
	}

}

func (h *AuthHandler) GetLogoutPage(w http.ResponseWriter, r *http.Request) {
	h.authProvider.ClearCookieAuthToken(w)
	http.Redirect(w, r, "/login", http.StatusSeeOther)
}

func (h *AuthHandler) GetOIDCPage(w http.ResponseWriter, r *http.Request) {
	state := uuid.New().String()
	http.SetCookie(w, &http.Cookie{
		Name:     "OpenIdState",
		Path:     "/sso/oidc",
		Value:    state,
		HttpOnly: true,
		Secure:   h.appConfig.SecureMode(),
	})
	http.Redirect(w, r, h.OAuth2Config.AuthCodeURL(state), http.StatusSeeOther)
}

func (h *AuthHandler) GetOIDCCallbackPage(w http.ResponseWriter, r *http.Request) {
	state, err := r.Cookie("OpenIdState")
	if err != nil {
		http.Error(w, "state cookie not found", http.StatusBadRequest)
		return
	}
	http.SetCookie(w, &http.Cookie{
		Name:     "OpenIdState",
		Path:     "/sso/oidc",
		Value:    "",
		Expires:  time.Date(2000, 1, 1, 0, 0, 0, 0, time.UTC),
		HttpOnly: true,
		Secure:   h.appConfig.SecureMode(),
	})
	if r.URL.Query().Get("state") != state.Value {
		http.Error(w, "state did not match", http.StatusBadRequest)
		return
	}

	oauth2Token, err := h.OAuth2Config.Exchange(context.Background(), r.URL.Query().Get("code"))
	if err != nil {
		InternalErrorResponse(w, err)
		return
	}
	userInfo, err := h.OIDCProvider.UserInfo(context.Background(), oauth2.StaticTokenSource(oauth2Token))
	if err != nil {
		InternalErrorResponse(w, err)
		return
	}
	var userClaims OIDCUserClaims
	if err := userInfo.Claims(&userClaims); err != nil {
		InternalErrorResponse(w, err)
		return
	}

	oidcUser := core.OIDCUserWithUsername{
		Username: userClaims.PreferredUsername,
		OIDCUser: core.OIDCUser{
			ClientID: h.appConfig.OIDC.ClientID,
			Subject:  userClaims.Subject,
		},
	}

	if err := h.validator.Struct(oidcUser); err != nil {
		s := h.sessionProvider.GetSession(r)
		s.AddFlash(middleware.CreateErrorFlash("given details are invalid, maybe the username is not compatible?"))
		s.Save(r, w) // TODO handle error
		http.Redirect(w, r, "/login", http.StatusSeeOther)
		return
	}

	var user database.User
	if h.appConfig.SignupEnabled {
		user, err = h.service.GetOrCreateOIDCUser(oidcUser)
	} else {
		user, err = h.service.GetOIDCUser(oidcUser.OIDCUser)
	}
	if err != nil {
		if errors.Is(err, services.ErrConflict) {
			s := h.sessionProvider.GetSession(r)
			s.AddFlash(middleware.CreateErrorFlash("user with that username already exists"))
			s.Save(r, w) // TODO handle error
			http.Redirect(w, r, "/login", http.StatusSeeOther)
		} else if errors.Is(err, services.ErrNotFound) && !h.appConfig.SignupEnabled {
			s := h.sessionProvider.GetSession(r)
			s.AddFlash(middleware.CreateErrorFlash("user not found and new accounts are disabled"))
			s.Save(r, w) // TODO handle error
			http.Redirect(w, r, "/login", http.StatusSeeOther)
		} else {
			InternalErrorResponse(w, err)
		}
		return
	}

	if token, err := core.CreateAuthenticationToken(
		user.Username,
		h.appConfig.TokenSecret,
		time.Duration(int64(time.Second)*h.appConfig.TokenExpiry),
	); err != nil {
		InternalErrorResponse(w, err)
	} else {
		h.authProvider.SetCookieAuthToken(w, token)
		http.Redirect(w, r, "/", http.StatusFound)
	}
}
