package main

import (
	"context"
	"database/sql"
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
	"github.com/enchant97/hasty-paste/app/migrations"
	"github.com/enchant97/hasty-paste/app/services"
	"github.com/enchant97/hasty-paste/app/storage"
)

func main() {
	var appConfig core.AppConfig
	if err := appConfig.ParseConfig(); err != nil {
		panic(err)
	}
	sc, err := storage.StorageController{}.New(appConfig.DataPath)
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
	if err := dbQueries.InsertAnonymousUser(context.Background()); err != nil {
		panic(err)
	}
	dao := core.DAO{}.New(db, dbQueries)
	validate := validator.New(validator.WithRequiredStructEnabled())

	r := chi.NewRouter()
	r.Use(middleware.Logger)
	r.Use(middleware.Recoverer)

	handlers.HomeHandler{}.Setup(r, services.HomeService{}.New(&dao, &sc), validate)
	handlers.PastesHandler{}.Setup(r, services.PastesService{}.New(&dao, &sc), validate)

	log.Println("listening on: http://127.0.0.1:8080/")
	http.ListenAndServe(":8080", r)
}
