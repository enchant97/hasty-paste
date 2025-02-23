package core

import (
	"mime/multipart"
	"time"
)

type NewPasteFormAttachment struct {
	Slug string `validate:"printascii,required"`
	Type string `validate:"required"`
	Size int64  `validate:"required"`
	Open func() (multipart.File, error)
}

type NewPasteForm struct {
	Slug          string `validate:"printascii,required"`
	Content       string `validate:"required"`
	ContentFormat string `validate:"required,lowercase,max=30"`
	Visibility    string `validate:"required,oneof=public unlisted private"`
	Expiry        *time.Time
	Attachments   []NewPasteFormAttachment
}

type NewUserForm struct {
	Username        string `validate:"alphanum,lowercase,min=3,max=30,required"`
	Password        string `validate:"min=8,required"`
	PasswordConfirm string `validate:"eqcsfield=Password,required"`
}

type OIDCUser struct {
	ClientID string `validate:"required"`
	Subject  string `validate:"required"`
}

type OIDCUserWithUsername struct {
	OIDCUser
	Username string `validate:"alphanum,lowercase,min=3,max=30,required"`
}

type LoginUserForm struct {
	Username string `validate:"required"`
	Password string `validate:"required"`
}
