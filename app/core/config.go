package core

import (
	"encoding/base64"
	"errors"
	"fmt"
	"strings"

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
	ViteDistPath string `env:"VITE_DIST_PATH,notEmpty" envDefault:"./dist"`
}

type OIDCConfig struct {
	Enabled      bool   `env:"ENABLED" envDefault:"false"`
	Name         string `env:"NAME"`
	IssuerUrl    string `env:"ISSUER_URL"`
	ClientID     string `env:"CLIENT_ID"`
	ClientSecret string `env:"CLIENT_SECRET"`
}

type AppConfig struct {
	Dev                    DevConfig     `envPrefix:"DEV__"`
	Bind                   BindConfig    `envPrefix:"BIND__"`
	OIDC                   OIDCConfig    `envPrefix:"OIDC__"`
	PublicURL              string        `env:"PUBLIC_URL,notEmpty"`
	BehindProxy            bool          `env:"BEHIND_PROXY" envDefault:"false"`
	DbUri                  string        `env:"DB_URI,notEmpty"`
	AttachmentsPath        string        `env:"ATTACHMENTS_PATH,notEmpty"`
	TokenSecret            Base64Decoded `env:"AUTH_TOKEN_SECRET,notEmpty"`
	TokenExpiry            int64         `env:"AUTH_TOKEN_EXPIRY" envDefault:"604800"`
	SessionSecret          Base64Decoded `env:"SESSION_SECRET,notEmpty"`
	SignupEnabled          bool          `env:"SIGNUP_ENABLED" envDefault:"true"`
	InternalAuthEnabled    bool          `env:"INTERNAL_AUTH_ENABLED" envDefault:"true"`
	RandomSlugLength       int           `env:"RANDOM_SLUG_LENGTH" envDefault:"10"`
	AnonymousPastesEnabled bool          `env:"ANONYMOUS_PASTES_ENABLED" envDefault:"true"`
	MaxPasteSize           int64         `env:"MAX_PASTE_SIZE" envDefault:"12582912"`
	AttachmentsEnabled     bool          `env:"ATTACHMENTS_ENABLED" envDefault:"true"`
}

func (ac *AppConfig) SecureMode() bool {
	return strings.HasPrefix(ac.PublicURL, "https://")
}

func (appConfig *AppConfig) ParseConfig() error {
	if err := env.Parse(appConfig); err != nil {
		return err
	}
	return nil
}
