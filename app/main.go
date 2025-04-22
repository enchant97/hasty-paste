package main

import (
	"context"
	"database/sql"
	"fmt"
	"log"
	"net/http"
	"strings"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/go-playground/validator/v10"
	_ "modernc.org/sqlite"

	"github.com/enchant97/hasty-paste/app/core"
	"github.com/enchant97/hasty-paste/app/database"
	"github.com/enchant97/hasty-paste/app/handlers"
	app_middleware "github.com/enchant97/hasty-paste/app/middleware"
	"github.com/enchant97/hasty-paste/app/migrations"
	"github.com/enchant97/hasty-paste/app/services"
	"github.com/enchant97/hasty-paste/app/storage"
)

func main() {
	var appConfig core.AppConfig
	if err := appConfig.ParseConfig(); err != nil {
		panic(err)
	}
	sc, err := storage.StorageController{}.New(appConfig.AttachmentsPath)
	if err != nil {
		panic(err)
	}

	if err := migrations.MigrateDB(appConfig.DbUri); err != nil {
		panic(err)
	}
	db, err := sql.Open("sqlite", strings.Split(appConfig.DbUri, "sqlite://")[1])
	if err != nil {
		panic(err)
	}
	dbQueries := database.New(db)
	if err := dbQueries.InsertAnonymousUser(context.Background(), core.NewUUID()); err != nil {
		panic(err)
	}
	dao := core.DAO{}.New(db, dbQueries)
	validate := validator.New(validator.WithRequiredStructEnabled())

	devProvider := app_middleware.ViteProvider{}.New(appConfig.Dev)
	configProvider := app_middleware.AppConfigProvider{}.New(appConfig)
	authenticationProvider := app_middleware.AuthenticationProvider{}.New(appConfig.SecureMode(), appConfig.TokenSecret, &dao)
	sessionProvider := app_middleware.SessionProvider{}.New(appConfig.SecureMode(), appConfig.SessionSecret)

	r := chi.NewRouter()
	if appConfig.BehindProxy {
		r.Use(middleware.RealIP)
	}
	r.Use(middleware.Logger)
	r.Use(middleware.Recoverer)
	r.Use(devProvider.ProviderMiddleware)
	r.Use(configProvider.ProviderMiddleware)
	r.Use(authenticationProvider.ProviderMiddleware)
	r.Use(sessionProvider.ProviderMiddleware)

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
}
