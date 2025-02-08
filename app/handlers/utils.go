package handlers

import (
	"log"
	"net/http"

	"github.com/a-h/templ"
	"github.com/enchant97/hasty-paste/app/components"
)

func InternalErrorResponse(w http.ResponseWriter, err error) {
	log.Println(err)
	http.Error(w, "Internal Server Error", http.StatusInternalServerError)
}

func NotFoundErrorResponse(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusNotFound)
	templ.Handler(components.NotFoundPage()).ServeHTTP(w, r)
}
