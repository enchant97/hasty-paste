package cmd

import (
	"context"
	"database/sql"
	"strings"

	"github.com/enchant97/hasty-paste/app/core"
	"github.com/enchant97/hasty-paste/app/database"
	"github.com/enchant97/hasty-paste/app/migrations"
	"github.com/enchant97/hasty-paste/app/storage"
	"github.com/spf13/cobra"
)

var (
	appConfig core.AppConfig
	sc        storage.StorageController
	dao       core.DAO
)

var rootCmd = &cobra.Command{
	Use:   "hasty-paste",
	Short: "Hasty Paste, paste it all with haste",
	Long:  `Hasty Paste II is a lighting fast pastebin that features a sleek and responsive web UI.`,
}

func Execute() error {
	return rootCmd.Execute()
}

func init() {
	cobra.OnInitialize(func() {
		var err error
		if err := appConfig.ParseConfig(); err != nil {
			panic(err)
		}
		sc, err = storage.StorageController{}.New(appConfig.AttachmentsPath)
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
		dao = core.DAO{}.New(db, dbQueries)
	})
}
