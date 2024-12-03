package core

import (
	"fmt"

	"github.com/caarlos0/env/v11"
)

type BindConfig struct {
	Host string `env:"HOST" envDefault:"127.0.0.1"`
	Port uint   `env:"PORT" envDefault:"8080"`
}

func (c *BindConfig) AsAddress() string {
	return fmt.Sprintf("%s:%d", c.Host, c.Port)
}

type AppConfig struct {
	Bind     BindConfig `envPrefix:"BIND__"`
	DbUri    string     `env:"DB__URI,notEmpty"`
	DataPath string     `env:"DATA_PATH,notEmpty"`
}

func (appConfig *AppConfig) ParseConfig() error {
	if err := env.Parse(appConfig); err != nil {
		return err
	}
	return nil
}
