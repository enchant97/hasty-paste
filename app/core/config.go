package core

import (
	"encoding/base64"
	"errors"
	"fmt"

	"github.com/caarlos0/env/v11"
	"github.com/labstack/gommon/bytes"
)

type Base64Decoded []byte

func (b *Base64Decoded) UnmarshalText(text []byte) error {
	decoded, err := base64.StdEncoding.DecodeString(string(text))
	if err != nil {
		return errors.New("cannot decode base64 string")
	}
	*b = decoded
	return nil
}

type Bytes int64

func (b *Bytes) UnmarshalText(text []byte) error {
	if v, err := bytes.Parse(string(text)); err != nil {
		return err
	} else {
		*b = Bytes(v)
		return nil
	}
}

type BindConfig struct {
	Host string `env:"HOST" envDefault:"127.0.0.1"`
	Port uint   `env:"PORT" envDefault:"8080"`
}

func (c *BindConfig) AsAddress() string {
	return fmt.Sprintf("%s:%d", c.Host, c.Port)
}

type DevConfig struct {
	Enabled      bool   `env:"ENABLED" envDefault:"false"`
	ViteDevHost  string `env:"VITE_DEV_HOST,notEmpty" envDefault:"localhost:5173"`
	ViteDistPath string `env:"VITE_DIST_PATH,notEmpty" envDefault:"./dist/assets"`
}

type AppConfig struct {
	Dev         DevConfig     `envPrefix:"DEV__"`
	Bind        BindConfig    `envPrefix:"BIND__"`
	PublicURL   string        `env:"PUBLIC_URL,notEmpty"`
	DbUri       string        `env:"DB__URI,notEmpty"`
	DataPath    string        `env:"DATA_PATH,notEmpty"`
	TokenSecret Base64Decoded `env:"TOKEN_SECRET,notEmpty"`
	TokenExpiry int64         `env:"TOKEN_EXPIRY" envDefault:"604800"`
}

func (appConfig *AppConfig) ParseConfig() error {
	if err := env.Parse(appConfig); err != nil {
		return err
	}
	return nil
}
