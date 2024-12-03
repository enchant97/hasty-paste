package main

import (
	"log"
	"net/http"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"

	"github.com/a-h/templ"
	"github.com/enchant97/hasty-paste/app/components"
)

func main() {
	r := chi.NewRouter()
	r.Use(middleware.Logger)
	r.Use(middleware.Recoverer)
	r.Get("/", templ.Handler(components.IndexPage()).ServeHTTP)
	r.Get("/pastes/new", templ.Handler(components.NewPastePage()).ServeHTTP)
	log.Println("listening on: http://127.0.0.1:8080/")
	http.ListenAndServe(":8080", r)
}
