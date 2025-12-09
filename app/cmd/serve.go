package cmd

import (
	"fmt"
	"github.com/spf13/cobra"
	"log"
	"net/http"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/go-playground/validator/v10"

	"github.com/enchant97/hasty-paste/app/handlers"
	app_middleware "github.com/enchant97/hasty-paste/app/middleware"
	"github.com/enchant97/hasty-paste/app/services"
)

var serveCmd = &cobra.Command{
	Use:   "serve",
	Short: "Run app server",
	Run: func(cmd *cobra.Command, args []string) {
		validate := validator.New(validator.WithRequiredStructEnabled())

		devProvider := app_middleware.ViteProvider{}.New(appConfig.Dev)
		configProvider := app_middleware.AppConfigProvider{}.New(appConfig)
		authenticationProvider := app_middleware.AuthenticationProvider{}.New(appConfig.SecureMode(), appConfig.TokenSecret, &dao)
		sessionProvider := app_middleware.SessionProvider{}.New(appConfig.SecureMode(), appConfig.SessionSecret)

		r := chi.NewRouter()
		// global middleware
		if appConfig.BehindProxy {
			r.Use(middleware.RealIP)
		}
		r.Use(middleware.Logger)
		r.Use(middleware.Recoverer)
		r.Use(devProvider.ProviderMiddleware)
		r.Use(configProvider.ProviderMiddleware)
		// route handlers
		handlers.AuxHandler{}.Setup(r, services.AuxService{}.New(&dao))
		devProvider.SetupHandlers(r)
		handlers.HomeHandler{}.Setup(r, services.HomeService{}.New(&dao, &sc), validate, &authenticationProvider, &sessionProvider, &appConfig)
		handlers.UserHandler{}.Setup(r, services.UserService{}.New(&dao, &sc), validate, &authenticationProvider, &sessionProvider)
		handlers.AuthHandler{}.Setup(r, appConfig, services.AuthService{}.New(&dao), validate, &authenticationProvider, &sessionProvider)

		fmt.Println(`
ooooo ooooo      o       oooooooo8 ooooooooooo ooooo  oooo
 888   888      888     888        88  888  88   888  88
 888ooo888     8  88     888oooooo     888         888
 888   888    8oooo88           888    888         888
o888o o888o o88o  o888o o88oooo888    o888o       o888o

oooooooooo   o       oooooooo8 ooooooooooo ooooooooooo      ooooo ooooo
 888    888 888     888        88  888  88  888    88        888   888
 888oooo88 8  88     888oooooo     888      888ooo8          888   888
 888      8oooo88           888    888      888    oo        888   888
o888o   o88o  o888o o88oooo888    o888o    o888ooo8888      o888o o888o`)
		fmt.Println()
		log.Printf("listening on: http://%s", appConfig.Bind.AsAddress())
		log.Printf("public access at: %s", appConfig.PublicURL)
		http.ListenAndServe(appConfig.Bind.AsAddress(), r)

	},
}

func init() {
	rootCmd.AddCommand(serveCmd)
}
