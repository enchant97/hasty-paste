package main

import (
	"database/sql"
	"log"
	"net/http"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	_ "modernc.org/sqlite"

	"github.com/a-h/templ"
	"github.com/enchant97/hasty-paste/app/components"
	"github.com/enchant97/hasty-paste/app/core"
	"github.com/enchant97/hasty-paste/app/database"
	"github.com/enchant97/hasty-paste/app/handlers"
	"github.com/enchant97/hasty-paste/app/migrations"
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
	db, err := sql.Open("sqlite", appConfig.DbUri)
	if err != nil {
		panic(err)
	}
	dao := database.New(db)

	r := chi.NewRouter()
	r.Use(middleware.Logger)
	r.Use(middleware.Recoverer)

	r.Get("/", templ.Handler(components.IndexPage()).ServeHTTP)
	handlers.PastesHandler{}.Setup(r, dao, &sc)

	log.Println("listening on: http://127.0.0.1:8080/")
	http.ListenAndServe(":8080", r)
}
